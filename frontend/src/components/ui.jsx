export function MetricCard({ color, count, label, icon, helper }) {
  return (
    <article className={`metric-card ${color}`}>
      <div>
        <h3>{count}</h3>
        <p>{label}</p>
        {helper ? <span>{helper}</span> : null}
      </div>
      <span className="metric-icon">{icon}</span>
    </article>
  )
}

export function PanelHeader({ eyebrow, title, action }) {
  return (
    <div className="panel-header">
      <div>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action ? <strong>{action}</strong> : null}
    </div>
  )
}

export function ProgressBar({ value, tone = 'success' }) {
  const normalizedValue = Math.min(Math.max(Number(value) || 0, 0), 100)
  return (
    <div className={`progress-track ${tone}`}>
      <span style={{ width: `${normalizedValue}%` }} />
    </div>
  )
}

export function StatusBadge({ status }) {
  const label = status.replaceAll('_', ' ')
  const tone = status === 'submitted' ? 'success' : status === 'in_progress' ? 'info' : 'neutral'
  return <span className={`status-badge ${tone}`}>{label}</span>
}

export function Notice({ message }) {
  if (!message) return null
  return (
    <div className="notice-bar" role="status" aria-live="polite">
      {message}
    </div>
  )
}
