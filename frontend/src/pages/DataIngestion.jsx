import React, { useState } from 'react';
import { DatabaseZap } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import DataSourceGrid from '../components/ingestion/DataSourceGrid';
import ImportPanel from '../components/ingestion/ImportPanel';
import MetricsRow from '../components/ingestion/MetricsRow';
import IngestionHistory from '../components/ingestion/IngestionHistory';
import ValidationErrors from '../components/ingestion/ValidationErrors';

export default function DataIngestion({ onNavigate, onOpenMobileSidebar }) {
  const [selectedSource, setSelectedSource] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handler for the "Process & Ingest" button.
   * Currently UI-only: simulates a brief processing state.
   */
  const handleProcess = ({ source, dataType, file }) => {
    setIsLoading(true);
    // Simulate async processing (UI only — no real backend call yet)
    setTimeout(() => setIsLoading(false), 2200);
  };

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
                Configure data sources, upload test datasets, and monitor ingestion pipeline health across all connected systems.
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

        {/* Section 2 — Data Source Categories */}
        <DataSourceGrid
          selectedSource={selectedSource}
          onSelect={setSelectedSource}
        />

        {/* Section 3 — Import Panel */}
        <div className="section">
          <div className="section-header">
            <div className="section-title">Import & Process Data</div>
          </div>
          <ImportPanel
            selectedSource={selectedSource}
            isLoading={isLoading}
            onProcess={handleProcess}
          />
        </div>

        <hr className="divider" />

        {/* Section 4 — Ingestion History */}
        <IngestionHistory onRefresh={() => {}} />

        <hr className="divider" />

        {/* Section 5 — Validation & Error Log */}
        <ValidationErrors />
      </div>
    </>
  );
}
