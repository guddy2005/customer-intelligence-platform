import React from 'react';
import { CreditCard } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Transactions({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Transactions' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={CreditCard}
        title="Transaction Intelligence"
        description="Deep transaction-level analysis across banking, e-commerce, investments, food delivery and all connected financial data sources."
        features={[
          'Cross-Source Transaction View',
          'Spend Category Breakdown',
          'Merchant Intelligence',
          'Payment Mode Analysis',
          'Anomaly Detection',
          'Transaction Search',
          'Temporal Trends',
        ]}
      />
    </>
  );
}
