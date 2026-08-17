import React, { useState } from 'react';
import './index.css';

import AppLayout from './components/layout/AppLayout';

// Pages
import Dashboard          from './pages/Dashboard';
import CustomerProfiles   from './pages/CustomerProfiles';
import CustomerProfileDetail from './pages/CustomerProfileDetail';
import Transactions       from './pages/Transactions';
import Analytics          from './pages/Analytics';
import Audience           from './pages/Audience';
import Insights           from './pages/Insights';
import Predictions        from './pages/Predictions';
import Reports            from './pages/Reports';
import DataIngestion      from './pages/DataIngestion';

const PAGE_MAP = {
  dashboard:           Dashboard,
  customers:           CustomerProfiles,
  'customer-profile':  CustomerProfileDetail,
  transactions:        Transactions,
  analytics:           Analytics,
  audience:            Audience,
  insights:            Insights,
  predictions:         Predictions,
  reports:             Reports,
  ingestion:           DataIngestion,
};

export default function App() {
  const [activePage, setActivePage] = useState('ingestion');
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);

  const handleNavigate = (page, customerId = null) => {
    setActivePage(page);
    setSelectedCustomerId(customerId);
  };

  const PageComponent = PAGE_MAP[activePage] || DataIngestion;

  return (
    <AppLayout activePage={activePage} onNavigate={handleNavigate}>
      <PageComponent
        onNavigate={handleNavigate}
        selectedCustomerId={selectedCustomerId}
      />
    </AppLayout>
  );
}
