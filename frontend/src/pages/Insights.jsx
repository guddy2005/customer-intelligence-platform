import React from 'react';
import { Lightbulb } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Insights({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Insights' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={Lightbulb}
        title="Financial Insights"
        description="AI-driven financial insights generation — surfacing consumer lifestyle classifications, wealth indicators, credit appetite signals and category spend intelligence."
        features={[
          'Lifestyle Classification',
          'Wealth Indicators',
          'Credit Appetite Score',
          'Category Spend Mix',
          'Investment Propensity',
          'Brand Affinity',
          'Auto-Generated Narratives',
        ]}
      />
    </>
  );
}
