import { useState } from 'react'

import { getAdminDashboardModel } from '../../dashboardModel.js'
import { useAdminPortal } from '../../hooks/useAdminPortal.js'
import { Notice, StatTile } from '../ui.jsx'
import AdminAnalytics from './AdminAnalytics.jsx'
import AdminOverview from './AdminOverview.jsx'
import AdminReports from './AdminReports.jsx'
import AdminShell from './AdminShell.jsx'
import AssignExam from './AssignExam.jsx'
import ExamBuilder from './ExamBuilder.jsx'
import ManageUsers from './ManageUsers.jsx'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Overview', icon: 'dashboard' },
  { key: 'exams', label: 'Exams', icon: 'exams' },
  { key: 'assignments', label: 'Assignments', icon: 'assignments' },
  { key: 'users', label: 'Users', icon: 'users' },
  { key: 'analytics', label: 'Analytics', icon: 'analytics' },
  { key: 'reports', label: 'Reports', icon: 'reports' },
]

const PAGE_META = {
  dashboard: { title: 'Overview', subtitle: 'Monitor exams, assignments, and security at a glance.' },
  exams: { title: 'Exams', subtitle: 'Author exams and manage the question bank.' },
  assignments: { title: 'Assignments', subtitle: 'Assign exams to students and track delivery.' },
  users: { title: 'Users', subtitle: 'Create, search, and manage student accounts.' },
  analytics: { title: 'Analytics', subtitle: 'Results, completion, and operational metrics.' },
  reports: { title: 'Reports', subtitle: 'Score reports and the security incident log.' },
}

export default function AdminDashboard({ api, user, message, setMessage, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard')
  const admin = useAdminPortal(api, setMessage)

  const model = getAdminDashboardModel(admin.adminStats, admin.assignments, admin.securityIncidents)
  const meta = PAGE_META[activeTab] || PAGE_META.dashboard

  return (
    <AdminShell
      navItems={NAV_ITEMS}
      activeTab={activeTab}
      onSelect={setActiveTab}
      title={meta.title}
      subtitle={meta.subtitle}
      user={user}
      onRefresh={admin.loadAdminData}
      onLogout={onLogout}
    >
      <Notice message={message} />

      {activeTab === 'dashboard' && (
        <>
          <section className="stat-row">
            <StatTile
              tone="blue"
              icon="users"
              value={admin.adminStats?.total_students || 0}
              label="Students"
              helper="Active records"
            />
            <StatTile
              tone="violet"
              icon="exams"
              value={admin.adminStats?.total_exams || 0}
              label="Exams"
              helper={`${admin.adminStats?.total_assignments || 0} assignments`}
            />
            <StatTile
              tone="teal"
              icon="analytics"
              value={`${model.completionRate}%`}
              label="Completion"
              helper={`${model.pendingAssignments.length} pending`}
            />
            <StatTile
              tone="amber"
              icon="reports"
              value={admin.adminStats?.completed_attempts || 0}
              label="Submitted"
              helper={`${model.averageScore}% avg score`}
            />
          </section>
          <AdminOverview
            model={model}
            assignments={admin.assignments}
            securityIncidents={admin.securityIncidents}
          />
        </>
      )}

      {activeTab === 'users' && (
        <ManageUsers
          students={admin.students}
          studentForm={admin.studentForm}
          setStudentForm={admin.setStudentForm}
          onCreateStudent={admin.createStudent}
          onDeleteStudent={admin.deleteStudent}
          bulkUsersText={admin.bulkUsersText}
          setBulkUsersText={admin.setBulkUsersText}
          onBulkUpload={admin.createStudentsBulk}
        />
      )}

      {activeTab === 'exams' && (
        <ExamBuilder
          examForm={admin.examForm}
          setExamForm={admin.setExamForm}
          updateExamQuestion={admin.updateExamQuestion}
          addQuestion={admin.addQuestion}
          removeQuestion={admin.removeQuestion}
          onCreateExam={admin.createExam}
          exams={admin.exams}
          onDeleteExam={admin.deleteExam}
          bulkExamsText={admin.bulkExamsText}
          setBulkExamsText={admin.setBulkExamsText}
          onBulkUpload={admin.createExamsBulk}
        />
      )}

      {activeTab === 'assignments' && (
        <AssignExam
          exams={admin.exams}
          students={admin.students}
          assignmentForm={admin.assignmentForm}
          setAssignmentForm={admin.setAssignmentForm}
          onAssign={admin.assignExam}
          assignments={admin.assignments}
          onDeleteAssignment={admin.deleteAssignment}
        />
      )}

      {activeTab === 'analytics' && (
        <AdminAnalytics analytics={admin.analytics} auditEvents={admin.auditEvents} />
      )}

      {activeTab === 'reports' && (
        <AdminReports assignments={admin.assignments} securityIncidents={admin.securityIncidents} />
      )}
    </AdminShell>
  )
}
