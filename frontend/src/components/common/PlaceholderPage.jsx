import React from 'react';
import { Construction } from 'lucide-react';

/**
 * PlaceholderPage — renders a polished "Coming Soon" page for stub nav sections.
 *
 * Props:
 *   icon     — Lucide icon component
 *   title    — page title string
 *   description — short description string
 *   features — array of feature label strings to preview
 */
export default function PlaceholderPage({ icon: Icon, title, description, features = [] }) {
  return (
    <div className="page-content">
      <div className="placeholder-page">
        <div className="placeholder-icon-wrap">
          {Icon ? <Icon size={36} /> : <Construction size={36} />}
        </div>

        <div className="coming-soon-chip">
          <Construction size={13} />
          Coming Soon
        </div>

        <h2>{title}</h2>

        <p>{description}</p>

        {features.length > 0 && (
          <div className="placeholder-features">
            {features.map((feat, i) => (
              <span key={i} className="placeholder-feature-tag">
                {feat}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
