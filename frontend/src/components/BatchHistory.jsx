import React from 'react';
import { History } from 'lucide-react';

export default function BatchHistory({ batches, onSelectBatch }) {
  if (!batches || batches.length === 0) {
    return (
      <div className="glass-panel" style={{ marginTop: 32 }}>
        <div className="section-header">
          <h2>
            <History size={20} color="#38bdf8" /> Recent Ingestion Executions
          </h2>
        </div>
        <div className="empty-state">No past ingestion batches recorded yet. Upload a dataset above!</div>
      </div>
    );
  }

  const getDomainTag = (domain) => {
    const d = (domain || '').toLowerCase();
    if (d.includes('banking')) return 'tag banking';
    if (d.includes('commerce')) return 'tag ecommerce';
    if (d.includes('food')) return 'tag food';
    if (d.includes('invest')) return 'tag investment';
    if (d.includes('util')) return 'tag utilities';
    if (d.includes('customer')) return 'tag customer';
    return 'tag';
  };

  return (
    <div className="glass-panel" style={{ marginTop: 32 }}>
      <div className="section-header">
        <h2>
          <History size={20} color="#38bdf8" /> Recent Ingestion Executions
        </h2>
      </div>

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Batch ID</th>
              <th>Filename</th>
              <th>Domain</th>
              <th>Total</th>
              <th>Valid</th>
              <th>Rejected</th>
              <th>Duplicates</th>
              <th>Inserted</th>
              <th>Status</th>
              <th>Ingested At</th>
            </tr>
          </thead>
          <tbody>
            {batches.map((b) => (
              <tr
                key={b.batch_id}
                style={{ cursor: 'pointer' }}
                onClick={() => onSelectBatch && onSelectBatch(b.batch_id)}
              >
                <td className="row-num">{b.batch_id}</td>
                <td style={{ fontWeight: 600 }}>{b.filename}</td>
                <td>
                  <span className={getDomainTag(b.source_domain)}>{b.source_domain}</span>
                </td>
                <td>{b.total_records}</td>
                <td style={{ color: '#10b981', fontWeight: 600 }}>{b.valid_records}</td>
                <td style={{ color: b.rejected_records > 0 ? '#ef4444' : '#64748b', fontWeight: 600 }}>
                  {b.rejected_records}
                </td>
                <td style={{ color: b.duplicate_records > 0 ? '#f59e0b' : '#64748b', fontWeight: 600 }}>
                  {b.duplicate_records}
                </td>
                <td style={{ color: '#a855f7', fontWeight: 700 }}>{b.inserted_records}</td>
                <td>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: 10,
                      fontSize: 11,
                      fontWeight: 700,
                      background: b.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: b.status === 'COMPLETED' ? '#10b981' : '#ef4444',
                    }}
                  >
                    {b.status}
                  </span>
                </td>
                <td style={{ color: '#64748b', fontSize: 12 }}>
                  {new Date(b.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
