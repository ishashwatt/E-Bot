import React from 'react';
import { X, UserCheck, Volume2, Play, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

export const ProfileModal = ({ isOpen, onClose, profile }) => {
  const { testSound, selectedSound, setSelectedSound } = useNotifications();

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'var(--accent-emerald-light)',
              color: 'var(--accent-emerald)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <UserCheck size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Student Profile & Target Criteria</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Loaded securely from backend environment configuration
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
              🎯 Direct Search Target Identifiers
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.85rem' }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.65rem 0.85rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Candidate Full Name</span>
                <strong style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>{profile?.name || 'Shashwat Pratap Singh'}</strong>
              </div>

              <div style={{ background: 'var(--bg-tertiary)', padding: '0.65rem 0.85rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>College Roll Number</span>
                <strong style={{ fontSize: '0.88rem', color: 'var(--accent-emerald)', fontFamily: 'monospace' }}>{profile?.roll_number || '23BAI11174'}</strong>
              </div>

              <div style={{ background: 'var(--bg-tertiary)', padding: '0.65rem 0.85rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>NeoPAT Assessment ID</span>
                <strong style={{ fontSize: '0.88rem', color: 'var(--accent-amber)', fontFamily: 'monospace' }}>{profile?.neopat_id || 'S4Z5F7U9'}</strong>
              </div>
            </div>
          </div>

          {}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
              📊 Academic Eligibility Metrics
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.65rem' }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.6rem 0.75rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Branch</span>
                <strong style={{ fontSize: '0.82rem' }}>{profile?.branch || 'CSE (AI & ML)'}</strong>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.6rem 0.75rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Batch</span>
                <strong style={{ fontSize: '0.82rem' }}>{profile?.batch_year || 2027}</strong>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.6rem 0.75rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Current CGPA</span>
                <strong style={{ fontSize: '0.82rem', color: 'var(--accent-emerald)' }}>{profile?.current_cgpa || 7.85}</strong>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.6rem 0.75rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>10th Score</span>
                <strong style={{ fontSize: '0.82rem' }}>{profile?.tenth_percentage || 72.6}%</strong>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '0.6rem 0.75rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>12th Score</span>
                <strong style={{ fontSize: '0.82rem' }}>{profile?.twelfth_percentage || 69.0}%</strong>
              </div>
            </div>
          </div>

          {}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
              🔊 Active Alert Chime Tone
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.65rem' }}>
              {[
                { id: 'urgent_ping', name: '🚨 Urgent Dual-Tone Pulse' },
                { id: 'chime', name: '🔔 High Priority Bell' },
                { id: 'crystal', name: '✨ Crystal Ding (Soft Harmony)' },
                { id: 'radar', name: '📡 Radar Wave Pulse' }
              ].map((snd) => (
                <div
                  key={snd.id}
                  onClick={() => setSelectedSound(snd.id)}
                  style={{
                    border: `1px solid ${selectedSound === snd.id ? 'var(--accent-emerald)' : 'var(--border-medium)'}`,
                    background: selectedSound === snd.id ? 'var(--accent-emerald-light)' : 'white',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.6rem 0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{snd.name}</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      testSound(snd.id);
                    }}
                    style={{
                      background: 'white',
                      border: '1px solid var(--border-medium)',
                      borderRadius: '4px',
                      padding: '2px 6px',
                      fontSize: '0.68rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '3px'
                    }}
                  >
                    <Play size={10} fill="currentColor" /> Test
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-light)', paddingTop: '1rem' }}>
            <button type="button" onClick={onClose} className="btn-primary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
