import React, { useMemo, useState } from 'react';
import {
  Search,
  Filter,
  Users,
  UserCheck,
  ShieldAlert,
  Wallet,
  ChevronDown,
  X,
  MapPin,
  Activity,
  CreditCard,
  MessageSquare,
  TrendingUp,
  Calendar,
  ArrowUpRight,
} from 'lucide-react';

import TopBar from '../components/common/TopBar';

const customers = [
  {
    id: 'CUS-10021',
    name: 'Customer 10021',
    initials: 'C1',
    segment: 'High Value',
    industry: 'Banking',
    location: 'Delhi',
    transactions: 84,
    spend: 284500,
    lastActivity: '2 hours ago',
    risk: 'Low',
    riskScore: 18,
    engagement: 92,
    messages: 146,
    avgTransaction: 3398,
    activeSince: 'Jan 2024',
    behavior: ['Frequent banking activity', 'High digital engagement'],
    categories: ['Banking', 'Travel', 'E-Commerce'],
  },
  {
    id: 'CUS-10022',
    name: 'Customer 10022',
    initials: 'C2',
    segment: 'Regular',
    industry: 'E-Commerce',
    location: 'Mumbai',
    transactions: 42,
    spend: 98600,
    lastActivity: '5 hours ago',
    risk: 'Low',
    riskScore: 24,
    engagement: 76,
    messages: 82,
    avgTransaction: 2348,
    activeSince: 'Mar 2024',
    behavior: ['Frequent online purchases', 'Weekend activity'],
    categories: ['E-Commerce', 'Food', 'Entertainment'],
  },
  {
    id: 'CUS-10023',
    name: 'Customer 10023',
    initials: 'C3',
    segment: 'At Risk',
    industry: 'Utilities',
    location: 'Bangalore',
    transactions: 18,
    spend: 42600,
    lastActivity: '18 days ago',
    risk: 'High',
    riskScore: 78,
    engagement: 31,
    messages: 38,
    avgTransaction: 2366,
    activeSince: 'Jun 2023',
    behavior: ['Declining activity', 'Low engagement'],
    categories: ['Utilities', 'Banking'],
  },
  {
    id: 'CUS-10024',
    name: 'Customer 10024',
    initials: 'C4',
    segment: 'Premium',
    industry: 'Travel',
    location: 'Gurgaon',
    transactions: 67,
    spend: 193800,
    lastActivity: '1 day ago',
    risk: 'Medium',
    riskScore: 46,
    engagement: 84,
    messages: 112,
    avgTransaction: 2892,
    activeSince: 'Aug 2023',
    behavior: ['Frequent travel purchases', 'Premium spending pattern'],
    categories: ['Travel', 'Dining', 'Banking'],
  },
  {
    id: 'CUS-10025',
    name: 'Customer 10025',
    initials: 'C5',
    segment: 'Regular',
    industry: 'Telecom',
    location: 'Pune',
    transactions: 31,
    spend: 67500,
    lastActivity: '3 days ago',
    risk: 'Low',
    riskScore: 21,
    engagement: 69,
    messages: 71,
    avgTransaction: 2177,
    activeSince: 'Nov 2024',
    behavior: ['Consistent monthly activity', 'Telecom focused'],
    categories: ['Telecom', 'Utilities', 'E-Commerce'],
  },
];

const formatCurrency = (value) => {
  return `₹${value.toLocaleString('en-IN')}`;
};

function StatCard({ icon: Icon, label, value, description }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <h3 className="mt-2 text-2xl font-bold text-slate-900">{value}</h3>
          <p className="mt-1 text-xs text-slate-400">{description}</p>
        </div>

        <div className="rounded-lg bg-slate-100 p-2.5">
          <Icon size={20} className="text-slate-700" />
        </div>
      </div>
    </div>
  );
}

