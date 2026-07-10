import { useCallback, useEffect, useState } from 'react'

import { defaultQuestion, emptyExamForm, emptyStudentForm, examBulkTemplate, userBulkTemplate } from '../lib/constants.js'

/**
 * Owns all admin-side data and mutations. Kept in a hook so the dashboard
 * components stay presentational and the data flow is testable in isolation.
 */
export function useAdminPortal(api, setMessage) {
  const [adminStats, setAdminStats] = useState(null)
  const [students, setStudents] = useState([])
  const [exams, setExams] = useState([])
  const [assignments, setAssignments] = useState([])
  const [securityIncidents, setSecurityIncidents] = useState([])

  const [studentForm, setStudentForm] = useState(emptyStudentForm)
  const [bulkUsersText, setBulkUsersText] = useState(userBulkTemplate)
  const [examForm, setExamForm] = useState(emptyExamForm)
  const [bulkExamsText, setBulkExamsText] = useState(examBulkTemplate)
  const [assignmentForm, setAssignmentForm] = useState({ exam_id: '', student_id: '' })

  const loadAdminData = useCallback(async () => {
    try {
      const [statsData, studentsData, examsData, assignmentData, incidentData] = await Promise.all([
        api('/api/v1/admin/dashboard'),
        api('/api/v1/admin/students'),
        api('/api/v1/admin/exams'),
        api('/api/v1/admin/assignments'),
        api('/api/v1/admin/security-incidents'),
      ])
      setAdminStats(statsData)
      setStudents(studentsData)
      setExams(examsData)
      setAssignments(assignmentData)
      setSecurityIncidents(incidentData)
    } catch (error) {
      setMessage(error.message)
    }
  }, [api, setMessage])

  useEffect(() => {
    // Async fetch: state updates happen after the await, not synchronously.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAdminData()
  }, [loadAdminData])

  const createStudent = async (event) => {
    event.preventDefault()
    try {
      await api('/api/v1/admin/students', {
        method: 'POST',
        body: JSON.stringify(studentForm),
      })
      setStudentForm(emptyStudentForm())
      setMessage('Student created successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const deleteStudent = async (studentId, name) => {
    if (!window.confirm(`Delete student "${name}"? This also removes their assignments and attempts.`)) {
      return
    }
    try {
      await api(`/api/v1/admin/students/${studentId}`, { method: 'DELETE' })
      setMessage('Student deleted')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const createStudentsBulk = async () => {
    try {
      const users = bulkUsersText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .filter((line) => line.toLowerCase() !== userBulkTemplate.toLowerCase())
        .map((line) => {
          const [fullName, username, email, password] = line.split(',').map((item) => item.trim())
          return { full_name: fullName, username, email, password, role: 'student' }
        })

      if (!users.length) {
        setMessage('Add at least one student row before uploading.')
        return
      }

      await api('/api/v1/admin/students/bulk', {
        method: 'POST',
        body: JSON.stringify({ users }),
      })
      setMessage(`${users.length} students added in bulk`)
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const updateExamQuestion = (index, field, value) => {
    setExamForm((current) => ({
      ...current,
      questions: current.questions.map((question, questionIndex) =>
        questionIndex === index ? { ...question, [field]: value } : question,
      ),
    }))
  }

  const addQuestion = () => {
    setExamForm((current) => ({
      ...current,
      questions: [...current.questions, { ...defaultQuestion }],
    }))
  }

  const removeQuestion = (index) => {
    setExamForm((current) => {
      if (current.questions.length <= 1) return current
      return {
        ...current,
        questions: current.questions.filter((_, questionIndex) => questionIndex !== index),
      }
    })
  }

  const createExam = async (event) => {
    event.preventDefault()
    const validationError = validateExamForm(examForm)
    if (validationError) {
      setMessage(validationError)
      return
    }
    try {
      await api('/api/v1/admin/exams', {
        method: 'POST',
        body: JSON.stringify({
          ...examForm,
          duration_minutes: Number(examForm.duration_minutes),
          questions: examForm.questions.map((question) => ({
            ...question,
            marks: Number(question.marks),
          })),
        }),
      })
      setExamForm(emptyExamForm())
      setMessage('Exam created successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const deleteExam = async (examId, title) => {
    if (!window.confirm(`Delete exam "${title}"? This removes its questions and assignments.`)) {
      return
    }
    try {
      await api(`/api/v1/admin/exams/${examId}`, { method: 'DELETE' })
      setMessage('Exam deleted')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const createExamsBulk = async () => {
    try {
      const payload = JSON.parse(bulkExamsText)
      await api('/api/v1/admin/exams/bulk', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setMessage(`${payload.exams?.length || 0} exams added in bulk`)
      loadAdminData()
    } catch (error) {
      setMessage(error.message.startsWith('Unexpected') ? 'Bulk exams must be valid JSON.' : error.message)
    }
  }

  const assignExam = async (event) => {
    event.preventDefault()
    try {
      await api('/api/v1/admin/assignments', {
        method: 'POST',
        body: JSON.stringify({
          exam_id: Number(assignmentForm.exam_id),
          student_id: Number(assignmentForm.student_id),
        }),
      })
      setAssignmentForm({ exam_id: '', student_id: '' })
      setMessage('Exam assigned successfully')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const deleteAssignment = async (assignmentId) => {
    if (!window.confirm('Remove this assignment?')) return
    try {
      await api(`/api/v1/admin/assignments/${assignmentId}`, { method: 'DELETE' })
      setMessage('Assignment removed')
      loadAdminData()
    } catch (error) {
      setMessage(error.message)
    }
  }

  return {
    adminStats,
    students,
    exams,
    assignments,
    securityIncidents,
    studentForm,
    setStudentForm,
    bulkUsersText,
    setBulkUsersText,
    examForm,
    setExamForm,
    bulkExamsText,
    setBulkExamsText,
    assignmentForm,
    setAssignmentForm,
    loadAdminData,
    createStudent,
    deleteStudent,
    createStudentsBulk,
    updateExamQuestion,
    addQuestion,
    removeQuestion,
    createExam,
    deleteExam,
    createExamsBulk,
    assignExam,
    deleteAssignment,
  }
}

export function validateExamForm(examForm) {
  if (!examForm.title.trim() || examForm.title.trim().length < 3) {
    return 'Exam title must be at least 3 characters.'
  }
  if (!examForm.description.trim() || examForm.description.trim().length < 5) {
    return 'Exam description must be at least 5 characters.'
  }
  if (Number(examForm.duration_minutes) < 1) {
    return 'Duration must be at least 1 minute.'
  }
  if (!examForm.questions.length) {
    return 'Add at least one question.'
  }
  for (let index = 0; index < examForm.questions.length; index += 1) {
    const question = examForm.questions[index]
    const label = `Question ${index + 1}`
    if (question.question_text.trim().length < 5) {
      return `${label}: text must be at least 5 characters.`
    }
    if (
      !question.option_a.trim() ||
      !question.option_b.trim() ||
      !question.option_c.trim() ||
      !question.option_d.trim()
    ) {
      return `${label}: all four options are required.`
    }
    if (Number(question.marks) < 1) {
      return `${label}: marks must be at least 1.`
    }
  }
  return ''
}
