import React, { useState, useEffect, useCallback, useRef } from 'react';
import { DatabaseZap, CheckCircle2, AlertCircle, Clock, Loader2 } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import DataSourceGrid from '../components/ingestion/DataSourceGrid';
import ImportPanel from '../components/ingestion/ImportPanel';
import MetricsRow from '../components/ingestion/MetricsRow';
import IngestionHistory from '../components/ingestion/IngestionHistory';
import ValidationErrors from '../components/ingestion/ValidationErrors';
import { uploadCSVFile, fetchIngestionBatches, pollBatchStatus } from '../services/api';

export default function DataIngestion({ onNavigate, onOpenMobileSidebar }) {
  const [selectedSource, setSelectedSource] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [batches, setBatches] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [notification, setNotification] = useState(null);

  // Live progress tracking
  const [activeBatch, setActiveBatch] = useState(null); // { batch_id, filename, ... }
  const pollRef = useRef(null);

  const loadBatches = useCallback(async () => {
    try {
      const data = await fetchIngestionBatches();
      if (Array.isArray(data) && data.length > 0) {
        const formatted = data.map((b) => ({
          id: b.batch_id,
          source: b.input_type || b.source_domain || 'UNKNOWN',
          domain: (b.input_type || b.source_domain || 'unknown').toLowerCase(),
          dataset: b.filename,
          records: (b.total_records || 0).toLocaleString(),
          valid: (b.valid_records || 0).toLocaleString(),
          rejected: (b.rejected_records || 0).toLocaleString(),
          duplicates: (b.duplicate_records || 0).toLocaleString(),
          date: b.created_at ? new Date(b.created_at).toLocaleString() : '—',
          status: b.status,
        }));
        setBatches(formatted);
      }
    } catch (e) {
      console.warn('Could not fetch batches from backend (using fallback):', e.message);
    }
  }, []);

  useEffect(() => {
    loadBatches();
  }, [loadBatches]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  const handleProcess = async ({ inputType, file, batchSize }) => {
    if (!file) return;
    setIsLoading(true);
    setNotification(null);
    setActiveBatch(null);
    setValidationErrors([]);

    try {
      // Step 1: Submit file — returns immediately with batch_id + status=PROCESSING
      const result = await uploadCSVFile(file, inputType || 'AUTO_DETECT', '', batchSize || 1000);

      setActiveBatch({
        batch_id: result.batch_id,
        filename: result.filename || file.name,
        input_type: result.input_type,
        status: 'PROCESSING',
        total_records: 0,
        valid_records: 0,
        rejected_records: 0,
        duplicate_records: 0,
        inserted_records: 0,
      });

      setNotification({
        type: 'info',
        message: `Batch ${result.batch_id} submitted. Pipeline is processing ${file.name} in the background...`,
      });

      // Step 2: Poll for live progress
      await pollBatchStatus(
        result.batch_id,
        // onProgress callback — called every poll interval
        (batch) => {
          setActiveBatch(batch);
          setNotification({
            type: 'info',
            message: `Processing ${batch.filename || file.name} — ${(batch.valid_records || 0).toLocaleString()} valid / ${(batch.total_records || 0).toLocaleString()} total records...`,
          });
        },
        3000,       // poll every 3 seconds
        30 * 60 * 1000  // max wait 30 minutes
      ).then((finalBatch) => {
        // Step 3: Done — show final result
        setActiveBatch(finalBatch);

        const isSuccess = finalBatch.status === 'COMPLETED' || finalBatch.status === 'PARTIAL';

        let breakdownText = '';
        if (finalBatch.domain_breakdown && Object.keys(finalBatch.domain_breakdown).length > 0) {
          breakdownText = Object.entries(finalBatch.domain_breakdown)
            .map(([domain, count]) => `${domain}: ${count.toLocaleString()}`)
            .join(' | ');
        }

        const insertedCount = (finalBatch.inserted_records || 0).toLocaleString();
        const validCount = (finalBatch.valid_records || 0).toLocaleString();
        const totalCount = (finalBatch.total_records || 0).toLocaleString();

        setNotification({
          type: isSuccess ? 'success' : 'error',
          message: `Batch ${finalBatch.batch_id} ${finalBatch.status}. ${insertedCount} records inserted into CDM. (${validCount} valid / ${totalCount} total)${breakdownText ? ` — Breakdown: [ ${breakdownText} ]` : ''}`,
        });

        // Show error log if any
        if (finalBatch.errors && finalBatch.errors.length > 0) {
          const mappedErrors = finalBatch.errors.map((err) => ({
            row: err.row,
            field: err.field || 'record',
            value: err.raw_value || 'N/A',
            rule: err.error,
            severity: 'error',
          }));
          setValidationErrors(mappedErrors);
        }

        loadBatches();
        setIsLoading(false);
        setActiveBatch(null);
      });

    } catch (err) {
      setNotification({
        type: 'error',
        message: `Ingestion failed: ${err.message}`,
      });
      setActiveBatch(null);
      setIsLoading(false);
    }
  };

  // Compute progress percentage for the active batch
  const progressPct = activeBatch && activeBatch.total_records > 0
    ? Math.min(100, Math.round(
        ((activeBatch.valid_records || 0) + (activeBatch.rejected_records || 0) + (activeBatch.duplicate_records || 0))
        / activeBatch.total_records * 100
      ))
    : null;

  return (
    <>
      <TopBar
        crumbs={[
          { label: 'Customer Intelligence Platform', onClick: () => onNavigate('dashboard') },
          { label: 'Data Ingestion' },
          { label: 'Ingestion Hub' },
        ]}
        status="active"
        statusLabel="Pipeline Engine Active"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />

      <div className="page-content">

        {/* Notification Banner */}
        {notification && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              marginBottom: 20,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              background:
                notification.type === 'success' ? 'var(--success-bg)'
                : notification.type === 'error'   ? 'var(--danger-bg)'
                : 'rgba(99,102,241,0.08)',
              border: `1px solid ${
                notification.type === 'success' ? 'var(--success-border)'
                : notification.type === 'error'   ? 'rgba(239,68,68,0.25)'
                : 'rgba(99,102,241,0.25)'
              }`,
              color:
                notification.type === 'success' ? 'var(--success)'
                : notification.type === 'error'   ? 'var(--danger)'
                : 'var(--primary-light)',
              fontSize: '13px',
              fontWeight: 500,
              lineHeight: 1.5,
            }}
          >
            {notification.type === 'success'
              ? <CheckCircle2 size={18} style={{ minWidth: 18, marginTop: 2 }} />
              : notification.type === 'error'
              ? <AlertCircle size={18} style={{ minWidth: 18, marginTop: 2 }} />
              : <Loader2 size={18} style={{ minWidth: 18, marginTop: 2, animation: 'spin 1s linear infinite' }} />
            }
            <span>{notification.message}</span>
          </div>
        )}

        {/* Live Batch Progress Panel */}
        {activeBatch && activeBatch.status === 'PROCESSING' && (
          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-md)',
              marginBottom: 20,
              background: 'var(--bg-surface)',
              border: '1px solid rgba(99,102,241,0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Clock size={15} style={{ color: 'var(--primary-light)' }} />
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                Live Batch Progress — {activeBatch.batch_id}
              </span>
              <span className="badge badge-info" style={{ fontSize: '10.5px', marginLeft: 'auto' }}>
                PROCESSING
              </span>
            </div>

            {/* Stats row */}
            <div style={{ display: 'flex', gap: 24, marginBottom: 12, flexWrap: 'wrap' }}>
              {[
                { label: 'Total Records', value: activeBatch.total_records, color: 'var(--text-sub)' },
                { label: 'Valid', value: activeBatch.valid_records, color: 'var(--success)' },
                { label: 'Rejected', value: activeBatch.rejected_records, color: 'var(--danger)' },
                { label: 'Duplicates', value: activeBatch.duplicate_records, color: 'var(--warning)' },
                { label: 'Inserted', value: activeBatch.inserted_records, color: 'var(--primary-light)' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', fontWeight: 700, color, fontFamily: 'var(--font-mono)' }}>
                    {(value || 0).toLocaleString()}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>

            {/* Progress bar */}
            {progressPct !== null && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Progress</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-sub)', fontFamily: 'var(--font-mono)' }}>
                    {progressPct}%
                  </span>
                </div>
                <div style={{ height: 6, background: 'var(--bg-card)', borderRadius: 999, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${progressPct}%`,
                      background: 'linear-gradient(90deg, var(--primary), var(--primary-light))',
                      borderRadius: 999,
                      transition: 'width 0.5s ease',
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Page Header */}
        <div className="page-header">
          <div className="page-header-top">
            <div>
              <h1 className="page-title">
                <span style={{ marginRight: 10 }}>
                  <DatabaseZap size={26} style={{ display: 'inline', verticalAlign: 'middle', color: 'var(--primary-light)', marginRight: 8 }} />
                </span>
                Data Ingestion Hub
              </h1>
              <p className="page-subtitle">
                Upload communication datasets (SMS) or structured transactions. The engine streams, parses,
                and classifies each record at the record level into the Common Data Model.
              </p>
            </div>
            <span className="page-badge">
              <DatabaseZap size={12} />
              Hub
            </span>
          </div>
        </div>

        {/* Section 1 — Metrics */}
        <MetricsRow />

        <hr className="divider" />

        {/* Section 2 — Import Panel */}
        <div className="section">
          <div className="section-header">
            <div className="section-title">Import &amp; Process Data</div>
          </div>
          <ImportPanel
            isLoading={isLoading}
            onProcess={handleProcess}
          />
        </div>

        <hr className="divider" />

        {/* Section 3 — Data Source Categories (Informational) */}
        <DataSourceGrid
          selectedSource={selectedSource}
          onSelect={setSelectedSource}
        />

        <hr className="divider" />

        {/* Section 4 — Ingestion History */}
        <IngestionHistory rows={batches} onRefresh={loadBatches} />

        <hr className="divider" />

        {/* Section 5 — Validation & Error Log */}
        <ValidationErrors errors={validationErrors} defaultOpen={validationErrors.length > 0} />
      </div>

      {/* Inline spinner keyframe */}
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </>
  );
}
