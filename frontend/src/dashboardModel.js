export function getAdminDashboardModel(adminStats = {}, assignments = [], securityIncidents = []) {
  const pendingAssignments = assignments.filter((item) => item.attempt_status !== 'submitted')
  const completedAssignments = assignments.filter((item) => item.attempt_status === 'submitted')
  const latestAssignments = assignments.slice(0, 5)
  const latestIncidents = securityIncidents.slice(0, 4)
  const completionRate = assignments.length
    ? Math.round((completedAssignments.length / assignments.length) * 100)
    : 0
  const scoredAssignments = assignments.filter(
    (item) => item.latest_score !== null && item.latest_score !== undefined,
  )
  const topScore = scoredAssignments.length
    ? Math.max(...scoredAssignments.map((item) => Number(item.latest_score) || 0))
    : 0

  return {
    pendingAssignments,
    completedAssignments,
    latestAssignments,
    latestIncidents,
    completionRate,
    securityReviewCount: latestIncidents.length,
    averageScore: adminStats?.average_score || 0,
    topScore,
  }
}

export function getStudentDashboardModel(studentStats = {}, studentAssignments = [], history = []) {
  const pendingStudentAssignments = studentAssignments.filter((item) => item.status !== 'submitted')
  const nextAssignment = pendingStudentAssignments[0] || null
  const completedScore = history[0] || null
  const assignedExams = studentStats?.assigned_exams || 0
  const completionRate = assignedExams
    ? Math.round(((studentStats.completed_exams || 0) / assignedExams) * 100)
    : 0

  return {
    pendingStudentAssignments,
    nextAssignment,
    completedScore,
    completionRate,
  }
}
