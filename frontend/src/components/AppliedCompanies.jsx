import React, { useState } from 'react';
import { Building2, Plus, Trash2, CheckCircle2, AlertCircle, Clock, Send } from 'lucide-react';

export const AppliedCompanies = ({ companies, onAddCompany, onDeleteCompany, onRefresh }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCompany, setNewCompany] = useState({ company_name: '', role_title: 'Software Engineer Trainee', status: 'Applied', notes: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newCompany.company_name.trim()) return;
    onAddCompany(newCompany);
    setNewCompany({ company_name: '', role_title: 'Software Engineer Trainee', status: 'Applied', notes: '' });
    setShowAddForm(false);
  };

  const getStatusBadge = (status) => {
    const s = status?.toLowerCase() || '';
    if (s.includes('shortlist') || s.includes('interview')) {
      return (
        <span style={{
          background: 'var(--accent-emerald-light)',
          color: 'var(--accent-emerald)',
          border: '1px solid var(--accent-emerald-border)',
          padding: '0.2rem 0.6rem',
          borderRadius: '9999px',
          fontSize: '0.72rem',
          fontWeight: 700
        }}>
          🎯 {status}
        </span>
      );
    }
    if (s.includes('assessment')) {
      return (
        <span style={{
          background: 'var(--accent-amber-light)',
          color: 'var(--accent-amber)',
          border: '1px solid var(--accent-amber-border)',
          padding: '0.2rem 0.6rem',
          borderRadius: '9999px',
          fontSize: '0.72rem',
          fontWeight: 700
        }}>
          💻 {status}
        </span>
      );
    }
    return (
      <span style={{
        background: 'var(--bg-tertiary)',
        color: 'var(--text-secondary)',
        border: '1px solid var(--border-medium)',
        padding: '0.2rem 0.6rem',
        borderRadius: '9999px',
        fontSize: '0.72rem',
        fontWeight: 600
      }}>
        📄 {status}
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {}
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800 }}>Applied Companies Watchlist</h2>
            <span style={{
              background: 'var(--accent-amber-light)',
              color: 'var(--accent-amber)',
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '6px'
            }}>
              High Priority Trigger
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Only emails and trailing follow-ups for these companies will trigger instant notifications. Other company announcements remain silent in background.
          </p>
        </div>

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary"
        >
          <Plus size={16} /> Add Applied Company
        </button>
      </div>

      {}
      {showAddForm && (
        <form onSubmit={handleSubmit} className="light-card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem' }}>
            Register New Applied Drive
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Company Name *
              </label>
              <input
                type="text"
                placeholder="e.g. Infosys, TCS, Amazon"
                required
                value={newCompany.company_name}
                onChange={(e) => setNewCompany({ ...newCompany, company_name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-medium)',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Role / Profile
              </label>
              <input
                type="text"
                placeholder="e.g. SDE Trainee, AI Engineer"
                value={newCompany.role_title}
                onChange={(e) => setNewCompany({ ...newCompany, role_title: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-medium)',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Initial Status
              </label>
              <select
                value={newCompany.status}
                onChange={(e) => setNewCompany({ ...newCompany, status: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-medium)',
                  fontSize: '0.85rem',
                  background: 'white'
                }}
              >
                <option value="Applied">Applied</option>
                <option value="Assessment">Assessment Slot</option>
                <option value="Shortlisted">Shortlisted for Interview</option>
                <option value="Interview">Interview Scheduled</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              <CheckCircle2 size={16} /> Save to Watchlist
            </button>
          </div>
        </form>
      )}

      {}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
        {companies.map((comp) => (
          <div key={comp.id} className="light-card" style={{ padding: '1.25rem', position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--accent-amber-light)',
                  color: 'var(--accent-amber)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Building2 size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{comp.company_name}</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{comp.role_title}</div>
                </div>
              </div>

              <button
                onClick={() => onDeleteCompany(comp.id)}
                title="Remove from watchlist"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '4px',
                  borderRadius: '4px'
                }}
              >
                <Trash2 size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-light)' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Current Status</span>
                {getStatusBadge(comp.status)}
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Last Mail Update</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {comp.last_mail_date ? new Date(comp.last_mail_date).toLocaleDateString() : 'Monitoring...'}
                </span>
              </div>
            </div>

            {comp.last_update_summary && (
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '0.45rem 0.65rem',
                borderRadius: '6px',
                fontSize: '0.72rem',
                color: 'var(--text-secondary)',
                marginTop: '0.75rem'
              }}>
                <strong>Last Note:</strong> {comp.last_update_summary}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
