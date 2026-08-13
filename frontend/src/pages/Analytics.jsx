import React from 'react';
import { BarChart3 } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Analytics({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Analytics' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={BarChart3}
        title="Behavioral Analytics"
        description="Advanced analytics engine surfacing spending patterns, category affinities, lifecycle stages and behavioral cohorts across your entire customer base."
        features={[
          'Spending Pattern Analysis',
          'Category Intelligence',
          'Affinity Modelling',
          'Cohort Analysis',
          'Funnel Analytics',
          'Retention Curves',
          'LTV Modelling',
        ]}
      />
    </>
  );
}
