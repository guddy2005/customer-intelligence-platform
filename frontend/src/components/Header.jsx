import React from 'react';
import { Database, ShieldCheck } from 'lucide-react';

export default function Header() {
  return (
    <header className="app-header">
      <div className="brand-title">
        <div className="brand-icon">
          <Database size={24} color="#ffffff" />
        </div>
        <div>
          <h1>Customer Intelligence Platform <span className="brand-badge">Ingestion Hub</span></h1>
        </div>
      </div>
      <div className="status-badge">
        <div className="pulse-dot"></div>
        <span>Pipeline Engine Active</span>
      </div>
    </header>
  );
}
