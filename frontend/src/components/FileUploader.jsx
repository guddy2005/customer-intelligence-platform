import React, { useState } from 'react';
import { UploadCloud, FileText, Play, CheckCircle2, AlertCircle } from 'lucide-react';

export default function FileUploader({ onUpload, isLoading, onPresetSelect }) {
  const [file, setFile] = useState(null);
  const [domainHint, setDomainHint] = useState('AUTO_DETECT');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
      } else {
        alert('Please drop a valid .csv file');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) return;
    onUpload(file, domainHint);
  };

  const presets = [
    { label: 'Banking Statements', domain: 'BANKING', filename: 'banking_transactions.csv' },
    { label: 'E-Commerce Orders', domain: 'E_COMMERCE', filename: 'ecommerce_orders.csv' },
    { label: 'Food Delivery Orders', domain: 'FOOD_DELIVERY', filename: 'food_delivery_orders.csv' },
    { label: 'Investment Portfolio', domain: 'INVESTMENT', filename: 'investment_transactions.csv' },
    { label: 'Utility Payments', domain: 'UTILITIES', filename: 'utility_payments.csv' },
    { label: 'Customer Profiles', domain: 'CUSTOMER', filename: 'customers.csv' },
  ];

  return (
    <div className="glass-panel">
      <form onSubmit={handleSubmit}>
        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('csv-file-input').click()}
        >
          <input
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <div className="dropzone-icon">
            <UploadCloud size={32} />
          </div>

          {file ? (
            <div>
              <p style={{ fontWeight: 700, fontSize: 16, color: '#38bdf8' }}>{file.name}</p>
              <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
                {(file.size / 1024).toFixed(2)} KB • Ready to process
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontWeight: 700, fontSize: 16 }}>
                Drag & drop your dataset CSV here, or <span style={{ color: '#6366f1' }}>Browse Files</span>
              </p>
              <p style={{ fontSize: 13, color: '#64748b', marginTop: 6 }}>
                Supports Banking, E-Commerce, Food Delivery, Investments, Utilities & Customer records
              </p>
            </div>
          )}
        </div>

        <div className="controls-row">
          <select
            className="select-control"
            value={domainHint}
            onChange={(e) => setDomainHint(e.target.value)}
          >
            <option value="AUTO_DETECT">✨ Auto-Detect Source Domain</option>
            <option value="BANKING">🏦 Banking Transactions</option>
            <option value="E_COMMERCE">🛍️ E-Commerce Orders</option>
            <option value="FOOD_DELIVERY">🍕 Food Delivery Orders</option>
            <option value="INVESTMENT">📈 Investment & Stocks</option>
            <option value="UTILITIES">⚡ Utility Bills</option>
            <option value="CUSTOMER">👤 Customer Master Profiles</option>
          </select>

          <button
            type="submit"
            className="btn-primary"
            disabled={!file || isLoading}
          >
            {isLoading ? (
              <>Processing Pipeline...</>
            ) : (
              <>
                <Play size={16} /> Process & Ingest Dataset
              </>
            )}
          </button>
        </div>
      </form>

      <div className="presets-group">
        <div className="presets-title">Quick Test Presets (Mock Datasets):</div>
        <div className="preset-pills">
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className="btn-pill"
              onClick={() => onPresetSelect(p.filename, p.domain)}
            >
              <FileText size={14} /> {p.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
