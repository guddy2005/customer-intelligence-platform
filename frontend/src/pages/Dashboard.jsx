import React from 'react';
import { LayoutDashboard } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Dashboard({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Dashboard' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={LayoutDashboard}
        title="Executive Dashboard"
        description="A real-time command center with KPI widgets, trend charts, customer health scores, segment summaries and pipeline status across all data sources."
        features={[
          'Real-time KPI widgets',
          'Customer Health Score',
          'Segment Overview',
          'Revenue Attribution',
          'Pipeline Status',
          'Geo Heatmaps',
          'Alert Center',
        ]}
      />
    </>
  );
}
