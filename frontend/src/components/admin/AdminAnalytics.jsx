import { PanelHeader, ProgressBar, StatTile } from '../ui.jsx'

function formatAction(action) {
  return action.replaceAll('.', ' · ').replaceAll('_', ' ')
}

export default function AdminAnalytics({ analytics, auditEvents }) {
  if (!analytics) {
    return (
      <section className="white-panel">
        <p className="helper-text">Loading analytics…</p>
      </section>
    )
  }

  const { assignments, results, incidents, exam_performance: examPerformance } = analytics
  const incidentTypes = Object.entries(incidents.by_type || {})

  return (
    <section className="admin-stack">
      <section className="stat-row">
        <StatTile tone="violet" icon="exams" value={analytics.total_exams} label="Exams" helper={`${analytics.active_exams} active`} />
        <StatTile tone="blue" icon="assignments" value={assignments.total} label="Assignments" helper={`${assignments.submitted} submitted`} />
        <StatTile tone="teal" icon="analytics" value={`${results.average_score}%`} label="Average Score" helper={`${results.submitted_attempts} attempts`} />
        <StatTile tone="rose" icon="shield" value={incidents.total} label="Security Incidents" helper={`${incidentTypes.length} types`} />
      </section>

      <section className="two-grid">
        <article className="white-panel">
          <PanelHeader eyebrow="Assignments" title="Completion Breakdown" action={`${assignments.total} total`} />
          <div className="status-list status-list-modern">
            <div>
              <span>Submitted</span>
              <strong>{assignments.submitted}</strong>
            </div>
            <div>
              <span>In progress</span>
              <strong>{assignments.in_progress}</strong>
            </div>
            <div>
              <span>Pending</span>
              <strong>{assignments.pending}</strong>
            </div>
          </div>
        </article>

        <article className="white-panel">
          <PanelHeader
            eyebrow="Results"
            title="Score Metrics"
            action={`Pass ≥ ${analytics.pass_threshold}%`}
          />
          <div className="progress-block">
            <div className="progress-copy">
              <strong>{results.pass_rate}% pass rate</strong>
              <span>{results.submitted_attempts} submitted attempts</span>
            </div>
            <ProgressBar value={results.pass_rate} tone="success" />
          </div>
          <div className="status-list status-list-modern">
            <div>
              <span>Average</span>
              <strong>{results.average_score}%</strong>
            </div>
            <div>
              <span>Highest</span>
              <strong>{results.highest_score}%</strong>
            </div>
            <div>
              <span>Lowest</span>
              <strong>{results.lowest_score}%</strong>
            </div>
          </div>
        </article>
      </section>

      <article className="white-panel">
        <h2>Exam Performance</h2>
        {examPerformance.length ? (
          <div className="data-table">
            <div className="table-row table-head">
              <span>Exam</span>
              <span>Assignments</span>
              <span>Submissions</span>
              <span>Avg score</span>
            </div>
            {examPerformance.map((exam) => (
              <div className="table-row" key={`perf-${exam.exam_id}`}>
                <strong>{exam.title}</strong>
                <span>{exam.assignments}</span>
                <span>{exam.submissions}</span>
                <span>{exam.average_score}%</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="helper-text">No exam activity yet.</p>
        )}
      </article>

      <section className="two-grid">
        <article className="white-panel">
          <h2>Incident Types</h2>
          {incidentTypes.length ? (
            <div className="list-stack compact-list">
              {incidentTypes
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => (
                  <div className="activity-row" key={`inc-${type}`}>
                    <span className="activity-dot danger-dot" />
                    <div>
                      <strong>{type.replaceAll('_', ' ')}</strong>
                      <p>{count} logged</p>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="helper-text">No security incidents logged.</p>
          )}
        </article>

        <article className="white-panel">
          <h2>Recent Admin Activity</h2>
          {auditEvents.length ? (
            <div className="list-stack compact-list">
              {auditEvents.slice(0, 12).map((event) => (
                <div className="activity-row" key={`audit-${event.id}`}>
                  <span className="activity-dot" />
                  <div>
                    <strong>{formatAction(event.action)}</strong>
                    <p>
                      {event.actor_username || 'system'} ·{' '}
                      {new Date(event.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="helper-text">No audit activity recorded yet.</p>
          )}
        </article>
      </section>
    </section>
  )
}
