import { useState } from 'react'

import Icon from '../icons.jsx'

/**
 * Professional admin layout: a dark, collapsible sidebar for navigation and a
 * light content area with a sticky topbar. Purely presentational — nav state
 * and page content come from props.
 */
export default function AdminShell({
  navItems,
  activeTab,
  onSelect,
  title,
  subtitle,
  user,
  onRefresh,
  onLogout,
  children,
}) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const initials = (user?.full_name || 'A')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className={`admin-shell ${collapsed ? 'is-collapsed' : ''} ${mobileOpen ? 'is-open' : ''}`}>
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <span className="admin-brand-icon">
            <Icon name="shield" size={20} />
          </span>
          <span className="admin-brand-text">Secure Exam</span>
        </div>

        <nav className="admin-nav" aria-label="Admin sections">
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={activeTab === item.key ? 'admin-nav-item active' : 'admin-nav-item'}
              aria-current={activeTab === item.key ? 'page' : undefined}
              onClick={() => {
                onSelect(item.key)
                setMobileOpen(false)
              }}
            >
              <Icon name={item.icon} size={19} />
              <span className="admin-nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-footer">
          <div className="admin-user">
            <span className="admin-avatar">{initials}</span>
            <div className="admin-user-meta">
              <strong>{user?.full_name || 'Administrator'}</strong>
              <span>@{user?.username || 'admin'}</span>
            </div>
          </div>
          <button type="button" className="admin-logout" onClick={onLogout}>
            <Icon name="logout" size={18} />
            <span className="admin-nav-label">Sign out</span>
          </button>
        </div>
      </aside>

      <button
        type="button"
        className="admin-scrim"
        aria-label="Close menu"
        onClick={() => setMobileOpen(false)}
      />

      <div className="admin-main">
        <header className="admin-topbar">
          <div className="admin-topbar-left">
            <button
              type="button"
              className="admin-icon-btn admin-menu-btn"
              aria-label="Toggle menu"
              onClick={() => setMobileOpen((open) => !open)}
            >
              <Icon name="menu" size={20} />
            </button>
            <button
              type="button"
              className="admin-icon-btn admin-collapse-btn"
              aria-label="Collapse sidebar"
              onClick={() => setCollapsed((value) => !value)}
            >
              <Icon name="menu" size={20} />
            </button>
            <div className="admin-page-heading">
              <h1>{title}</h1>
              {subtitle ? <p>{subtitle}</p> : null}
            </div>
          </div>
          <div className="admin-topbar-actions">
            <button type="button" className="admin-icon-btn" aria-label="Refresh data" onClick={onRefresh}>
              <Icon name="refresh" size={18} />
            </button>
            <span className="admin-role-pill">Admin</span>
          </div>
        </header>

        <div className="admin-content">{children}</div>
      </div>
    </div>
  )
}
