import React, { useState } from 'react';
import { FileUp, FileText, CheckCircle2, ShieldAlert, Search, RefreshCw } from 'lucide-react';
import { API_BASE } from '../utils/apiConfig';

export const AttachmentScanner = ({ profile }) => {
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setScanning(true);
    setScanResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/scan-custom-file`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setScanResult(data);
    } catch (err) {
      console.error('Scan error:', err);
      alert('Error scanning file. Ensure backend is running.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {}
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800 }}>Document & PDF Deep-Scanner</h2>
          <span style={{
            background: 'var(--accent-emerald-light)',
            color: 'var(--accent-emerald)',
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '6px'
          }}>
            Multi-Page Table OCR & PDF Parser
          </span>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Instantly scan any placement PDF, shortlisted candidate list, or Excel sheet for your credentials: 
          <strong> {profile?.roll_number || '23BAI11174'}</strong>, 
          <strong> {profile?.name || 'Shashwat Pratap Singh'}</strong>, or 
          <strong> NeoPAT ID: {profile?.neopat_id || 'S4Z5F7U9'}</strong>.
        </p>
      </div>

      {}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        style={{
          background: dragOver ? 'var(--accent-emerald-light)' : 'var(--bg-secondary)',
          border: `2px dashed ${dragOver ? 'var(--accent-emerald)' : 'var(--border-medium)'}`,
          borderRadius: 'var(--radius-xl)',
          padding: '3rem 2rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
        onClick={() => document.getElementById('file-upload-input').click()}
      >
        <input
          id="file-upload-input"
          type="file"
          accept=".pdf,.xlsx,.xls,.docx,.txt"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--accent-emerald-light)',
          color: 'var(--accent-emerald)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1rem auto'
        }}>
          {scanning ? <RefreshCw className="animate-spin" size={28} /> : <FileUp size={28} />}
        </div>

        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
          {scanning ? 'Parsing and scanning pages...' : 'Upload PDF / Excel Document to Scan'}
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto' }}>
          Drop candidate shortlist PDFs, interview schedules, or circular sheets here (Supports 100+ pages).
        </p>
      </div>

      {}
      {scanResult && (
        <div className="light-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.75rem' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Scan Report: {scanResult.filename}</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Total Pages / Sheets Analyzed: {scanResult.total_pages}
              </span>
            </div>

            <div>
              {scanResult.matches_found > 0 ? (
                <span className="badge-critical" style={{ fontSize: '0.85rem', padding: '0.35rem 0.85rem' }}>
                  <ShieldAlert size={16} /> {scanResult.matches_found} Direct Matches Found!
                </span>
              ) : (
                <span className="badge-silent" style={{ fontSize: '0.85rem', padding: '0.35rem 0.85rem' }}>
                  <CheckCircle2 size={16} /> 0 Matches Found (Clean)
                </span>
              )}
            </div>
          </div>

          {scanResult.matches_found > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                Matched Locations in Document:
              </h4>
              {scanResult.matches.map((match, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--accent-ruby-light)',
                    border: '1px solid var(--accent-ruby-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.3rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-ruby)' }}>
                    <span>🎯 Matched Target: "{match.term}"</span>
                    <span>{match.page ? `Page ${match.page}` : match.sheet ? `Sheet: ${match.sheet}, Row: ${match.row}` : 'Line hit'}</span>
                  </div>
                  <div style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '0.82rem',
                    background: 'white',
                    padding: '0.45rem 0.65rem',
                    borderRadius: '6px',
                    border: '1px solid var(--accent-ruby-border)',
                    color: 'var(--text-primary)'
                  }}>
                    {match.snippet}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ background: 'var(--bg-tertiary)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              None of your configured identifiers ({profile?.roll_number}, {profile?.name}, {profile?.neopat_id}) appeared in this document.
            </div>
          )}

          {}
          {scanResult.preview && (
            <div style={{ marginTop: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Extracted Text Preview:
              </div>
              <pre style={{
                background: 'var(--bg-tertiary)',
                padding: '0.85rem',
                borderRadius: '8px',
                fontSize: '0.78rem',
                maxHeight: '180px',
                overflowY: 'auto',
                color: 'var(--text-secondary)'
              }}>
                {scanResult.preview}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
