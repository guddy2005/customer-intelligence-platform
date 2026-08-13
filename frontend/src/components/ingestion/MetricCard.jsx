import React from 'react';

/**
 * MetricCard — single KPI card with colored accent bar.
 *
 * Props:
 *   variant  — 'total' | 'valid' | 'rejected' | 'duplicate' | 'processed'
 *   icon     — Lucide icon component
 *   value    — number or string
 *   label    — string
 *   sub      — optional sub-label string
 *   trend    — optional { direction: 'up'|'down'|'neutral', value: string }
 */
export default function MetricCard({ variant = 'total', icon: Icon, value, label, sub, trend }) {
  return (
    <div className={`metric-card ${variant}`}>
      <div className="metric-top">
        <div className={`metric-icon ${variant}`}>
          {Icon && <Icon size={18} />}
        </div>
        {trend && (
          <span className={`metric-trend ${trend.direction}`}>
            {trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : '—'}
            {trend.value}
          </span>
        )}
      </div>
      <div>
        <div className={`metric-value ${variant}`}>
          {value ?? '—'}
        </div>
        <div className="metric-label">{label}</div>
        {sub && <div className="metric-sub">{sub}</div>}
      </div>
    </div>
  );
}
