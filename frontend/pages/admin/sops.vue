<script setup lang="ts">
// --- Assumptions: you have composables `useApi()` and `useAuth()` that expose
// baseURL, token, get/post helpers, and current user with biz_role.
const { get } = useApi()
const { user } = useAuth()
const canEdit = computed(() => ['manager','admin'].includes(user.value?.biz_role || ''))

type FieldSpec = {
  name: string
  label: string
  type?: string
  required?: boolean
  readOnly?: boolean
  choices?: Array<{ value:any; display:string }>
}

// ---------------------- Reactive state ----------------------
const rows = ref<any[]>([])
const loading = ref(false)
const err = ref<string|null>(null)

// Create form fields (dynamic if OPTIONS works, else fallback)
const createFields = ref<FieldSpec[]>([])
const form = ref<Record<string, any>>({})
const fileFields = ref<string[]>([])
const createFiles = reactive<Record<string, File | null>>({})
const myOrgId = ref<string | null>(null)

// Edit dialog
const editOpen = ref(false)
const editing = ref<any|null>(null)
const editErr = ref<string|null>(null)
const editFields = ref<FieldSpec[]>([])
const editForm = ref<Record<string, any>>({})
const editFiles = reactive<Record<string, File | null>>({})

// Video preview modal (optional for admin; we route to viewer for PDFs)
const previewOpen = ref(false)
const previewTitle = ref('')
const previewSrc = ref('')

