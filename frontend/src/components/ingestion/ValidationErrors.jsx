import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, ShieldAlert } from 'lucide-react';

/* Mock validation errors for visual demonstration */
const MOCK_ERRORS = [
  {
    row: 142,
    field: 'transaction_date',
    value: 'BAD_DATE_FORMAT',
    rule: 'ISO8601 or DD/MM/YYYY required',
    severity: 'error',
  },
  {
    row: 87,
    field: 'amount',
    value: 'INVALID_AMOUNT',
    rule: 'Numeric value expected',
    severity: 'error',
  },
  {
    row: 204,
    field: 'customer_id',
    value: '',
    rule: 'customer_id cannot be null',
    severity: 'error',
  },
  {
    row: 316,
    field: 'email',
    value: 'not-an-email',
    rule: 'Valid email format required',
    severity: 'warning',
  },
  {
    row: 55,
    field: 'phone',
    value: '+910000000000',
    rule: 'Suspicious phone pattern detected',
    severity: 'warning',
  },
];

const SEVERITY_CONFIG = {
  error:   { className: 'badge-danger',  label: 'Error' },
  warning: { className: 'badge-warning', label: 'Warning' },
};

/**
 * ValidationErrors — collapsible accordion showing validation error table.
 *
 * Props:
 *   errors — array of error objects (falls back to mock data for demo)
 *   defaultOpen — boolean, whether panel starts open (default: false)
 */
export default function ValidationErrors({ errors, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const data = errors && errors.length > 0 ? errors : MOCK_ERRORS;
  const errorCount = data.filter((e) => e.severity === 'error').length;
  const warnCount  = data.filter((e) => e.severity === 'warning').length;

  return (
    <div className="section">
      {/* Accordion header */}
      <div
        className="accordion-header"
        onClick={() => setOpen((o) => !o)}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onKeyDown={(e) => e.key === 'Enter' && setOpen((o) => !o)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ShieldAlert size={17} style={{ color: errorCount > 0 ? 'var(--danger)' : 'var(--warning)' }} />
          <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-sub)' }}>
            Validation & Error Log
          </span>
          <span className="badge badge-danger" style={{ marginLeft: 4 }}>
            {errorCount} errors
          </span>
          <span className="badge badge-warning">
            {warnCount} warnings
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-dim)' }}>
          <span style={{ fontSize: 12, fontWeight: 500 }}>
            {open ? 'Collapse' : 'Expand'}
          </span>
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {/* Accordion body */}
      {open && (
        <div className="accordion-body">
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table" aria-label="Validation Errors">
              <thead>
                <tr>
                  <th>Row #</th>
                  <th>Field</th>
                  <th>Received Value</th>
                  <th>Validation Rule</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {data.map((err, i) => {
                  const sevCfg = SEVERITY_CONFIG[err.severity] || SEVERITY_CONFIG.error;
                  return (
                    <tr key={i}>
                      <td>
                        <span className="table-mono">#{err.row}</span>
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        {err.field}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {err.value || <span style={{ color: 'var(--text-faint)', fontStyle: 'italic' }}>null / empty</span>}
                      </td>
                      <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                        {err.rule}
                      </td>
                      <td>
                        <span className={`badge ${sevCfg.className}`}>
                          {sevCfg.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
