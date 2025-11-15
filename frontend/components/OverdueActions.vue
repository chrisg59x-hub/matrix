<script setup lang="ts">
const router = useRouter()

type Item = {
  id: number
  skill_name?: string | null
  skill_id?: number | null
  sop_id?: string | null
}

const props = defineProps<{
  item: Item
}>()

function goToTraining () {
  if (!props.item.skill_id) {
    router.push('/modules')
  } else {
    router.push(`/modules?skill=${props.item.skill_id}`)
  }
}

function viewSOP () {
  if (!props.item.sop_id) return
  router.push(`/sops/${props.item.sop_id}`)
}
</script>

<template>
  <div class="flex gap-2 justify-end min-w-[11rem]">
    <!-- Primary action: Start training (with icon) -->
    <button
      type="button"
      class="inline-flex items-center px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
      @click="goToTraining"
    >
      <span class="mr-1">
        Start training
      </span>
      <svg
        class="w-4 h-4"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M6 4.5v11l9-5.5-9-5.5z" />
      </svg>
    </button>

    <!-- Context-aware icon button: View modules for this skill -->
    <NuxtLink
      :to="item.skill_id ? `/modules?skill=${item.skill_id}` : '/modules'"
      class="inline-flex items-center justify-center px-2 py-1.5 text-xs rounded border text-emerald-700 hover:bg-emerald-50"
      :aria-label="item.skill_name ? `View training modules for ${item.skill_name}` : 'View related training modules'"
    >
      <svg
        class="w-4 h-4"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          d="M4 5h8v1.5H4V5zm0 4h8v1.5H4V9zm0 4h8v1.5H4V13zm10.25-8.5h1.75v1.75H14.25V4.5zm0 4h1.75v1.75H14.25V8.5zm0 4h1.75v1.75H14.25V12.5z"
        />
      </svg>
    </NuxtLink>

    <!-- View SOP -->
    <button
      v-if="item.sop_id"
      type="button"
      class="px-3 py-1.5 text-xs rounded border text-gray-700 hover:bg-gray-50"
      @click="viewSOP"
    >
      View SOP
    </button>
  </div>
</template>
