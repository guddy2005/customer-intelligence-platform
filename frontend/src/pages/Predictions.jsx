import React from 'react';
import { TrendingUp } from 'lucide-react';
import TopBar from '../components/common/TopBar';
import PlaceholderPage from '../components/common/PlaceholderPage';

export default function Predictions({ onNavigate, onOpenMobileSidebar }) {
  return (
    <>
      <TopBar
        crumbs={[{ label: 'Customer Intelligence Platform' }, { label: 'Predictions' }]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />
      <PlaceholderPage
        icon={TrendingUp}
        title="Predictive Audience Generation"
        description="ML-powered prediction engine for churn forecasting, next-best-action recommendations, product propensity scoring and trend analysis."
        features={[
          'Churn Prediction',
          'Next Purchase Propensity',
          'Product Recommendations',
          'Trend Forecasting',
          'Lifetime Value Prediction',
          'Lookalike Modelling',
          'Model Performance Monitoring',
        ]}
      />
    </>
  );
}
