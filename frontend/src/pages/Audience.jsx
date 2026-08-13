import React from 'react';
import { Target } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Audience({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Audience' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={Target}
        title="Audience Segmentation"
        description="Build, explore and activate dynamic audience segments using behavioral, financial, demographic and lifestyle signals for targeted marketing and analytics."
        features={[
          'Dynamic Segmentation',
          'RFM Scoring',
          'Behavioral Clusters',
          'Lookalike Audiences',
          'Segment Builder',
          'Audience Overlap',
          'Activation Integrations',
        ]}
      />
    </>
  );
}
