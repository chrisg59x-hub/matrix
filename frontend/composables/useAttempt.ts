// composables/useAttempt.ts
type PublicChoice = { id: string; text: string }
type PublicQuestion = {
  id: string
  qtype: string
  text: string
  points: number
  choices: PublicChoice[]
}

type NextQuestionPayload = {
  attempt_id: string
  question: PublicQuestion | null
  remaining: number
  total: number
}

type SubmitResponse = {
  attempt_id: string
  question_id: string
  completed: boolean
  remaining: number
  correct?: boolean
  earned?: number
  max_points?: number
  message?: string
}

type FinishPayload = {
  attempt_id: string
  percent: number
  passed: boolean
  score: number
  max_score: number
  feedback: {
    question_id: string
    earned: number
    max: number
    correct: boolean
    message: string
  }[]
}

export function useAttempt() {
  const { get, post } = useApi()

  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchNext(attemptId: string): Promise<NextQuestionPayload> {
    loading.value = true
    error.value = null
    try {
      return await get<NextQuestionPayload>(`/attempts/${attemptId}/next/`)
    } catch (e: any) {
      error.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load next question')
      throw e
    } finally {
      loading.value = false
    }
  }

  async function submitQuestion(
    attemptId: string,
    questionId: string,
    choiceIds: string[],
    timeTaken?: number
  ): Promise<SubmitResponse> {
    loading.value = true
    error.value = null
    try {
      const body: any = { question_id: questionId, choice_ids: choiceIds }
      if (typeof timeTaken === 'number') body.time_taken = timeTaken
      return await post<SubmitResponse>(`/attempts/${attemptId}/submit/`, body)
    } catch (e: any) {
      error.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to submit answer')
      throw e
    } finally {
      loading.value = false
    }
  }

  async function finishAttempt(attemptId: string): Promise<FinishPayload> {
    loading.value = true
    error.value = null
    try {
      return await post<FinishPayload>(`/attempts/${attemptId}/finish/`, {})
    } catch (e: any) {
      error.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to finish attempt')
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, fetchNext, submitQuestion, finishAttempt }
}
