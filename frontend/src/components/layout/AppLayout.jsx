import React, { useState, useCallback } from 'react';
import Sidebar from './Sidebar';

export default function AppLayout({ activePage, onNavigate, children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNavigate = useCallback((key) => {
    onNavigate(key);
    setMobileOpen(false); // close sidebar on mobile after navigation
  }, [onNavigate]);

  return (
    <div className="app-shell">
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
      />

      <div className={`main-content${collapsed ? ' sidebar-collapsed' : ''}`}>
        {/* Inject hamburger button into children context via cloneElement */}
        {React.Children.map(children, (child) =>
          React.isValidElement(child)
            ? React.cloneElement(child, { onOpenMobileSidebar: () => setMobileOpen(true) })
            : child
        )}
      </div>
    </div>
  );
}
