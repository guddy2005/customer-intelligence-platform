import React from 'react';
import { ChevronRight, Menu } from 'lucide-react';

/**
 * TopBar — sticky page-level header with breadcrumb + status indicator.
 *
 * Props:
 *   crumbs  — array of { label, onClick? }  (last item is rendered as leaf)
 *   status  — 'active' | 'idle'
 *   statusLabel — string label for status pill
 *   actions — optional React node to render on the right side
 *   onOpenMobileSidebar — callback to open mobile sidebar (injected by AppLayout)
 */
export default function TopBar({
  crumbs = [],
  status = 'active',
  statusLabel = 'Pipeline Active',
  actions,
  onOpenMobileSidebar,
}) {
  return (
    <div className="topbar">
      {/* Left: hamburger (mobile) + breadcrumb */}
      <div className="topbar-left">
        <button
          className="hamburger-btn"
          onClick={onOpenMobileSidebar}
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <nav className="topbar-breadcrumb" aria-label="breadcrumb">
          {crumbs.map((crumb, i) => {
            const isLast = i === crumbs.length - 1;
            return (
              <React.Fragment key={i}>
                {i > 0 && (
                  <ChevronRight size={13} className="breadcrumb-sep" style={{ color: 'var(--text-faint)' }} />
                )}
                <span
                  className={
                    isLast
                      ? 'breadcrumb-leaf'
                      : crumb.onClick
                      ? 'breadcrumb-root'
                      : 'breadcrumb-root'
                  }
                  style={{ cursor: crumb.onClick ? 'pointer' : 'default' }}
                  onClick={crumb.onClick}
                >
                  {crumb.label}
                </span>
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      {/* Right side */}
      <div className="topbar-actions">
        {actions}
        <div className={`status-pill ${status}`}>
          {status === 'active' && <div className="pulse-dot" />}
          <span className="status-label-text">{statusLabel}</span>
        </div>
      </div>
    </div>
  );
}
