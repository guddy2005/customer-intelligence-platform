import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X } from 'lucide-react';

/**
 * UploadZone — drag-and-drop file upload area.
 * This is a UI/testing mechanism only. The underlying data ingestion
 * architecture is not tied to CSV as a production source.
 *
 * Props:
 *   file       — currently selected File object (or null)
 *   onFileChange — callback(File | null)
 *   accept     — accepted MIME types string (default: any)
 */
export default function UploadZone({ file, onFileChange, accept }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

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
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFileChange(dropped);
  };

  const handleInputChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) onFileChange(selected);
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    onFileChange(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const openPicker = () => inputRef.current?.click();

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div>
      <div
        className={`upload-zone${dragActive ? ' drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={openPicker}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && openPicker()}
        aria-label="Upload file"
      >
        <input
          ref={inputRef}
          id="upload-zone-input"
          type="file"
          accept={accept}
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        <div className="upload-zone-icon">
          <UploadCloud size={26} />
        </div>

        <div className="upload-zone-title">
          Drag & drop your dataset here
        </div>
        <div className="upload-zone-sub">
          or <span>browse files</span> to select — CSV, JSON, XML, XLSX, Parquet supported
        </div>
      </div>

      {/* File selected indicator */}
      {file && (
        <div className="file-selected" onClick={(e) => e.stopPropagation()}>
          <div className="file-icon-box">
            <FileText size={18} />
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div className="file-info-name">{file.name}</div>
            <div className="file-info-meta">
              {formatSize(file.size)} &bull; Ready to process
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleRemove}
            title="Remove file"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* UI-only note */}
      <div className="upload-note">
        <span style={{ fontSize: 15 }}>ℹ️</span>
        <span>
          File upload is a UI testing mechanism. Production ingestion will support
          streaming APIs, message queues, database connectors and more.
        </span>
      </div>
    </div>
  );
}
