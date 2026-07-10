import { useCallback, useEffect, useState } from 'react'

import { useExamGuard } from './useExamGuard.js'

/**
 * Owns student-facing data plus the full live-exam session (timer, autosave,
 * navigation, and integrity guard). `onEnterExam` / `onExitToReports` let the
 * hosting dashboard switch tabs as the session starts and ends.
 */
export function useStudentPortal(api, setMessage, { onEnterExam, onExitToReports } = {}) {
  const [studentStats, setStudentStats] = useState(null)
  const [studentAssignments, setStudentAssignments] = useState([])
  const [history, setHistory] = useState([])

  const [liveExam, setLiveExam] = useState(null)
  const [answers, setAnswers] = useState({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [autosaveState, setAutosaveState] = useState('')
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [securityWarning, setSecurityWarning] = useState('')

  const loadStudentData = useCallback(async () => {
    try {
      const [statsData, assignmentData, historyData] = await Promise.all([
        api('/api/v1/student/dashboard'),
        api('/api/v1/student/assignments'),
        api('/api/v1/student/attempts/history'),
      ])
      setStudentStats(statsData)
      setStudentAssignments(assignmentData)
      setHistory(historyData)
    } catch (error) {
      setMessage(error.message)
    }
  }, [api, setMessage])

  useEffect(() => {
    // Async fetch: state updates happen after the await, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadStudentData()
  }, [loadStudentData])

  const logIncident = useCallback(
    (incidentType, detail) => {
      setSecurityWarning(detail)
      if (!liveExam) return
      api(`/api/v1/student/attempts/${liveExam.attempt_id}/security-incidents`, {
        method: 'POST',
        body: JSON.stringify({ incident_type: incidentType, detail }),
      }).catch((error) => setAutosaveState(`Security log failed: ${error.message}`))
    },
    [api, liveExam],
  )

  useExamGuard(liveExam, logIncident)

  const submitExam = useCallback(async () => {
    if (!liveExam) return
    try {
      const result = await api(`/api/v1/student/attempts/${liveExam.attempt_id}/submit`, {
        method: 'POST',
        body: JSON.stringify({
          answers: Object.entries(answers).map(([questionId, selectedOption]) => ({
            question_id: Number(questionId),
            selected_option: selectedOption,
          })),
        }),
      })
      setMessage(`Exam submitted. Score ${result.score}/${result.total_marks} (${result.percentage}%)`)
      setLiveExam(null)
      setAnswers({})
      setSecurityWarning('')
      setCurrentQuestionIndex(0)
      setIsReviewMode(false)
      setAutosaveState('')
      setSecondsLeft(0)
      onExitToReports?.()
      loadStudentData()
    } catch (error) {
      setMessage(error.message)
    }
  }, [api, answers, liveExam, loadStudentData, onExitToReports, setMessage])

  // Countdown timer.
  useEffect(() => {
    if (!liveExam || secondsLeft <= 0) return undefined
    const timerId = window.setInterval(() => {
      setSecondsLeft((value) => Math.max(value - 1, 0))
    }, 1000)
    return () => window.clearInterval(timerId)
  }, [liveExam, secondsLeft])

  // Auto-submit when the timer runs out.
  useEffect(() => {
    if (liveExam && secondsLeft === 0) {
      // Auto-submit on timeout; submission state updates run after the await.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      submitExam()
    }
  }, [secondsLeft, liveExam, submitExam])

  const startExam = async (assignmentId) => {
    try {
      const data = await api(`/api/v1/student/assignments/${assignmentId}/start`, { method: 'POST' })
      setLiveExam(data)
      setSecurityWarning('')
      setAnswers(
        Object.fromEntries(
          (data.saved_answers || []).map((answer) => [answer.question_id, answer.selected_option]),
        ),
      )
      setCurrentQuestionIndex(data.current_question_index || 0)
      setIsReviewMode(false)
      setAutosaveState('')
      setSecondsLeft(data.duration_minutes * 60)
      onEnterExam?.()
      if (data.enforce_fullscreen && document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {
          setSecurityWarning(
            'Fullscreen is required for this exam. Use the browser prompt to enter fullscreen.',
          )
        })
      }
    } catch (error) {
      setMessage(error.message)
    }
  }

  const autosaveAnswer = async (questionId, selectedOption) => {
    if (!liveExam) return
    const nextAnswers = { ...answers, [questionId]: selectedOption }
    setAnswers(nextAnswers)
    setAutosaveState('Saving...')
    try {
      await api(`/api/v1/student/attempts/${liveExam.attempt_id}/answers`, {
        method: 'PUT',
        body: JSON.stringify({
          answers: Object.entries(nextAnswers).map(([savedQuestionId, savedOption]) => ({
            question_id: Number(savedQuestionId),
            selected_option: savedOption,
          })),
        }),
      })
      setAutosaveState('All answers saved')
    } catch (error) {
      setAutosaveState('Autosave failed')
      setMessage(error.message)
    }
  }

  return {
    studentStats,
    studentAssignments,
    history,
    liveExam,
    answers,
    currentQuestionIndex,
    setCurrentQuestionIndex,
    isReviewMode,
    setIsReviewMode,
    autosaveState,
    secondsLeft,
    securityWarning,
    loadStudentData,
    startExam,
    autosaveAnswer,
    submitExam,
  }
}
