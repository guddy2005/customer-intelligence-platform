import React from 'react';
import { History, RefreshCw } from 'lucide-react';

/* Mock ingestion history for visual demonstration */
const MOCK_HISTORY = [
  {
    id: 'ING-2048',
    source: 'Banking',
    domain: 'banking',
    dataset: 'Bank Transactions',
    records: '124,500',
    valid: '121,002',
    rejected: '2,108',
    duplicates: '1,390',
    date: '2026-08-13 14:30',
    status: 'COMPLETED',
  },
  {
    id: 'ING-2047',
    source: 'E-Commerce',
    domain: 'ecommerce',
    dataset: 'Orders',
    records: '87,312',
    valid: '85,900',
    rejected: '812',
    duplicates: '600',
    date: '2026-08-13 11:15',
    status: 'COMPLETED',
  },
  {
    id: 'ING-2046',
    source: 'Food Delivery',
    domain: 'food_delivery',
    dataset: 'Food Orders',
    records: '56,740',
    valid: '55,200',
    rejected: '940',
    duplicates: '600',
    date: '2026-08-12 22:00',
    status: 'COMPLETED',
  },
  {
    id: 'ING-2045',
    source: 'Investments',
    domain: 'investments',
    dataset: 'SIP Transactions',
    records: '33,890',
    valid: '33,100',
    rejected: '540',
    duplicates: '250',
    date: '2026-08-12 18:45',
    status: 'COMPLETED',
  },
  {
    id: 'ING-2044',
    source: 'Healthcare',
    domain: 'healthcare',
    dataset: 'Pharmacy Orders',
    records: '19,204',
    valid: '17,800',
    rejected: '1,204',
    duplicates: '200',
    date: '2026-08-12 15:20',
    status: 'PARTIAL',
  },
  {
    id: 'ING-2043',
    source: 'Utilities',
    domain: 'utilities',
    dataset: 'Electricity Bills',
    records: '45,110',
    valid: '44,800',
    rejected: '210',
    duplicates: '100',
    date: '2026-08-11 09:10',
    status: 'COMPLETED',
  },
  {
    id: 'ING-2042',
    source: 'Travel',
    domain: 'travel',
    dataset: 'Flight Bookings',
    records: '12,800',
    valid: '0',
    rejected: '12,800',
    duplicates: '0',
    date: '2026-08-10 23:55',
    status: 'FAILED',
  },
  {
    id: 'ING-2041',
    source: 'Insurance',
    domain: 'insurance',
    dataset: 'Premium Payments',
    records: '28,600',
    valid: '28,100',
    rejected: '300',
    duplicates: '200',
    date: '2026-08-10 16:30',
    status: 'COMPLETED',
  },
];

const STATUS_CONFIG = {
  COMPLETED: { className: 'badge-success', label: 'Completed' },
  PARTIAL:   { className: 'badge-warning', label: 'Partial' },
  FAILED:    { className: 'badge-danger',  label: 'Failed' },
  RUNNING:   { className: 'badge-info',    label: 'Running' },
};

/**
 * IngestionHistory — table of recent ingestion runs.
 *
 * Props:
 *   rows     — array of ingestion run objects (falls back to mock data)
 *   onRefresh — optional callback to refresh data
 */
export default function IngestionHistory({ rows, onRefresh }) {
  const data = rows && rows.length > 0 ? rows : MOCK_HISTORY;

  return (
    <div className="section">
      <div className="section-header">
        <div className="section-title">
          <History size={17} style={{ color: 'var(--accent)' }} />
          Recent Ingestion Runs
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="section-count">{data.length} runs shown</span>
          {onRefresh && (
            <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
              <RefreshCw size={13} />
              Refresh
            </button>
          )}
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table" aria-label="Ingestion History">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Source</th>
              <th>Dataset / Data Type</th>
              <th>Records</th>
              <th>Valid</th>
              <th>Rejected</th>
              <th>Duplicates</th>
              <th>Date & Time</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => {
              const statusCfg = STATUS_CONFIG[row.status] || STATUS_CONFIG.COMPLETED;
              return (
                <tr key={row.id}>
                  <td>
                    <span className="table-mono">{row.id}</span>
                  </td>
                  <td>
                    <span className={`domain-tag domain-${row.domain}`}>{row.source}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-sub)' }}>
                    {row.dataset}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {row.records}
                  </td>
                  <td style={{ color: 'var(--success)', fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {row.valid}
                  </td>
                  <td
                    style={{
                      color: parseInt(row.rejected) > 0 ? 'var(--danger)' : 'var(--text-dim)',
                      fontWeight: 600,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                    }}
                  >
                    {row.rejected}
                  </td>
                  <td
                    style={{
                      color: parseInt(row.duplicates) > 0 ? 'var(--warning)' : 'var(--text-dim)',
                      fontWeight: 600,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                    }}
                  >
                    {row.duplicates}
                  </td>
                  <td style={{ color: 'var(--text-dim)', fontSize: 12 }}>{row.date}</td>
                  <td>
                    <span className={`badge ${statusCfg.className}`}>{statusCfg.label}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
