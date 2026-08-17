import React from 'react';
import {
  ArrowLeft,
  MapPin,
  Wallet,
  Activity,
  CreditCard,
  MessageSquare,
  TrendingUp,
  Calendar,
  ShieldAlert,
  Users,
} from 'lucide-react';

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

const formatCurrency = (value) => `₹${value.toLocaleString('en-IN')}`;

function RiskBadge({ risk }) {
  const styles = {
    Low: 'risk-low',
    Medium: 'risk-medium',
    High: 'risk-high',
  };

  return <span className={`customer-risk-badge ${styles[risk] || 'risk-low'}`}>{risk}</span>;
}

function SegmentBadge({ segment }) {
  const styles = {
    'High Value': 'segment-high-value',
    Premium: 'segment-premium',
    Regular: 'segment-regular',
    'At Risk': 'segment-at-risk',
  };

  return <span className={`customer-segment-badge ${styles[segment] || 'segment-regular'}`}>{segment}</span>;
}

export default function CustomerProfileDetail({ onNavigate, selectedCustomerId }) {
  const customer = customers.find((item) => item.id === selectedCustomerId) || customers[0];

  return (
    <>
      <main className="customer-detail-page">
        <div className="customer-detail-header">
          <button className="customer-back-button" onClick={() => onNavigate('customers')}>
            <ArrowLeft size={16} />
            Back to profiles
          </button>
        </div>

        <div className="customer-detail-hero">
          <div className="customer-detail-identity">
            <div className="customer-detail-avatar">{customer.initials}</div>
            <div>
              <div className="customer-detail-name-row">
                <h1>{customer.name}</h1>
                <RiskBadge risk={customer.risk} />
              </div>
              <p className="customer-detail-subtitle">{customer.id} · {customer.industry}</p>
              <div className="customer-detail-location">
                <MapPin size={14} />
                {customer.location}
              </div>
            </div>
          </div>

          <div className="customer-detail-quickmeta">
            <div>
              <span>Customer Type</span>
              <SegmentBadge segment={customer.segment} />
            </div>
            <div>
              <span>Risk Score</span>
              <strong>{customer.riskScore}</strong>
            </div>
          </div>
        </div>

        <div className="customer-detail-grid">
          <section className="customer-detail-card customer-profile-overview">
            <div className="customer-detail-card-header">
              <h3>Profile Overview</h3>
            </div>
            <div className="customer-detail-metrics">
              <div className="customer-detail-metric">
                <span>Transactions</span>
                <strong>{customer.transactions}</strong>
              </div>
              <div className="customer-detail-metric">
                <span>Total Spend</span>
                <strong>{formatCurrency(customer.spend)}</strong>
              </div>
              <div className="customer-detail-metric">
                <span>Engagement</span>
                <strong>{customer.engagement}%</strong>
              </div>
              <div className="customer-detail-metric">
                <span>Last Activity</span>
                <strong>{customer.lastActivity}</strong>
              </div>
            </div>
          </section>

          <section className="customer-detail-card">
            <div className="customer-detail-card-header left-icon">
              <Wallet size={18} />
              <h3>Financial Footprint</h3>
            </div>
            <div className="customer-detail-two-col">
              <div className="customer-detail-stat-box">
                <span>Total Transaction Value</span>
                <strong>{formatCurrency(customer.spend)}</strong>
              </div>
              <div className="customer-detail-stat-box">
                <span>Average Transaction</span>
                <strong>{formatCurrency(customer.avgTransaction)}</strong>
              </div>
            </div>
          </section>

          <section className="customer-detail-card">
            <div className="customer-detail-card-header left-icon">
              <Activity size={18} />
              <h3>Behavioral Signals</h3>
            </div>
            <div className="customer-detail-list">
              {customer.behavior.map((item) => (
                <div key={item} className="customer-detail-list-item">
                  <div className="customer-detail-icon-wrap"><TrendingUp size={15} /></div>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="customer-detail-card">
            <div className="customer-detail-card-header left-icon">
              <CreditCard size={18} />
              <h3>Category Affinity</h3>
            </div>
            <div className="customer-detail-tags">
              {customer.categories.map((category) => (
                <span key={category} className="customer-detail-tag">{category}</span>
              ))}
            </div>
          </section>

          <section className="customer-detail-card">
            <div className="customer-detail-card-header left-icon">
              <MessageSquare size={18} />
              <h3>Communication Intelligence</h3>
            </div>
            <div className="customer-detail-two-col">
              <div className="customer-detail-stat-box">
                <span>Messages Processed</span>
                <strong>{customer.messages}</strong>
              </div>
              <div className="customer-detail-stat-box">
                <span>Last Activity</span>
                <strong>{customer.lastActivity}</strong>
              </div>
            </div>
          </section>

          <section className="customer-detail-card">
            <div className="customer-detail-card-header left-icon">
              <Calendar size={18} />
              <h3>Profile Metadata</h3>
            </div>
            <div className="customer-detail-meta-list">
              <div className="customer-detail-meta-row">
                <span>Customer ID</span>
                <strong>{customer.id}</strong>
              </div>
              <div className="customer-detail-meta-row">
                <span>Active Since</span>
                <strong>{customer.activeSince}</strong>
              </div>
              <div className="customer-detail-meta-row">
                <span>Profile Confidence</span>
                <strong className="customer-detail-confidence">94%</strong>
              </div>
            </div>
          </section>

          <section className="customer-detail-card customer-detail-alert-box">
            <div className="customer-detail-card-header left-icon">
              <ShieldAlert size={18} />
              <h3>Risk Summary</h3>
            </div>
            <p>
              This customer shows {customer.risk.toLowerCase()} risk exposure with {customer.riskScore} risk score.
              Engagement remains {customer.engagement}% and recent activity indicates {customer.behavior[0].toLowerCase()}.
            </p>
          </section>
        </div>
      </main>

      <style>{`
        .customer-detail-page {
          min-height: 100vh;
          background:
            radial-gradient(circle at top left, rgba(99, 102, 241, 0.12), transparent 24%),
            linear-gradient(180deg, #0b1120 0%, #0f172a 100%);
          padding: 24px 18px 42px;
          color: #e2e8f0;
        }

        .customer-detail-header {
          max-width: 1200px;
          margin: 0 auto 16px;
        }

        .customer-back-button {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: rgba(15, 23, 42, 0.7);
          border: 1px solid rgba(148, 163, 184, 0.14);
          color: #e2e8f0;
          border-radius: 12px;
          padding: 10px 14px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
        }

        .customer-detail-hero {
          max-width: 1200px;
          margin: 0 auto 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 20px;
          padding: 22px 24px;
          box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
        }

        .customer-detail-identity {
          display: flex;
          align-items: center;
          gap: 18px;
        }

        .customer-detail-avatar {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          border: 1px solid rgba(148, 163, 184, 0.16);
          font-size: 18px;
          font-weight: 800;
          color: #f8fafc;
        }

        .customer-detail-name-row {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }

        .customer-detail-name-row h1 {
          margin: 0;
          font-size: clamp(1.8rem, 2vw, 2.3rem);
          font-weight: 800;
          color: #f8fafc;
        }

        .customer-detail-subtitle {
          margin-top: 6px;
          font-size: 13px;
          color: #cbd5e1;
        }

        .customer-detail-location {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-top: 8px;
          color: #94a3b8;
          font-size: 12px;
        }

        .customer-detail-quickmeta {
          display: flex;
          align-items: center;
          gap: 24px;
          flex-wrap: wrap;
        }

        .customer-detail-quickmeta > div {
          display: flex;
          flex-direction: column;
          gap: 8px;
          min-width: 130px;
        }

        .customer-detail-quickmeta span {
          color: #94a3b8;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .customer-detail-quickmeta strong {
          color: #f8fafc;
          font-size: 1.1rem;
        }

        .customer-detail-grid {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
        }

        .customer-detail-card {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 12px 30px rgba(2, 6, 23, 0.18);
        }

        .customer-profile-overview {
          grid-column: 1 / -1;
        }

        .customer-detail-card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .customer-detail-card-header h3 {
          margin: 0;
          font-size: 15px;
          font-weight: 700;
          color: #f8fafc;
        }

        .customer-detail-card-header.left-icon {
          justify-content: flex-start;
          gap: 10px;
          color: #cbd5e1;
        }

        .customer-detail-metrics {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 12px;
        }

        .customer-detail-metric,
        .customer-detail-stat-box {
          background: rgba(15, 23, 42, 0.92);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          padding: 14px;
        }

        .customer-detail-metric span,
        .customer-detail-stat-box span,
        .customer-detail-list-item span,
        .customer-detail-meta-row span {
          color: #94a3b8;
          font-size: 11px;
        }

        .customer-detail-metric strong,
        .customer-detail-stat-box strong,
        .customer-detail-meta-row strong {
          display: block;
          margin-top: 8px;
          color: #f8fafc;
          font-size: 1.05rem;
          font-weight: 700;
        }

        .customer-detail-two-col {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }

        .customer-detail-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .customer-detail-list-item {
          display: flex;
          align-items: center;
          gap: 12px;
          background: rgba(15, 23, 42, 0.92);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          padding: 12px 14px;
        }

        .customer-detail-icon-wrap {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          border-radius: 8px;
          background: rgba(99, 102, 241, 0.14);
          color: #a5b4fc;
        }

        .customer-detail-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .customer-detail-tag {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          padding: 7px 12px;
          background: rgba(99, 102, 241, 0.12);
          border: 1px solid rgba(129, 140, 248, 0.26);
          color: #c7d2fe;
          font-size: 12px;
          font-weight: 600;
        }

        .customer-detail-meta-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .customer-detail-meta-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 12px 14px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 12px;
          background: rgba(15, 23, 42, 0.92);
        }

        .customer-detail-confidence {
          color: #34d399;
        }

        .customer-detail-alert-box p {
          margin: 0;
          color: #cbd5e1;
          line-height: 1.7;
          font-size: 14px;
        }

        .customer-risk-badge,
        .customer-segment-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          padding: 6px 10px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.02em;
        }

        .risk-low {
          background: rgba(16, 185, 129, 0.12);
          color: #6ee7b7;
          border: 1px solid rgba(16, 185, 129, 0.22);
        }

        .risk-medium {
          background: rgba(245, 158, 11, 0.12);
          color: #fbbf24;
          border: 1px solid rgba(245, 158, 11, 0.22);
        }

        .risk-high {
          background: rgba(239, 68, 68, 0.12);
          color: #fca5a5;
          border: 1px solid rgba(239, 68, 68, 0.22);
        }

        .segment-high-value {
          background: rgba(168, 85, 247, 0.12);
          color: #d8b4fe;
          border: 1px solid rgba(168, 85, 247, 0.24);
        }

        .segment-premium {
          background: rgba(59, 130, 246, 0.12);
          color: #bfdbfe;
          border: 1px solid rgba(59, 130, 246, 0.24);
        }

        .segment-regular {
          background: rgba(148, 163, 184, 0.12);
          color: #e2e8f0;
          border: 1px solid rgba(148, 163, 184, 0.22);
        }

        .segment-at-risk {
          background: rgba(239, 68, 68, 0.12);
          color: #fca5a5;
          border: 1px solid rgba(239, 68, 68, 0.22);
        }

        @media (max-width: 900px) {
          .customer-detail-grid,
          .customer-detail-metrics,
          .customer-detail-two-col {
            grid-template-columns: 1fr;
          }

          .customer-detail-hero {
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>
    </>
  );
}
