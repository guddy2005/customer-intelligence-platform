import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function ErrorTable({ errors }) {
  if (!errors || errors.length === 0) {
    return (
      <div className="glass-panel" style={{ marginTop: 24, padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#10b981' }}>
          <AlertCircle size={18} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Zero validation errors detected in this batch!</span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ marginTop: 24 }}>
      <div className="section-header">
        <h2>
          <AlertCircle size={20} color="#ef4444" /> Validation Error Log ({errors.length})
        </h2>
      </div>

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Row #</th>
              <th>Target Field</th>
              <th>Error Detail</th>
              <th>Raw Value Received</th>
            </tr>
          </thead>
          <tbody>
            {errors.map((err, idx) => (
              <tr key={idx}>
                <td className="row-num">#{err.row}</td>
                <td>
                  <span style={{ fontWeight: 700, color: '#f8fafc' }}>
                    {err.field || 'General'}
                  </span>
                </td>
                <td style={{ color: '#f87171', fontWeight: 500 }}>{err.error}</td>
                <td>
                  <code style={{ background: '#1e293b', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', color: '#94a3b8' }}>
                    {err.raw_value !== null ? String(err.raw_value) : 'N/A'}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
