import React from 'react';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  BarChart3,
  Target,
  Lightbulb,
  TrendingUp,
  FileBarChart,
  DatabaseZap,
  Brain,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    label: 'Overview',
    items: [
      { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Data',
    items: [
      { key: 'customers', label: 'Customer Profiles', icon: Users },
      { key: 'transactions', label: 'Transactions', icon: CreditCard },
      { key: 'ingestion', label: 'Data Ingestion', icon: DatabaseZap, badge: 'Hub' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { key: 'analytics', label: 'Analytics', icon: BarChart3 },
      { key: 'audience', label: 'Audience', icon: Target },
      { key: 'insights', label: 'Insights', icon: Lightbulb },
    ],
  },
  {
    label: 'Output',
    items: [
      { key: 'predictions', label: 'Predictions', icon: TrendingUp },
      { key: 'reports', label: 'Reports', icon: FileBarChart },
    ],
  },
];

export default function Sidebar({ activePage, onNavigate, collapsed, onToggleCollapse, mobileOpen }) {
  return (
    <aside className={`sidebar${collapsed ? ' collapsed' : ''}${mobileOpen ? ' mobile-open' : ''}`}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <Brain size={20} color="#ffffff" />
        </div>
        <div className="sidebar-brand-text">
          <div className="brand-name">CIP Platform</div>
          <div className="brand-sub">Customer Intelligence</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map(({ key, label, icon: Icon, badge }) => (
              <div
                key={key}
                className={`nav-item${activePage === key ? ' active' : ''}`}
                onClick={() => onNavigate(key)}
                title={collapsed ? label : undefined}
              >
                <span className="nav-icon">
                  <Icon size={18} />
                </span>
                <span className="nav-label">{label}</span>
                {badge && !collapsed && (
                  <span className="nav-badge">{badge}</span>
                )}
              </div>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer Toggle */}
      <div className="sidebar-footer">
        <button className="sidebar-toggle" onClick={onToggleCollapse}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
