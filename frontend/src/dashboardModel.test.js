import assert from 'node:assert/strict'
import test from 'node:test'

import { getAdminDashboardModel, getStudentDashboardModel } from './dashboardModel.js'

test('admin dashboard model summarizes completion, latest records, and scores', () => {
  const assignments = [
    { id: 1, attempt_status: 'submitted', latest_score: 91 },
    { id: 2, attempt_status: 'in_progress', latest_score: 64 },
    { id: 3, attempt_status: null, latest_score: null },
    { id: 4, attempt_status: 'submitted', latest_score: 74 },
    { id: 5, attempt_status: 'submitted', latest_score: 88 },
    { id: 6, attempt_status: null, latest_score: undefined },
  ]
  const incidents = [
    { id: 1 },
    { id: 2 },
    { id: 3 },
    { id: 4 },
    { id: 5 },
  ]

  const model = getAdminDashboardModel({ average_score: 82.5 }, assignments, incidents)

  assert.equal(model.pendingAssignments.length, 3)
  assert.equal(model.completedAssignments.length, 3)
  assert.equal(model.completionRate, 50)
  assert.equal(model.averageScore, 82.5)
  assert.equal(model.topScore, 91)
  assert.equal(model.latestAssignments.length, 5)
  assert.equal(model.latestIncidents.length, 4)
  assert.equal(model.securityReviewCount, 4)
})

test('admin dashboard model handles empty API payloads safely', () => {
  const model = getAdminDashboardModel()

  assert.equal(model.completionRate, 0)
  assert.equal(model.averageScore, 0)
  assert.equal(model.topScore, 0)
  assert.deepEqual(model.pendingAssignments, [])
  assert.deepEqual(model.latestIncidents, [])
})

test('student dashboard model prioritizes the next unsubmitted exam and progress', () => {
  const assignments = [
    { assignment_id: 1, exam_title: 'Already Done', status: 'submitted' },
    { assignment_id: 2, exam_title: 'Network Security', status: null },
    { assignment_id: 3, exam_title: 'Database Systems', status: 'in_progress' },
  ]
  const history = [{ attempt_id: 9, percentage: 76 }]

  const model = getStudentDashboardModel(
    { assigned_exams: 3, completed_exams: 1 },
    assignments,
    history,
  )

  assert.equal(model.pendingStudentAssignments.length, 2)
  assert.equal(model.nextAssignment.exam_title, 'Network Security')
  assert.equal(model.completedScore.percentage, 76)
  assert.equal(model.completionRate, 33)
})

test('student dashboard model avoids divide-by-zero and missing history errors', () => {
  const model = getStudentDashboardModel({ assigned_exams: 0, completed_exams: 0 }, [], [])

  assert.equal(model.completionRate, 0)
  assert.equal(model.nextAssignment, null)
  assert.equal(model.completedScore, null)
})
