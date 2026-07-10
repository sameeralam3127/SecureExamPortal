export default function AdminReports({ assignments, securityIncidents }) {
  return (
    <section className="two-grid">
      <article className="white-panel">
        <h2>Assignment &amp; Score Report</h2>
        <div className="list-stack">
          {assignments.length ? (
            assignments.map((assignment) => (
              <div className="row-card" key={`report-${assignment.id}`}>
                <strong>{assignment.exam_title}</strong>
                <p>
                  {assignment.student_name} | {assignment.attempt_status || 'pending'} | Score{' '}
                  {assignment.latest_score ?? '--'}
                </p>
              </div>
            ))
          ) : (
            <p className="helper-text">No assignments to report yet.</p>
          )}
        </div>
      </article>
      <article className="white-panel wide-panel">
        <h2>Security Incident Report</h2>
        <div className="list-stack">
          {securityIncidents.length ? (
            securityIncidents.map((incident) => (
              <div className="row-card" key={incident.id}>
                <strong>{incident.incident_type.replaceAll('_', ' ')}</strong>
                <p>
                  {incident.student_name || 'Student'} | {incident.exam_title || 'Exam'} |{' '}
                  {new Date(incident.occurred_at).toLocaleString()}
                </p>
                <p>{incident.detail}</p>
              </div>
            ))
          ) : (
            <p className="helper-text">No security incidents logged yet.</p>
          )}
        </div>
      </article>
    </section>
  )
}
