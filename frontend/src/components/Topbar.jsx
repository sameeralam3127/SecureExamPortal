export default function Topbar({ tabs, activeTab, onSelect, onLogout }) {
  return (
    <header className="portal-navbar">
      <div className="brand-area">
        <span className="brand-icon">S</span>
        <span>Secure Exam Portal</span>
      </div>
      <nav className="nav-links" aria-label="Primary">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={activeTab === tab.key ? 'nav-active' : ''}
            aria-current={activeTab === tab.key ? 'page' : undefined}
            onClick={() => onSelect(tab.key)}
          >
            {tab.label}
          </button>
        ))}
        <button type="button" className="logout-btn" onClick={onLogout}>
          Logout
        </button>
      </nav>
    </header>
  )
}
