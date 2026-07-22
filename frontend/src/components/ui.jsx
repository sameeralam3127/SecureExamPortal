import Icon from './icons.jsx'

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

// Clean SaaS-style stat tile used across the admin dashboard.
export function StatTile({ tone = 'blue', icon, value, label, helper }) {
  return (
    <article className={`stat-tile tone-${tone}`}>
      <div className="stat-tile-head">
        <span className="stat-chip">
          <Icon name={icon} size={18} />
        </span>
        {helper ? <span className="stat-helper">{helper}</span> : null}
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-label">{label}</span>
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
