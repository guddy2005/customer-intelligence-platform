import React from 'react';
import { Layers, CheckCircle, AlertTriangle, Copy, Database } from 'lucide-react';

export default function IngestionSummary({ summary }) {
  if (!summary) return null;

  const { total_records, valid_records, rejected_records, duplicate_records, inserted_records } = summary;

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-icon total">
          <Layers size={22} />
        </div>
        <div>
          <div className="metric-val" style={{ color: '#3b82f6' }}>{total_records}</div>
          <div className="metric-lbl">Total Records Received</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon valid">
          <CheckCircle size={22} />
        </div>
        <div>
          <div className="metric-val" style={{ color: '#10b981' }}>{valid_records}</div>
          <div className="metric-lbl">Valid Records</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon rejected">
          <AlertTriangle size={22} />
        </div>
        <div>
          <div className="metric-val" style={{ color: '#ef4444' }}>{rejected_records}</div>
          <div className="metric-lbl">Rejected / Failed</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon duplicates">
          <Copy size={22} />
        </div>
        <div>
          <div className="metric-val" style={{ color: '#f59e0b' }}>{duplicate_records}</div>
          <div className="metric-lbl">Duplicates Skipped</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon inserted">
          <Database size={22} />
        </div>
        <div>
          <div className="metric-val" style={{ color: '#a855f7' }}>{inserted_records}</div>
          <div className="metric-lbl">CDM MySQL Inserted</div>
        </div>
      </div>
    </div>
  );
}
