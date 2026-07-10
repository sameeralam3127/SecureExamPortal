import { useCallback, useState } from 'react'

import { getStudentDashboardModel } from '../../dashboardModel.js'
import { useStudentPortal } from '../../hooks/useStudentPortal.js'
import Topbar from '../Topbar.jsx'
import { MetricCard, Notice, PanelHeader, ProgressBar } from '../ui.jsx'
import ExamRunner from './ExamRunner.jsx'

const TABS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'exam', label: 'Exams' },
  { key: 'reports', label: 'Reports' },
]

export default function StudentDashboard({ api, user, message, setMessage, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard')
  const onEnterExam = useCallback(() => setActiveTab('exam'), [])
  const onExitToReports = useCallback(() => setActiveTab('reports'), [])

  const student = useStudentPortal(api, setMessage, { onEnterExam, onExitToReports })

  const { pendingStudentAssignments, nextAssignment, completedScore, completionRate } =
    getStudentDashboardModel(student.studentStats, student.studentAssignments, student.history)

  return (
    <main className="portal-page">
      <Topbar tabs={TABS} activeTab={activeTab} onSelect={setActiveTab} onLogout={onLogout} />

      <section className="welcome-banner">
        <div>
          <h1>Welcome, {user.full_name}!</h1>
          <p>Track assigned exams, take live assessments, and review your scores.</p>
        </div>
        <div className="banner-actions">
          <span className="role-chip">Student Portal</span>
          <button className="ghost-btn" type="button" onClick={student.loadStudentData}>
            Refresh
          </button>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard color="blue" count={student.studentStats?.assigned_exams || 0} label="Assigned Exams" icon="AE" helper="Total scheduled" />
        <MetricCard color="green" count={student.studentStats?.completed_exams || 0} label="Completed" icon="CO" helper={`${completionRate}% complete`} />
        <MetricCard color="cyan" count={student.studentStats?.pending_exams || 0} label="Pending" icon="PE" helper="Ready to start" />
        <MetricCard color="orange" count={`${student.studentStats?.average_score || 0}%`} label="Average Score" icon="AS" helper="Submitted attempts" />
      </section>

      <Notice message={message} />

      {activeTab === 'dashboard' && (
        <section className="dashboard-grid student-dashboard-grid">
          <article className="white-panel dashboard-panel focus-panel">
            <PanelHeader
              eyebrow="Next Up"
              title={nextAssignment?.exam_title || 'No pending exams'}
              action={nextAssignment ? `${nextAssignment.duration_minutes} min` : 'Clear'}
            />
            <p className="helper-text">
              {nextAssignment
                ? `Assigned ${new Date(nextAssignment.assigned_at).toLocaleDateString()} with ${nextAssignment.status || 'not started'} status.`
                : 'You are all caught up. New exams will appear here when assigned.'}
            </p>
            <button
              className="action-btn blue"
              type="button"
              disabled={!nextAssignment}
              onClick={() => setActiveTab('exam')}
            >
              Open Exams
            </button>
          </article>
          <article className="white-panel dashboard-panel">
            <PanelHeader eyebrow="Progress" title="Study Status" action={`${completionRate}%`} />
            <div className="progress-block">
              <div className="progress-copy">
                <strong>{student.studentStats?.completed_exams || 0} completed</strong>
                <span>{pendingStudentAssignments.length} still pending</span>
              </div>
              <ProgressBar value={completionRate} tone="info" />
            </div>
            <div className="status-list status-list-modern">
              <div>
                <span>Average score</span>
                <strong>{student.studentStats?.average_score || 0}%</strong>
              </div>
              <div>
                <span>Latest result</span>
                <strong>{completedScore ? `${completedScore.percentage}%` : '--'}</strong>
              </div>
            </div>
          </article>
          <article className="white-panel dashboard-panel">
            <PanelHeader eyebrow="Account" title="Profile" action="Student" />
            <div className="profile-card">
              <span className="avatar-mark">{user.full_name?.slice(0, 1) || 'S'}</span>
              <div>
                <strong>{user.full_name}</strong>
                <p className="helper-text">@{user.username}</p>
              </div>
            </div>
            <button className="mini-btn" type="button" onClick={() => setActiveTab('reports')}>
              View Results
            </button>
          </article>
        </section>
      )}

      {activeTab === 'exam' && (
        <ExamRunner
          liveExam={student.liveExam}
          studentAssignments={student.studentAssignments}
          answers={student.answers}
          currentQuestionIndex={student.currentQuestionIndex}
          setCurrentQuestionIndex={student.setCurrentQuestionIndex}
          isReviewMode={student.isReviewMode}
          setIsReviewMode={student.setIsReviewMode}
          autosaveState={student.autosaveState}
          secondsLeft={student.secondsLeft}
          securityWarning={student.securityWarning}
          autosaveAnswer={student.autosaveAnswer}
          submitExam={student.submitExam}
          onStart={student.startExam}
        />
      )}

      {activeTab === 'reports' && (
        <section className="white-panel">
          <h2>Score History</h2>
          <div className="list-stack">
            {student.history.length ? (
              student.history.map((attempt) => (
                <div className="row-card" key={attempt.attempt_id}>
                  <strong>{attempt.exam_title}</strong>
                  <p>
                    Score {attempt.score}/{attempt.total_marks} | {attempt.percentage}% |{' '}
                    {attempt.status}
                  </p>
                </div>
              ))
            ) : (
              <p className="helper-text">No attempts submitted yet.</p>
            )}
          </div>
        </section>
      )}
    </main>
  )
}
