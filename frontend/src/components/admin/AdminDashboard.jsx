import { useState } from 'react'

import { getAdminDashboardModel } from '../../dashboardModel.js'
import { useAdminPortal } from '../../hooks/useAdminPortal.js'
import Topbar from '../Topbar.jsx'
import { MetricCard, Notice } from '../ui.jsx'
import AdminAnalytics from './AdminAnalytics.jsx'
import AdminOverview from './AdminOverview.jsx'
import AdminReports from './AdminReports.jsx'
import AssignExam from './AssignExam.jsx'
import ExamBuilder from './ExamBuilder.jsx'
import ManageUsers from './ManageUsers.jsx'

const TABS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'exams', label: 'Exams' },
  { key: 'assignments', label: 'Assignments' },
  { key: 'users', label: 'Users' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'reports', label: 'Reports' },
]

export default function AdminDashboard({ api, message, setMessage, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard')
  const admin = useAdminPortal(api, setMessage)

  const model = getAdminDashboardModel(admin.adminStats, admin.assignments, admin.securityIncidents)

  return (
    <main className="portal-page">
      <Topbar tabs={TABS} activeTab={activeTab} onSelect={setActiveTab} onLogout={onLogout} />

      <section className="welcome-banner">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Monitor exams, assignments, student activity, and security events.</p>
        </div>
        <div className="banner-actions">
          <span className="role-chip">Admin Console</span>
          <button className="ghost-btn" type="button" onClick={admin.loadAdminData}>
            Refresh
          </button>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard color="blue" count={admin.adminStats?.total_students || 0} label="Students" icon="ST" helper="Active learner records" />
        <MetricCard color="green" count={admin.adminStats?.total_exams || 0} label="Exams" icon="EX" helper={`${admin.adminStats?.total_assignments || 0} assignments`} />
        <MetricCard color="cyan" count={`${model.completionRate}%`} label="Completion Rate" icon="CR" helper={`${model.pendingAssignments.length} pending`} />
        <MetricCard color="orange" count={admin.adminStats?.completed_attempts || 0} label="Submitted Attempts" icon="SA" helper={`${model.averageScore}% average`} />
      </section>

      <Notice message={message} />

      <section className="white-panel">
        <h2>Quick Actions</h2>
        <div className="quick-grid">
          <button className="action-btn blue" onClick={() => setActiveTab('exams')} type="button">
            Create New Exam
          </button>
          <button className="action-btn green" onClick={() => setActiveTab('users')} type="button">
            Manage Users
          </button>
          <button className="action-btn cyan" onClick={() => setActiveTab('reports')} type="button">
            View Reports
          </button>
          <button className="action-btn yellow" onClick={() => setActiveTab('assignments')} type="button">
            Assign Exam
          </button>
        </div>
      </section>

      {activeTab === 'dashboard' && (
        <AdminOverview
          model={model}
          assignments={admin.assignments}
          securityIncidents={admin.securityIncidents}
        />
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
        <AdminReports
          assignments={admin.assignments}
          securityIncidents={admin.securityIncidents}
        />
      )}
    </main>
  )
}
