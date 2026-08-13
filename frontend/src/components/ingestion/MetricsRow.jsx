import React from 'react';
import MetricCard from './MetricCard';
import { Layers, CheckCircle2, XCircle, Copy, Zap } from 'lucide-react';

/**
 * MetricsRow — 5-card grid of ingestion KPI metrics.
 *
 * Props:
 *   metrics — {
 *     totalRecords, validRecords, rejectedRecords,
 *     duplicates, processed
 *   }
 * All values default to mock/display values if not provided.
 */
export default function MetricsRow({ metrics = {} }) {
  const {
    totalRecords  = '1,248,604',
    validRecords  = '1,201,337',
    rejectedRecords = '31,486',
    duplicates    = '15,781',
    processed     = '1,185,556',
  } = metrics;

  return (
    <div className="metrics-row">
      <MetricCard
        variant="total"
        icon={Layers}
        value={totalRecords}
        label="Total Records"
        sub="Across all ingestion runs"
        trend={{ direction: 'up', value: '12.4%' }}
      />
      <MetricCard
        variant="valid"
        icon={CheckCircle2}
        value={validRecords}
        label="Valid Records"
        sub="Passed all validation rules"
        trend={{ direction: 'up', value: '8.1%' }}
      />
      <MetricCard
        variant="rejected"
        icon={XCircle}
        value={rejectedRecords}
        label="Rejected Records"
        sub="Failed schema / quality checks"
        trend={{ direction: 'down', value: '3.2%' }}
      />
      <MetricCard
        variant="duplicate"
        icon={Copy}
        value={duplicates}
        label="Duplicates"
        sub="Detected and skipped"
        trend={{ direction: 'neutral', value: '0.0%' }}
      />
      <MetricCard
        variant="processed"
        icon={Zap}
        value={processed}
        label="Successfully Processed"
        sub="Written to data store"
        trend={{ direction: 'up', value: '9.7%' }}
      />
    </div>
  );
}