// ---------------------- Helpers ----------------------
function authHeaders() {
  const t = useApi().token.value
  return t ? { Authorization: `Bearer ${t}` } : {}
}
function defaultValue(t?: string) {
  const tp = (t || '').toLowerCase()
  if (tp.includes('boolean')) return false
  if (tp.includes('integer') || tp.includes('number')) return 0
  return ''
}
const isFileFieldName = (name: string) => {
  const n = (name || '').toLowerCase()
  // Treat common variants as file inputs
  return (
    n === 'file' ||
    n.endsWith('_file') ||
    n.includes('media_file') ||
    n.includes('upload') ||
    n.includes('attachment')
  )
}
function discoverFileFields(fields: FieldSpec[]) {
  fileFields.value = fields
    .filter(f => (f.type === 'file') || isFileFieldName(f.name))
    .map(f => f.name)
  for (const k of fileFields.value) {
    if (!(k in createFiles)) createFiles[k] = null
    if (!(k in editFiles))   editFiles[k]   = null
  }
}
function buildFieldsFromOptions(opts:any, method:'POST'|'PATCH'): FieldSpec[] {
  const fieldsObj = opts?.actions?.[method] || {}
  const fields: FieldSpec[] = []
  for (const [name, meta] of Object.entries<any>(fieldsObj)) {
    const readOnly = !!meta.read_only
    const hide = ['id','created_at','updated_at','last_heartbeat']
    if (readOnly || hide.includes(name)) continue
    fields.push({
      name,
      label: meta.label || name,
      type: (meta.type || '').toLowerCase(),
      required: !!meta.required,
      readOnly: !!meta.read_only,
      choices: Array.isArray(meta.choices)
        ? meta.choices.map((c:any)=>({ value:c.value, display:c.display_name || c.display || String(c.value) }))
        : undefined
    })
  }
  // nice ordering (if present)
  const order = ['code','title','name','description','media_file','video_url','pdf_url','pptx_url','link','link_url','org','skill','sop']
  fields.sort((a,b)=>{
    const ia = order.indexOf(a.name); const ib = order.indexOf(b.name)
    if (ia === -1 && ib === -1) return a.name.localeCompare(b.name)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
  return fields
}
function absoluteMediaUrl(pathOrUrl: string) {
  if (!pathOrUrl) return ''
  try { new URL(pathOrUrl); return pathOrUrl } catch {}
  const api = useApi().baseURL
  const origin = new URL(api).origin
  if (pathOrUrl.startsWith('/')) return origin + pathOrUrl
  return origin.replace(/\/+$/, '') + '/' + pathOrUrl.replace(/^\/+/, '')
}
function getSource(r:any) {
  const file = r.media_file || r.file || ''
  const video = r.video_url || r.video || r.media_url || ''
  const pdf   = r.pdf_url || r.pdf || ''
  const pptx  = r.pptx_url || r.pptx || ''
  const link  = r.link_url || r.link || ''
  const title = r.title || r.name || r.code || r.id
  const first = file ? absoluteMediaUrl(file) : (video || pdf || pptx || link)
  return { file, video, pdf, pptx, link, title, first }
}
function kind(r:any) {
  const { file, video, pdf, pptx, link } = getSource(r)
  if (file) {
    const l = String(file).toLowerCase()
    if (l.endsWith('.mp4') || l.endsWith('.webm')) return 'File (Video)'
    if (l.endsWith('.pdf')) return 'File (PDF)'
    return 'File'
  }
  if (video) return 'Video URL'
  if (pdf) return 'PDF URL'
  if (pptx) return 'PPTX URL'
  if (link) return 'Link'
  return 'Unknown'
}
function openItem(r:any) {
  const { first, title } = getSource(r)
  if (!first) return
  const lower = String(first).toLowerCase()
  if (lower.endsWith('.mp4') || lower.endsWith('.webm')) {
    // route to viewer so heartbeat can still work as video
    navigateTo(`/sops/${r.id}?type=video&src=${encodeURIComponent(first)}`)
    return
  }
  if (lower.endsWith('.pdf')) {
    navigateTo(`/sops/${r.id}?type=pdf&src=${encodeURIComponent(first)}`)
    return
  }
  window.open(String(first), '_blank', 'noopener')
}

// ---------------------- Data loading ----------------------
onMounted(async () => {
  await hydrateOrg()
  await loadSchema()
  await loadRows()
})
async function hydrateOrg() {
  try {
    const me = user.value?.username
    if (!me) return
    const u:any = await get(`/users/?username=${encodeURIComponent(me)}`)
    const list = Array.isArray(u) ? u : (u?.results || [])
    if (list.length) myOrgId.value = list[0].org || null
  } catch { /* org might be optional */ }
}
async function loadSchema() {
  // try OPTIONS for dynamic form; fallback to a safe static schema
  try {
    const opts:any = await $fetch('/sops/', { method: 'OPTIONS', baseURL: useApi().baseURL, headers: authHeaders() })
    createFields.value = buildFieldsFromOptions(opts, 'POST')
  } catch {
    createFields.value = []
  }
  if (!createFields.value.length) {
    // Fallback schema (aligned with your SOPSerializer/__all__)
    createFields.value = [
      { name:'code',         label:'Code',         type:'text',     required:true },
      { name:'title',        label:'Title',        type:'text' },
      { name:'description',  label:'Description',  type:'text' },
      { name:'media_file',   label:'Upload File',  type:'file' },
      { name:'video_url',    label:'Video URL',    type:'url' },
      { name:'pdf_url',      label:'PDF URL',      type:'url' },
      { name:'pptx_url',     label:'PPTX URL',     type:'url' },
      { name:'link_url',     label:'Link URL',     type:'url' },
      { name:'org',          label:'Org',          type:'text' }, // UUID if required
    ]
  }
  // init create form defaults
  const f:Record<string,any> = {}
  createFields.value.forEach(field => { f[field.name] = defaultValue(field.type) })
  form.value = f
  discoverFileFields(createFields.value)
}
async function loadRows() {
  const data:any = await get('/sops/')
  rows.value = Array.isArray(data) ? data : (data.results || [])
}

// ---------------------- Create ----------------------
async function createSOP() {
  if (!canEdit.value) return
  loading.value = true; err.value = null
  try {
    const hasFile = fileFields.value.some(k => !!createFiles[k])
    if (hasFile) {
      const fd = new FormData()
      for (const f of createFields.value) {
        const name = f.name
        if (isFileFieldName(name)) continue // append files below
        const val = form.value[name]
        if ((val === '' || val === null) && !f.required) continue
        fd.append(name, String(val))
      }
      // append detected file inputs (prefer media_file)
      for (const k of fileFields.value) {
        if (createFiles[k]) fd.append(k, createFiles[k] as File)
      }
      await $fetch('/sops/', {
        method: 'POST', baseURL: useApi().baseURL,
        headers: { ...authHeaders() }, body: fd // NO content-type header
      })
    } else {
      const payload:any = {}
      for (const f of createFields.value) {
        const val = form.value[f.name]
        if ((val === '' || val === null) && !f.required) continue
        payload[f.name] = val
      }
      await $fetch('/sops/', {
        method:'POST', baseURL: useApi().baseURL,
        headers:{ 'Content-Type':'application/json', ...authHeaders() },
        body: payload
      })
    }
    // reset
    for (const f of createFields.value) form.value[f.name] = defaultValue(f.type)
    for (const k of fileFields.value) createFiles[k] = null
    await loadRows()
  } catch (e:any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Create failed')
  } finally {
    loading.value = false
  }
}

// ---------------------- Edit ----------------------
function openEdit(row:any) {
  editing.value = row
  editErr.value = null
  editOpen.value = true
  // try OPTIONS detail; if not available, mirror the create fields
  loadEditSchemaAndFill()
}
async function loadEditSchemaAndFill() {
  let fields: FieldSpec[] = []
  try {
    if (editing.value?.id) {
      const opts:any = await $fetch(`/sops/${editing.value.id}/`, {
        method:'OPTIONS', baseURL: useApi().baseURL, headers: authHeaders()
      })
      fields = buildFieldsFromOptions(opts, 'PATCH')
    }
  } catch { /* ignore */ }
  if (!fields.length) fields = [...createFields.value]
  editFields.value = fields
  discoverFileFields(editFields.value)
  const f:Record<string,any> = {}
  for (const fld of fields) {
    f[fld.name] = editing.value?.[fld.name] ?? defaultValue(fld.type)
  }
  editForm.value = f
}
async function saveEdit() {
  if (!canEdit.value || !editing.value) return
  editErr.value = null
  try {
    const hasFile = fileFields.value.some(k => !!editFiles[k])
    if (hasFile) {
      const fd = new FormData()
      for (const f of editFields.value) {
        const name = f.name
        if (isFileFieldName(name)) continue
        const val = editForm.value[name]
        if ((val === '' || val === null) && !f.required) continue
        fd.append(name, String(val))
      }
      for (const k of fileFields.value) {
        if (editFiles[k]) fd.append(k, editFiles[k] as File)
      }
      await $fetch(`/sops/${editing.value.id}/`, {
        method:'PATCH', baseURL: useApi().baseURL,
        headers: { ...authHeaders() }, body: fd
      })
    } else {
      const payload:any = {}
      for (const f of editFields.value) {
        const val = editForm.value[f.name]
        if ((val === '' || val === null) && !f.required) continue
        payload[f.name] = val
      }
      await $fetch(`/sops/${editing.value.id}/`, {
        method:'PATCH', baseURL: useApi().baseURL,
        headers:{ 'Content-Type':'application/json', ...authHeaders() },
        body: payload
      })
    }
    editOpen.value = false
    editing.value = null
    for (const k of fileFields.value) editFiles[k] = null
    await loadRows()
  } catch (e:any) {
    editErr.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Save failed')
  }
}
async function deleteSop(r:any) {
  if (!canEdit.value) return
  if (!confirm(`Delete SOP "${r.title || r.name || r.code || r.id}"? This cannot be undone.`)) return
  try {
    await $fetch(`/sops/${r.id}/`, {
      method:'DELETE', baseURL: useApi().baseURL, headers: authHeaders()
    })
    await loadRows()
  } catch (e:any) {
    alert(e?.data ? JSON.stringify(e.data) : (e?.message || 'Delete failed'))
  }
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">SOP Admin</h1>
    <p v-if="!canEdit" class="text-red-600">Manager or Admin only.</p>

    <!-- Create -->
    <section>
      <h2 class="text-lg font-semibold mb-2">Create SOP</h2>
      <div class="grid md:grid-cols-2 gap-2 max-w-3xl">
        <template v-for="f in createFields" :key="`c-${f.name}`">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-gray-600">
              {{ f.label }} <span v-if="f.required" class="text-red-600">*</span>
            </label>

            <!-- Choice -->
            <select v-if="f.type==='choice' && f.choices?.length"
                    v-model="form[f.name]" class="border rounded p-2">
              <option :value="''">— Select —</option>
              <option v-for="c in f.choices" :key="String(c.value)" :value="c.value">{{ c.display }}</option>
            </select>

            <!-- File -->
            <input v-else-if="isFileFieldName(f.name) || f.type === 'file'"
                   type="file" class="border rounded p-2"
                   @change="(e:any)=>{ createFiles[f.name] = (e.target?.files?.[0] || null) }" />

            <!-- Boolean -->
            <input v-else-if="(f.type||'').includes('boolean')" type="checkbox" v-model="form[f.name]" />

            <!-- Number -->
            <input v-else-if="(f.type||'').includes('integer') || (f.type||'').includes('number')"
                   type="number" class="border rounded p-2" v-model.number="form[f.name]" />

            <!-- Date/Datetime -->
            <input v-else-if="(f.type||'').includes('datetime')" type="datetime-local" class="border rounded p-2" v-model="form[f.name]" />
            <input v-else-if="(f.type||'').includes('date')" type="date" class="border rounded p-2" v-model="form[f.name]" />

            <!-- Text / URL / String -->
            <textarea v-else-if="(f.type||'').includes('text')" rows="3" class="border rounded p-2" v-model="form[f.name]" />
            <input v-else :type="(f.type||'')==='url' ? 'url' : 'text'"
                   class="border rounded p-2" v-model="form[f.name]" />
          </div>
        </template>
      </div>
      <div class="mt-2">
        <button :disabled="!canEdit || loading" class="px-3 py-1 rounded bg-black text-white" @click="createSOP">
          {{ loading ? 'Creating…' : 'Create' }}
        </button>
        <span v-if="err" class="text-red-600 ml-2 break-all">{{ err }}</span>
      </div>
    </section>

    <!-- List -->
    <section>
      <h2 class="text-lg font-semibold mb-2">All SOPs</h2>
      <table class="w-full border">
        <thead><tr class="bg-gray-50">
          <th class="p-2 text-left">Code</th>
          <th class="p-2 text-left">Title/Name</th>
          <th class="p-2 text-left">Kind</th>
          <th class="p-2 text-left">Source</th>
          <th class="p-2">Actions</th>
        </tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id" class="border-t">
            <td class="p-2">{{ r.code || '-' }}</td>
            <td class="p-2">{{ r.title || r.name || r.id }}</td>
            <td class="p-2">{{ kind(r) }}</td>
            <td class="p-2 truncate">
              {{ (r.media_file || r.video_url || r.pdf_url || r.pptx_url || r.link_url || r.media_url || r.link || '') || '—' }}
            </td>
            <td class="p-2 flex gap-2 justify-center">
              <button class="underline" @click="openItem(r)">Open</button>
              <button v-if="canEdit" class="px-2 py-1 border rounded" @click="openEdit(r)">Edit</button>
              <button v-if="canEdit" class="px-2 py-1 border rounded" @click="deleteSop(r)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Edit dialog -->
    <div v-if="editOpen" class="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div class="bg-white w-full max-w-2xl rounded shadow p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">Edit SOP</h3>
          <button class="text-sm px-2 py-1 border rounded" @click="editOpen=false; editing=null">Close</button>
        </div>

        <div class="grid md:grid-cols-2 gap-2">
          <template v-for="f in editFields" :key="`e-${f.name}`">
            <div class="flex flex-col gap-1">
              <label class="text-xs text-gray-600">
                {{ f.label }} <span v-if="f.required" class="text-red-600">*</span>
              </label>

              <select v-if="f.type==='choice' && f.choices?.length"
                      v-model="editForm[f.name]" class="border rounded p-2">
                <option :value="''">— Select —</option>
                <option v-for="c in f.choices" :key="String(c.value)" :value="c.value">{{ c.display }}</option>
              </select>

              <input v-else-if="isFileFieldName(f.name) || f.type === 'file'"
                     type="file" class="border rounded p-2"
                     @change="(e:any)=>{ editFiles[f.name] = (e.target?.files?.[0] || null) }" />

              <input v-else-if="(f.type||'').includes('boolean')" type="checkbox" v-model="editForm[f.name]" />

              <input v-else-if="(f.type||'').includes('integer') || (f.type||'').includes('number')"
                     type="number" class="border rounded p-2" v-model.number="editForm[f.name]" />

              <input v-else-if="(f.type||'').includes('datetime')" type="datetime-local" class="border rounded p-2" v-model="editForm[f.name]" />
              <input v-else-if="(f.type||'').includes('date')" type="date" class="border rounded p-2" v-model="editForm[f.name]" />

              <textarea v-else-if="(f.type||'').includes('text')" rows="3" class="border rounded p-2" v-model="editForm[f.name]" />
              <input v-else :type="(f.type||'')==='url' ? 'url' : 'text'"
                     class="border rounded p-2" v-model="editForm[f.name]" />
            </div>
          </template>
        </div>

        <div class="flex items-center gap-2">
          <button class="px-3 py-1 rounded bg-black text-white" @click="saveEdit">Save</button>
          <span v-if="editErr" class="text-red-600 break-all">{{ editErr }}</span>
        </div>
      </div>
    </div>

    <!-- Optional inline video preview (we generally route to /sops/[id]) -->
    <div v-if="previewOpen" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded shadow max-w-4xl w-full p-3 space-y-2">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">{{ previewTitle }}</h3>
          <button class="text-sm border rounded px-2 py-1" @click="previewOpen=false">Close</button>
        </div>
        <video :src="previewSrc" controls class="w-full rounded border" />
      </div>
    </div>
  </div>
</template>