function RiskBadge({ risk }) {
  const styles = {
    Low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Medium: 'bg-amber-50 text-amber-700 border-amber-200',
    High: 'bg-red-50 text-red-700 border-red-200',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${
        styles[risk]
      }`}
    >
      {risk}
    </span>
  );
}

function SegmentBadge({ segment }) {
  const styles = {
    'High Value': 'bg-violet-50 text-violet-700',
    Premium: 'bg-blue-50 text-blue-700',
    Regular: 'bg-slate-100 text-slate-700',
    'At Risk': 'bg-red-50 text-red-700',
  };

  return (
    <span
      className={`rounded-md px-2 py-1 text-xs font-medium ${
        styles[segment] || styles.Regular
      }`}
    >
      {segment}
    </span>
  );
}

function CustomerProfileDrawer({ customer, onClose }) {
  if (!customer) return null;

  return (
    <div className="customer-profile-overlay">
      <div className="customer-profile-drawer">
        <div className="customer-profile-drawer-header">
          <div className="customer-profile-drawer-profile">
            <div className="customer-profile-drawer-avatar">
              {customer.initials}
            </div>

            <div>
              <div className="customer-profile-drawer-title-row">
                <h2 className="customer-profile-drawer-name">
                  {customer.name}
                </h2>
                <RiskBadge risk={customer.risk} />
              </div>

              <p className="customer-profile-drawer-meta">
                {customer.id} · {customer.industry}
              </p>

              <div className="customer-profile-drawer-location">
                <MapPin size={14} />
                {customer.location}
              </div>
            </div>
          </div>

          <button className="customer-profile-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="customer-profile-drawer-body">
          <section className="customer-profile-section">
            <div className="customer-profile-section-header">
              <h3>Profile Overview</h3>
              <SegmentBadge segment={customer.segment} />
            </div>

            <div className="customer-profile-metrics-grid">
              <div className="customer-profile-stat-box">
                <p>Transactions</p>
                <p className="customer-profile-stat-value">{customer.transactions}</p>
              </div>

              <div className="customer-profile-stat-box">
                <p>Total Spend</p>
                <p className="customer-profile-stat-value">{formatCurrency(customer.spend)}</p>
              </div>

              <div className="customer-profile-stat-box">
                <p>Engagement</p>
                <p className="customer-profile-stat-value">{customer.engagement}%</p>
              </div>

              <div className="customer-profile-stat-box">
                <p>Risk Score</p>
                <p className="customer-profile-stat-value">{customer.riskScore}</p>
              </div>
            </div>
          </section>

          <section className="customer-profile-section">
            <div className="customer-profile-section-header left-aligned">
              <Wallet size={18} />
              <h3>Financial Footprint</h3>
            </div>

            <div className="customer-profile-financial-box">
              <div className="customer-profile-financial-item">
                <p>Total Transaction Value</p>
                <p className="customer-profile-stat-value">{formatCurrency(customer.spend)}</p>
              </div>

              <div className="customer-profile-financial-item">
                <p>Average Transaction</p>
                <p className="customer-profile-stat-value">{formatCurrency(customer.avgTransaction)}</p>
              </div>
            </div>
          </section>

          <section className="customer-profile-section">
            <div className="customer-profile-section-header left-aligned">
              <Activity size={18} />
              <h3>Behavioral Signals</h3>
            </div>

            <div className="customer-profile-signal-list">
              {customer.behavior.map((item) => (
                <div key={item} className="customer-profile-signal-item">
                  <div className="customer-profile-signal-icon">
                    <TrendingUp size={15} />
                  </div>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="customer-profile-section">
            <div className="customer-profile-section-header left-aligned">
              <CreditCard size={18} />
              <h3>Category Affinity</h3>
            </div>

            <div className="customer-profile-tag-list">
              {customer.categories.map((category) => (
                <span key={category} className="customer-profile-tag">
                  {category}
                </span>
              ))}
            </div>
          </section>

          <section className="customer-profile-section">
            <div className="customer-profile-section-header left-aligned">
              <MessageSquare size={18} />
              <h3>Communication Intelligence</h3>
            </div>

            <div className="customer-profile-two-col-grid">
              <div className="customer-profile-small-card">
                <p>Messages Processed</p>
                <p className="customer-profile-stat-value">{customer.messages}</p>
              </div>

              <div className="customer-profile-small-card">
                <p>Last Activity</p>
                <p className="customer-profile-stat-value">{customer.lastActivity}</p>
              </div>
            </div>
          </section>

          <section className="customer-profile-section">
            <div className="customer-profile-section-header left-aligned">
              <Calendar size={18} />
              <h3>Profile Metadata</h3>
            </div>

            <div className="customer-profile-metadata-box">
              <div className="customer-profile-metadata-row">
                <span>Customer ID</span>
                <strong>{customer.id}</strong>
              </div>

              <div className="customer-profile-metadata-row">
                <span>Active Since</span>
                <strong>{customer.activeSince}</strong>
              </div>

              <div className="customer-profile-metadata-row">
                <span>Profile Confidence</span>
                <strong className="customer-profile-confidence">94%</strong>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default function CustomerProfiles({
  onNavigate,
  onOpenMobileSidebar,
}) {
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('All Segments');
  const [industry, setIndustry] = useState('All Industries');
  const [risk, setRisk] = useState('All Risk Levels');
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  const filteredCustomers = useMemo(() => {
    return customers.filter((customer) => {
      const matchesSearch =
        customer.name.toLowerCase().includes(search.toLowerCase()) ||
        customer.id.toLowerCase().includes(search.toLowerCase()) ||
        customer.location.toLowerCase().includes(search.toLowerCase());

      const matchesSegment =
        segment === 'All Segments' || customer.segment === segment;

      const matchesIndustry =
        industry === 'All Industries' || customer.industry === industry;

      const matchesRisk = risk === 'All Risk Levels' || customer.risk === risk;

      return (
        matchesSearch &&
        matchesSegment &&
        matchesIndustry &&
        matchesRisk
      );
    });
  }, [search, segment, industry, risk]);

  return (
    <>
      <TopBar
        crumbs={[
          { label: 'Customer Intelligence Platform' },
          { label: 'Customer Profiles' },
        ]}
        status="active"
        statusLabel="System Online"
        onOpenMobileSidebar={onOpenMobileSidebar}
      />

      <main className="customer-profile-page">
        {/* Page Header */}
        <div className="customer-profile-header">
          <div>
            <h1 className="customer-profile-title">
              Customer Profiles
            </h1>

            <p className="customer-profile-subtitle">
              Explore unified customer profiles, behavioral signals,
              financial footprints and intelligence across connected data
              sources.
            </p>
          </div>

          <button className="customer-export-button">
            <Users size={17} />
            Export Profiles
          </button>
        </div>

        {/* KPI Cards */}
        <div className="customer-stat-grid">
          <StatCard
            icon={Users}
            label="Total Customers"
            value="12,482"
            description="Across connected data sources"
          />

          <StatCard
            icon={UserCheck}
            label="Active Customers"
            value="8,941"
            description="Active in the last 30 days"
          />

          <StatCard
            icon={Wallet}
            label="High Value"
            value="1,286"
            description="High-value customer profiles"
          />

          <StatCard
            icon={ShieldAlert}
            label="At Risk"
            value="734"
            description="Requires attention"
          />
        </div>

        {/* Filters */}
        <div className="customer-filters-panel">
          <div className="customer-filter-row">
            {/* Search */}
            <div className="customer-search-box">
              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search customer ID, name or location..."
                className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
              />
            </div>

            <div className="customer-filter-controls">
              {/* Segment */}
              <div className="relative">
                <select
                  value={segment}
                  onChange={(e) => setSegment(e.target.value)}
                  className="appearance-none rounded-lg border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm text-slate-700 outline-none"
                >
                  <option>All Segments</option>
                  <option>High Value</option>
                  <option>Premium</option>
                  <option>Regular</option>
                  <option>At Risk</option>
                </select>

                <ChevronDown
                  size={15}
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
              </div>

              {/* Industry */}
              <div className="relative">
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="appearance-none rounded-lg border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm text-slate-700 outline-none"
                >
                  <option>All Industries</option>
                  <option>Banking</option>
                  <option>E-Commerce</option>
                  <option>Utilities</option>
                  <option>Travel</option>
                  <option>Telecom</option>
                </select>

                <ChevronDown
                  size={15}
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
              </div>

              {/* Risk */}
              <div className="relative">
                <select
                  value={risk}
                  onChange={(e) => setRisk(e.target.value)}
                  className="appearance-none rounded-lg border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm text-slate-700 outline-none"
                >
                  <option>All Risk Levels</option>
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>

                <ChevronDown
                  size={15}
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
              </div>

              <button
                onClick={() => {
                  setSearch('');
                  setSegment('All Segments');
                  setIndustry('All Industries');
                  setRisk('All Risk Levels');
                }}
                className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
              >
                <Filter size={16} />
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Customer Table */}
        <div className="customer-directory-panel">
          <div className="customer-directory-header">
            <div>
              <h2 className="customer-directory-title">
                Customer Directory
              </h2>

              <p className="customer-directory-meta">
                {filteredCustomers.length} profiles displayed
              </p>
            </div>

            <button className="customer-directory-sort">
              Sort by Activity
              <ChevronDown size={15} />
            </button>
          </div>

          <div className="customer-table-wrapper">
            <table className="customer-profile-table">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Customer
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Segment
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Industry
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Transactions
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Total Spend
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Last Activity
                  </th>

                  <th className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Risk
                  </th>

                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {filteredCustomers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
                          {customer.initials}
                        </div>

                        <div>
                          <p className="text-sm font-semibold text-slate-900">
                            {customer.name}
                          </p>

                          <p className="mt-0.5 text-xs text-slate-500">
                            {customer.id} · {customer.location}
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      <SegmentBadge segment={customer.segment} />
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-600">
                      {customer.industry}
                    </td>

                    <td className="px-5 py-4 text-sm font-medium text-slate-800">
                      {customer.transactions}
                    </td>

                    <td className="px-5 py-4 text-sm font-medium text-slate-800">
                      {formatCurrency(customer.spend)}
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-500">
                      {customer.lastActivity}
                    </td>

                    <td className="px-5 py-4">
                      <RiskBadge risk={customer.risk} />
                    </td>

                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => onNavigate('customer-profile', customer.id)}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      >
                        View Profile
                        <ArrowUpRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}

                {filteredCustomers.length === 0 && (
                  <tr>
                    <td colSpan="8" className="px-5 py-12 text-center">
                      <Users
                        size={30}
                        className="mx-auto text-slate-300"
                      />

                      <p className="mt-3 text-sm font-medium text-slate-700">
                        No customers found
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        Try changing your search or filters.
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      <style>{`
        .customer-profile-page {
          min-height: 100vh;
          background:
            radial-gradient(circle at top left, rgba(99, 102, 241, 0.10), transparent 30%),
            linear-gradient(180deg, #0b1120 0%, #0f172a 100%);
          padding: 20px 18px 32px;
          color: #e2e8f0;
        }

        .customer-profile-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 24px;
          padding: 6px 2px;
        }

        .customer-profile-title {
          margin: 0;
          font-size: clamp(2rem, 2vw + 1rem, 2.5rem);
          line-height: 1.15;
          letter-spacing: -0.03em;
          font-weight: 800;
          color: #f8fafc;
        }

        .customer-profile-subtitle {
          margin-top: 8px;
          max-width: 700px;
          font-size: 13px;
          line-height: 1.6;
          color: #94a3b8;
        }

        .customer-export-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          background: linear-gradient(135deg, #1f2937 0%, #0f172a 100%);
          color: #f8fafc;
          border: 1px solid rgba(148, 163, 184, 0.24);
          padding: 11px 16px;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 10px 25px rgba(15, 23, 42, 0.25);
        }

        .customer-export-button:hover {
          transform: translateY(-1px);
          border-color: rgba(129, 140, 248, 0.4);
          box-shadow: 0 16px 35px rgba(99, 102, 241, 0.2);
        }

        .customer-stat-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 16px;
          margin-bottom: 22px;
        }

        .customer-filters-panel {
          background: rgba(15, 23, 42, 0.88);
          border: 1px solid rgba(148, 163, 184, 0.16);
          border-radius: 18px;
          padding: 18px;
          margin-bottom: 18px;
          box-shadow: 0 12px 30px rgba(2, 6, 23, 0.2);
        }

        .customer-filter-row {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .customer-search-box {
          position: relative;
          flex: 1;
        }

        .customer-search-box input {
          width: 100%;
          background: rgba(15, 23, 42, 0.7);
          border: 1px solid rgba(148, 163, 184, 0.18);
          color: #e2e8f0;
          border-radius: 12px;
          padding: 12px 14px 12px 42px;
          font-size: 13px;
          outline: none;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .customer-search-box input:focus {
          border-color: rgba(129, 140, 248, 0.7);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
        }

        .customer-search-box svg {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: #94a3b8;
        }

        .customer-filter-controls {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 12px;
        }

        .customer-filter-controls select,
        .customer-filter-controls button {
          height: 42px;
          border-radius: 12px;
          border: 1px solid rgba(148, 163, 184, 0.18);
          background: rgba(15, 23, 42, 0.7);
          color: #e2e8f0;
          font-size: 13px;
        }

        .customer-filter-controls select {
          appearance: none;
          padding: 0 32px 0 12px;
        }

        .customer-filter-controls button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 0 14px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .customer-filter-controls button:hover {
          border-color: rgba(148, 163, 184, 0.28);
          background: rgba(30, 41, 59, 0.9);
        }

        .customer-directory-panel {
          overflow: hidden;
          border-radius: 18px;
          background: rgba(15, 23, 42, 0.88);
          border: 1px solid rgba(148, 163, 184, 0.16);
          box-shadow: 0 12px 30px rgba(2, 6, 23, 0.2);
        }

        .customer-directory-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 18px 20px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(15, 23, 42, 0.7);
        }

        .customer-directory-title {
          margin: 0;
          font-size: 16px;
          font-weight: 700;
          color: #f8fafc;
        }

        .customer-directory-meta {
          margin-top: 4px;
          font-size: 12px;
          color: #94a3b8;
        }

        .customer-directory-sort {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(30, 41, 59, 0.7);
          color: #e2e8f0;
          padding: 8px 12px;
          border-radius: 10px;
          font-size: 12px;
          cursor: pointer;
        }

        .customer-table-wrapper {
          overflow-x: auto;
        }

        .customer-profile-table {
          width: 100%;
          min-width: 1000px;
          border-collapse: collapse;
          color: #e2e8f0;
        }

        .customer-profile-table thead {
          background: rgba(15, 23, 42, 0.9);
        }

        .customer-profile-table th,
        .customer-profile-table td {
          padding: 16px 20px;
          text-align: left;
          border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }

        .customer-profile-table th {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #94a3b8;
        }

        .customer-profile-table tbody tr {
          transition: background 0.2s ease;
        }

        .customer-profile-table tbody tr:hover {
          background: rgba(15, 23, 42, 0.55);
        }

        .customer-profile-table tbody td {
          font-size: 13px;
          color: #cbd5e1;
        }

        .customer-profile-overlay {
          position: fixed;
          inset: 0;
          z-index: 50;
          display: flex;
          justify-content: flex-end;
          background: rgba(2, 6, 23, 0.55);
        }

        .customer-profile-drawer {
          width: min(100%, 720px);
          height: 100%;
          overflow-y: auto;
          background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
          border-left: 1px solid rgba(148, 163, 184, 0.15);
          box-shadow: -24px 0 50px rgba(2, 6, 23, 0.45);
        }

        .customer-profile-drawer-header {
          position: sticky;
          top: 0;
          z-index: 10;
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          padding: 22px 24px 18px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(15, 23, 42, 0.95);
          backdrop-filter: blur(10px);
        }

        .customer-profile-drawer-profile {
          display: flex;
          align-items: flex-start;
          gap: 16px;
        }

        .customer-profile-drawer-avatar {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          color: #f8fafc;
          font-size: 18px;
          font-weight: 700;
          border: 1px solid rgba(148, 163, 184, 0.16);
        }

        .customer-profile-drawer-title-row {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }

        .customer-profile-drawer-name {
          margin: 0;
          font-size: 1.4rem;
          font-weight: 800;
          color: #f8fafc;
        }

        .customer-profile-drawer-meta {
          margin-top: 4px;
          font-size: 13px;
          color: #cbd5e1;
        }

        .customer-profile-drawer-location {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-top: 8px;
          font-size: 12px;
          color: #94a3b8;
        }

        .customer-profile-close-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border-radius: 10px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(15, 23, 42, 0.7);
          color: #cbd5e1;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .customer-profile-close-btn:hover {
          background: rgba(30, 41, 59, 0.9);
          color: #f8fafc;
        }

        .customer-profile-drawer-body {
          display: flex;
          flex-direction: column;
          gap: 20px;
          padding: 22px 24px 30px;
        }

        .customer-profile-section {
          background: rgba(15, 23, 42, 0.7);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 16px;
          padding: 18px;
        }

        .customer-profile-section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 14px;
          color: #f8fafc;
        }

        .customer-profile-section-header.left-aligned {
          justify-content: flex-start;
        }

        .customer-profile-section-header h3 {
          margin: 0;
          font-size: 15px;
          font-weight: 700;
        }

        .customer-profile-metrics-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }

        .customer-profile-stat-box,
        .customer-profile-small-card,
        .customer-profile-financial-item {
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          padding: 14px;
        }

        .customer-profile-stat-box p,
        .customer-profile-small-card p,
        .customer-profile-financial-item p {
          margin: 0;
          color: #94a3b8;
          font-size: 11px;
        }

        .customer-profile-stat-value {
          margin-top: 8px;
          color: #f8fafc;
          font-size: 1.05rem;
          font-weight: 700;
          line-height: 1.3;
        }

        .customer-profile-financial-box {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 0;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          overflow: hidden;
        }

        .customer-profile-financial-item + .customer-profile-financial-item {
          border-left: 1px solid rgba(148, 163, 184, 0.12);
        }

        .customer-profile-signal-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .customer-profile-signal-item {
          display: flex;
          align-items: center;
          gap: 12px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          padding: 12px 14px;
          background: rgba(15, 23, 42, 0.9);
          color: #cbd5e1;
          font-size: 13px;
        }

        .customer-profile-signal-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          border-radius: 8px;
          background: rgba(99, 102, 241, 0.12);
          color: #a5b4fc;
        }

        .customer-profile-tag-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .customer-profile-tag {
          display: inline-flex;
          border-radius: 999px;
          padding: 8px 12px;
          background: rgba(99, 102, 241, 0.12);
          border: 1px solid rgba(129, 140, 248, 0.28);
          color: #c7d2fe;
          font-size: 12px;
          font-weight: 600;
        }

        .customer-profile-two-col-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }

        .customer-profile-metadata-box {
          display: flex;
          flex-direction: column;
          gap: 12px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          background: rgba(15, 23, 42, 0.9);
          padding: 14px;
        }

        .customer-profile-metadata-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          font-size: 13px;
          color: #cbd5e1;
        }

        .customer-profile-confidence {
          color: #34d399;
        }

        @media (max-width: 980px) {
          .customer-stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .customer-profile-header {
            flex-direction: column;
            align-items: flex-start;
          }
        }

        @media (max-width: 640px) {
          .customer-profile-page {
            padding: 16px 12px 28px;
          }

          .customer-stat-grid,
          .customer-profile-metrics-grid,
          .customer-profile-two-col-grid,
          .customer-profile-financial-box {
            grid-template-columns: 1fr;
          }

          .customer-filter-controls {
            display: grid;
            grid-template-columns: 1fr;
          }

          .customer-directory-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .customer-profile-drawer {
            width: 100%;
          }
        }
      `}</style>
    </>
  );
}