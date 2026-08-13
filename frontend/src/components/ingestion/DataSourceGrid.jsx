import React from 'react';
import {
  Landmark,
  TrendingUp,
  ShoppingBag,
  UtensilsCrossed,
  Plane,
  Car,
  Home,
  Zap,
  Stethoscope,
  GraduationCap,
  ShoppingCart,
  Shield,
} from 'lucide-react';

const DATA_SOURCES = [
  {
    key: 'banking',
    label: 'Banking',
    icon: Landmark,
    iconClass: 'source-icon-banking',
  },
  {
    key: 'investments',
    label: 'Investments',
    icon: TrendingUp,
    iconClass: 'source-icon-investment',
  },
  {
    key: 'ecommerce',
    label: 'E-Commerce',
    icon: ShoppingBag,
    iconClass: 'source-icon-ecommerce',
  },
  {
    key: 'food_delivery',
    label: 'Food Delivery',
    icon: UtensilsCrossed,
    iconClass: 'source-icon-food',
  },
  {
    key: 'travel',
    label: 'Travel',
    icon: Plane,
    iconClass: 'source-icon-travel',
  },
  {
    key: 'automobile',
    label: 'Automobile',
    icon: Car,
    iconClass: 'source-icon-auto',
  },
  {
    key: 'real_estate',
    label: 'Real Estate',
    icon: Home,
    iconClass: 'source-icon-realestate',
  },
  {
    key: 'utilities',
    label: 'Utilities',
    icon: Zap,
    iconClass: 'source-icon-utilities',
  },
  {
    key: 'healthcare',
    label: 'Healthcare',
    icon: Stethoscope,
    iconClass: 'source-icon-health',
  },
  {
    key: 'education',
    label: 'Education',
    icon: GraduationCap,
    iconClass: 'source-icon-education',
  },
  {
    key: 'retail',
    label: 'Retail & Lifestyle',
    icon: ShoppingCart,
    iconClass: 'source-icon-retail',
  },
  {
    key: 'insurance',
    label: 'Insurance',
    icon: Shield,
    iconClass: 'source-icon-insurance',
  },
];

/**
 * DataSourceGrid — 12-category grid of clickable data source cards.
 *
 * Props:
 *   selectedSource — currently selected source key (string)
 *   onSelect       — callback(sourceKey: string)
 */
export default function DataSourceGrid({ selectedSource, onSelect }) {
  return (
    <div className="section">
      <div className="section-header">
        <div className="section-title" style={{ fontSize: 13.5 }}>
          Data Source Categories
        </div>
        <span className="section-count">{DATA_SOURCES.length} sources available</span>
      </div>

      <div className="source-grid">
        {DATA_SOURCES.map(({ key, label, icon: Icon, iconClass }) => (
          <div
            key={key}
            className={`source-card${selectedSource === key ? ' selected' : ''}`}
            onClick={() => onSelect(key === selectedSource ? null : key)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelect(key === selectedSource ? null : key)}
          >
            <div className={`source-card-icon ${iconClass}`}>
              <Icon size={20} />
            </div>
            <span className="source-card-label">{label}</span>
            <span className="source-card-badge">Active</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export { DATA_SOURCES };
