import React from 'react';
import { Users } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function CustomerProfiles({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Customer Profiles' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={Users}
        title="Customer Profiles"
        description="360° unified customer profiles stitching identity, demographics, behavioral signals and financial footprints from all connected data sources."
        features={[
          '360° Unified Profile',
          'Identity Graph',
          'Behavioral Signals',
          'Financial Footprint',
          'Lifestyle Classification',
          'Risk Scoring',
          'Profile Search & Filter',
        ]}
      />
    </>
  );
}
