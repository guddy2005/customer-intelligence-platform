import React, { useState } from 'react';
import { Play, Loader } from 'lucide-react';
import UploadZone from './UploadZone';

/* Data type options per source category */
const DATA_TYPE_MAP = {
  banking:      ['Bank Transactions', 'Account Statements', 'Loan Records', 'Credit Card History'],
  investments:  ['SIP Transactions', 'Stock Trades', 'Mutual Fund Portfolio', 'Digital Gold', 'Bonds'],
  ecommerce:    ['Orders', 'Returns & Refunds', 'Wishlist Activity', 'Product Reviews', 'Cart Abandonment'],
  food_delivery:['Food Orders', 'Restaurant Reviews', 'Subscription Plans', 'Offer Redemptions'],
  travel:       ['Flight Bookings', 'Hotel Reservations', 'Cab Rides', 'Bus Tickets', 'Holiday Packages'],
  automobile:   ['Vehicle Purchase', 'Service Records', 'Fuel Transactions', 'Insurance Renewals'],
  real_estate:  ['Property Transactions', 'Rental Payments', 'Home Loans', 'Society Maintenance'],
  utilities:    ['Electricity Bills', 'Water Bills', 'Gas Bills', 'Broadband Payments', 'Mobile Recharge'],
  healthcare:   ['Doctor Visits', 'Lab Reports', 'Pharmacy Orders', 'Health Insurance Claims'],
  education:    ['Course Enrollments', 'Fee Payments', 'Online Learning', 'Exam Registrations'],
  retail:       ['In-Store Purchases', 'Loyalty Points', 'Fashion & Apparel', 'Subscription Boxes'],
  insurance:    ['Policy Purchases', 'Premium Payments', 'Claims Filed', 'Policy Renewals'],
  _default:     ['Select a source category first'],
};

const SOURCE_OPTIONS = [
  { value: '',             label: 'Select Source Category' },
  { value: 'banking',      label: 'Banking' },
  { value: 'investments',  label: 'Investments' },
  { value: 'ecommerce',    label: 'E-Commerce' },
  { value: 'food_delivery',label: 'Food Delivery' },
  { value: 'travel',       label: 'Travel' },
  { value: 'automobile',   label: 'Automobile' },
  { value: 'real_estate',  label: 'Real Estate' },
  { value: 'utilities',    label: 'Utilities' },
  { value: 'healthcare',   label: 'Healthcare' },
  { value: 'education',    label: 'Education' },
  { value: 'retail',       label: 'Retail & Lifestyle' },
  { value: 'insurance',    label: 'Insurance' },
];

/**
 * ImportPanel — source/type selectors + UploadZone + process button.
 *
 * Props:
 *   selectedSource — source key pre-selected from DataSourceGrid (or null)
 *   isLoading      — boolean
 *   onProcess      — callback({ source, dataType, file })
 */
export default function ImportPanel({ selectedSource, isLoading, onProcess }) {
  const [source, setSource] = useState(selectedSource || '');
  const [dataType, setDataType] = useState('');
  const [file, setFile] = useState(null);

  // Sync when parent grid selection changes
  React.useEffect(() => {
    if (selectedSource !== undefined) {
      setSource(selectedSource || '');
      setDataType('');
    }
  }, [selectedSource]);

  const dataTypes = DATA_TYPE_MAP[source] || DATA_TYPE_MAP['_default'];
  const canProcess = source && dataType && file;

  const handleProcess = () => {
    if (!canProcess) return;
    onProcess({ source, dataType, file });
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon" style={{ background: 'var(--primary-dim)', color: 'var(--primary-light)' }}>
            <Play size={15} />
          </div>
          Import Data
        </div>
      </div>

      {/* Selectors */}
      <div className="import-grid">
        <div className="form-group">
          <label className="form-label" htmlFor="source-select">Source Category</label>
          <select
            id="source-select"
            className="select-control"
            value={source}
            onChange={(e) => { setSource(e.target.value); setDataType(''); }}
          >
            {SOURCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="datatype-select">Data Type</label>
          <select
            id="datatype-select"
            className="select-control"
            value={dataType}
            onChange={(e) => setDataType(e.target.value)}
            disabled={!source}
          >
            <option value="">Select Data Type</option>
            {dataTypes.map((dt) => (
              <option key={dt} value={dt}>{dt}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Upload Zone */}
      <UploadZone file={file} onFileChange={setFile} />

      {/* Process Button */}
      <div className="mt-4">
        <button
          id="process-btn"
          className="btn btn-primary btn-lg btn-full"
          disabled={!canProcess || isLoading}
          onClick={handleProcess}
        >
          {isLoading ? (
            <>
              <div className="spinner" />
              Processing Pipeline...
            </>
          ) : (
            <>
              <Play size={16} />
              Process & Ingest Dataset
            </>
          )}
        </button>
      </div>
    </div>
  );
}
