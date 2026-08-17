import React, { useState } from 'react';
import { Play, FileText, Layers, Settings2 } from 'lucide-react';
import UploadZone from './UploadZone';

const INPUT_TYPES = [
  { value: 'AUTO_DETECT',   label: 'Auto Detect (SMS / Transactions / Customers)' },
  { value: 'SMS',           label: 'SMS / Communication Logs (Multi-Source)' },
  { value: 'TRANSACTIONS',  label: 'Structured Transactions CSV' },
  { value: 'CUSTOMERS',     label: 'Customer Master Profiles' },
  { value: 'JSON',          label: 'JSON / Event Stream' },
];

const BATCH_SIZE_OPTIONS = [
  { value: 500,  label: '500  — Conservative (low RAM)' },
  { value: 1000, label: '1000 — Default (recommended)' },
  { value: 2000, label: '2000 — Fast (moderate RAM)' },
  { value: 5000, label: '5000 — High throughput' },
];

/**
 * ImportPanel — Input type selector + Batch size + UploadZone + process button.
 *
 * Source domain is NOT selected here — it is determined at RECORD LEVEL
 * by the classification engine after parsing.
 *
 * Props:
 *   isLoading  — bool, disables form while processing
 *   onProcess  — callback({ inputType, file, batchSize })
 */
export default function ImportPanel({ isLoading, onProcess }) {
  const [inputType, setInputType] = useState('AUTO_DETECT');
  const [batchSize, setBatchSize] = useState(1000);
  const [file, setFile] = useState(null);

  const canProcess = Boolean(file) && !isLoading;

  const handleProcess = () => {
    if (!canProcess) return;
    onProcess({ inputType, file, batchSize });
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon" style={{ background: 'var(--primary-dim)', color: 'var(--primary-light)' }}>
            <Play size={15} />
          </div>
          Import &amp; Ingest Dataset
        </div>
      </div>

      {/* Row 1: Input Type + Classification Mode */}
      <div className="import-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="form-group">
          <label className="form-label" htmlFor="input-type-select">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileText size={14} style={{ color: 'var(--primary-light)' }} />
              Input / Content Type
            </span>
          </label>
          <select
            id="input-type-select"
            className="select-control"
            value={inputType}
            onChange={(e) => setInputType(e.target.value)}
            disabled={isLoading}
          >
            {INPUT_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Layers size={14} style={{ color: 'var(--accent)' }} />
              Classification Mode
            </span>
          </label>
          <div
            style={{
              padding: '9px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-light)',
              color: 'var(--text-sub)',
              fontSize: '12.5px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Record-Level · Multi-Domain</span>
            <span className="badge badge-success" style={{ fontSize: '10.5px' }}>Active</span>
          </div>
        </div>
      </div>

      {/* Row 2: Batch Size */}
      <div className="form-group" style={{ marginBottom: 16 }}>
        <label className="form-label" htmlFor="batch-size-select">
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Settings2 size={14} style={{ color: 'var(--warning)' }} />
            Batch Size
            <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 400 }}>
              — records processed per DB commit cycle
            </span>
          </span>
        </label>
        <select
          id="batch-size-select"
          className="select-control"
          value={batchSize}
          onChange={(e) => setBatchSize(Number(e.target.value))}
          disabled={isLoading}
          style={{ maxWidth: 340 }}
        >
          {BATCH_SIZE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', marginTop: 5 }}>
          For SMS-Data.csv (100k+ records): 1000 is recommended. Larger batches are faster but use more RAM.
        </div>
      </div>

      {/* Upload Zone */}
      <UploadZone file={file} onFileChange={isLoading ? undefined : setFile} />

      {/* Process Button */}
      <div className="mt-4">
        <button
          id="process-btn"
          className="btn btn-primary btn-lg btn-full"
          disabled={!canProcess}
          onClick={handleProcess}
        >
          {isLoading ? (
            <>
              <div className="spinner" />
              Processing Pipeline — Polling for Status...
            </>
          ) : (
            <>
              <Play size={16} />
              Process &amp; Ingest Dataset
            </>
          )}
        </button>
      </div>
    </div>
  );
}
