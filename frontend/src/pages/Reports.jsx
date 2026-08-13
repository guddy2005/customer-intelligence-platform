import React from 'react';
import { FileBarChart } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Reports({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Reports' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={FileBarChart}
        title="Business Intelligence Reports"
        description="Scheduled and on-demand reporting — executive summaries, segment performance reports, category trend reports and exportable intelligence decks."
        features={[
          'Executive Summary Reports',
          'Segment Performance',
          'Category Trend Reports',
          'Scheduled Delivery',
          'PDF / Excel Export',
          'Custom Report Builder',
          'Share & Collaborate',
        ]}
      />
    </>
  );
}
