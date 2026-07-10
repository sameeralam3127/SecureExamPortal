import { PanelHeader, ProgressBar, StatusBadge } from '../ui.jsx'

export default function AdminOverview({ model, assignments, securityIncidents }) {
  const {
    pendingAssignments,
    completedAssignments,
    latestAssignments,
    latestIncidents,
    completionRate,
    securityReviewCount,
    averageScore,
    topScore,
  } = model

  return (
    <section className="dashboard-grid dashboard-grid-modern">
      <article className="white-panel dashboard-panel command-panel">
        <PanelHeader eyebrow="Today" title="Exam Operations" action={`${completionRate}% complete`} />
        <div className="progress-block">
          <div className="progress-copy">
            <strong>
              {completedAssignments.length} of {assignments.length}
            </strong>
            <span>assignments submitted</span>
          </div>
          <ProgressBar value={completionRate} tone="success" />
        </div>
        <div className="status-list status-list-modern">
          <div>
            <span>Pending review</span>
            <strong>{pendingAssignments.length}</strong>
          </div>
          <div>
            <span>Average score</span>
            <strong>{averageScore}%</strong>
          </div>
          <div>
            <span>Highest score</span>
            <strong>{topScore}%</strong>
          </div>
        </div>
      </article>

      <article className="white-panel dashboard-panel insight-panel">
        <PanelHeader eyebrow="Risk" title="Security Watch" action={`${securityReviewCount} recent`} />
        <div className="incident-score">
          <strong>{securityIncidents.length}</strong>
          <span>Total incident logs</span>
        </div>
        <div className="list-stack compact-list">
          {latestIncidents.length ? (
            latestIncidents.map((incident) => (
              <div className="activity-row" key={`dash-incident-${incident.id}`}>
                <span className="activity-dot danger-dot" />
                <div>
                  <strong>{incident.incident_type.replaceAll('_', ' ')}</strong>
                  <p>
                    {incident.student_name || 'Student'} on {incident.exam_title || 'Exam'}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="helper-text">No security incidents logged.</p>
          )}
        </div>
      </article>

      <article className="white-panel dashboard-panel wide-panel">
        <PanelHeader eyebrow="Live Feed" title="Recent Assignments" action={`${latestAssignments.length} latest`} />
        <div className="data-table">
          <div className="table-row table-head">
            <span>Exam</span>
            <span>Student</span>
            <span>Status</span>
            <span>Score</span>
          </div>
          {latestAssignments.length ? (
            latestAssignments.map((assignment) => (
              <div className="table-row" key={`dash-assignment-${assignment.id}`}>
                <strong>{assignment.exam_title}</strong>
                <span>{assignment.student_name}</span>
                <StatusBadge status={assignment.attempt_status || 'pending'} />
                <span>{assignment.latest_score ?? '--'}</span>
              </div>
            ))
          ) : (
            <p className="helper-text">No assignments created yet.</p>
          )}
        </div>
      </article>
    </section>
  )
}
