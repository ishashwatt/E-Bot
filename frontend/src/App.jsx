import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { useNotifications } from './context/NotificationContext';
import { API_BASE } from './utils/apiConfig';
import { 
  ShieldAlert, 
  CheckCircle2, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  X,
  BellRing
} from 'lucide-react';

export default function App() {
  const [threads, setThreads] = useState([]);
  const [profile, setProfile] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [showBackgroundMails, setShowBackgroundMails] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  const { latestAlert, dismissAlert } = useNotifications();

  const fetchSilent = async () => {
    try {
      const [threadsRes, profileRes] = await Promise.all([
        fetch(`${API_BASE}/api/threads`),
        fetch(`${API_BASE}/api/profile`)
      ]);

      if (threadsRes.ok) setThreads(await threadsRes.json());
      if (profileRes.ok) setProfile(await profileRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    fetchSilent();
    const poll = setInterval(fetchSilent, 20000);
    return () => clearInterval(poll);
  }, []);

  const handleSyncNow = async () => {
    try {
      await fetch(`${API_BASE}/api/mail/sync-now`, { method: 'POST' });
      await fetchSilent();
    } catch (err) {
      console.error(err);
    }
  };

  const isPlacementOrAcademic = (t) => {
    if (t.priority === 'Critical' || t.priority === 'High') return true;
    if (t.has_identity_match || t.is_applied_company) return true;
    if (t.category && !['General', 'General Circular'].includes(t.category)) return true;
    return false;
  };

  const importantMails = threads.filter(isPlacementOrAcademic);
  const backgroundMails = threads.filter(t => !isPlacementOrAcademic(t));

  const getBadgeInfo = (item) => {
    if (item.priority === 'Critical' || item.has_identity_match) {
      return {
        label: '🎯 Shortlisted',
        className: 'badge-critical',
        border: '4px solid #ef4444',
        accentBg: 'var(--accent-ruby-light)',
        accentColor: 'var(--accent-ruby)'
      };
    }
    if (item.category === 'Pre-Placement Talk / Event Update' || item.category?.includes('Pre-Placement')) {
      return {
        label: '📢 Pre-Placement Talk',
        className: 'badge-high',
        border: '4px solid #06b6d4',
        accentBg: '#ecfeff',
        accentColor: '#0891b2'
      };
    }
    if (item.category === 'Eligible Placement Drive') {
      return {
        label: '✅ Eligible Drive',
        className: 'badge-high',
        border: '4px solid #10b981',
        accentBg: '#ecfdf5',
        accentColor: '#059669'
      };
    }
    if (item.category === 'Ineligible Placement Drive') {
      return {
        label: '❌ Not Eligible',
        className: 'badge-medium',
        border: '4px solid #f43f5e',
        accentBg: '#fff1f2',
        accentColor: '#e11d48'
      };
    }
    if (item.category === 'Not Shortlisted for Test / Round') {
      return {
        label: 'ℹ️ Not Shortlisted',
        className: 'badge-medium',
        border: '4px solid #8b5cf6',
        accentBg: 'var(--accent-violet-light)',
        accentColor: 'var(--accent-violet)'
      };
    }
    if (item.category === 'Practice / Mock Exam Notice') {
      return {
        label: '📢 Practice / Mock Exam',
        className: 'badge-medium',
        border: '4px solid #6366f1',
        accentBg: '#e0e7ff',
        accentColor: '#4338ca'
      };
    }
    if (item.category?.includes('Academic') || item.category?.includes('Program Chair')) {
      return {
        label: '🏛️ Academic Notice',
        className: 'badge-high',
        border: '4px solid #3b82f6',
        accentBg: '#eff6ff',
        accentColor: '#2563eb'
      };
    }
    if (item.category?.includes('CDC') || item.category?.includes('Placement Office')) {
      return {
        label: '📢 Placement Office Update',
        className: 'badge-high',
        border: '4px solid #f59e0b',
        accentBg: 'var(--accent-amber-light)',
        accentColor: 'var(--accent-amber)'
      };
    }
    return {
      label: '⚠️ Placement Update',
      className: 'badge-high',
      border: '4px solid var(--accent-amber)',
      accentBg: 'var(--accent-amber-light)',
      accentColor: 'var(--accent-amber)'
    };
  };

  return (
    <div className="app-layout">
      {}
      <Navbar
        profile={profile}
        onSyncNow={handleSyncNow}
      />

      {}
      {latestAlert && (
        <div style={{
          background: 'var(--accent-ruby-light)',
          borderBottom: '2px solid var(--accent-ruby)',
          padding: '0.85rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <BellRing size={20} color="#dc2626" />
            <div>
              <strong style={{ color: 'var(--accent-ruby)', fontSize: '0.88rem' }}>
                {latestAlert.title}
              </strong>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {latestAlert.reason}
              </div>
            </div>
          </div>
          <button onClick={dismissAlert} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>
      )}

      {}
      <main style={{ flex: 1, padding: '1.5rem 2rem', maxWidth: '960px', margin: '0 auto', width: '100%' }}>
        
        {}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.1rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.5rem'
        }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800 }}>College Mail Monitor</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Scanning incoming mails & attachments in the background.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', textAlign: 'right' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Important Mails</span>
              <strong style={{ fontSize: '1.3rem', color: 'var(--accent-ruby)' }}>{importantMails.length}</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Silenced in Background</span>
              <strong style={{ fontSize: '1.3rem', color: 'var(--text-secondary)' }}>{backgroundMails.length}</strong>
            </div>
          </div>
        </div>

        {}
        <section style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.85rem' }}>
            <span style={{
              background: 'var(--accent-ruby-light)',
              color: 'var(--accent-ruby)',
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '3px 8px',
              borderRadius: '6px'
            }}>
              IMPORTANT FOR YOU ({importantMails.length})
            </span>
          </div>

          {initialLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Checking mailbox...
            </div>
          ) : importantMails.length === 0 ? (
            <div style={{
              background: 'var(--bg-secondary)',
              border: '1px dashed var(--border-medium)',
              borderRadius: 'var(--radius-lg)',
              padding: '3rem 2rem',
              textAlign: 'center'
            }}>
              <CheckCircle2 size={32} color="#059669" style={{ margin: '0 auto 0.75rem auto' }} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>No Action Needed Right Now</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0.25rem auto 0 auto' }}>
                All scanned emails are general circulars. When a placement drive, assessment, or PDF shortlist with your roll number (23BAI11174) arrives, it will appear here immediately and ring your alert sound.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {importantMails.map((item) => {
                const isExpanded = expandedId === item.id;
                const isCritical = item.priority === 'Critical' || item.has_identity_match;

                const badge = getBadgeInfo(item);

                return (
                  <div
                    key={item.id}
                    className="light-card"
                    style={{
                      padding: '1.25rem',
                      borderLeft: badge.border,
                      background: 'var(--bg-secondary)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                          <span className={badge.className} style={{ background: badge.accentBg, color: badge.accentColor }}>
                            {badge.label}
                          </span>
                          {item.company_name && (
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', background: 'var(--bg-tertiary)', padding: '2px 6px', borderRadius: '4px' }}>
                              {item.company_name}
                            </span>
                          )}
                        </div>

                        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                          {item.subject}
                        </h3>

                        <div style={{
                          background: badge.accentBg,
                          color: badge.accentColor,
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          padding: '0.5rem 0.75rem',
                          borderRadius: '6px',
                          marginTop: '0.5rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}>
                          <ShieldAlert size={15} />
                          <span>{item.status_summary}</span>
                        </div>
                      </div>

                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {item.latest_received_at ? new Date(item.latest_received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                      </span>
                    </div>

                    {}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-light)' }}>
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : item.id)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--accent-emerald)',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        {isExpanded ? <><ChevronUp size={14} /> Hide Details</> : <><ChevronDown size={14} /> View Email & Attachments</>}
                      </button>

                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {item.messages?.length || 1} message(s) in thread
                      </span>
                    </div>

                    {}
                    {isExpanded && item.messages && (
                      <div style={{ marginTop: '0.75rem', background: 'var(--bg-tertiary)', padding: '0.85rem', borderRadius: '8px' }}>
                        {item.messages.map((m, mIdx) => (
                          <div key={mIdx} style={{ marginBottom: mIdx > 0 ? '1rem' : '0' }}>
                            <div style={{ fontSize: '0.75rem', fontWeight: 700, marginBottom: '4px' }}>
                              From: {m.sender}
                            </div>
                            <pre style={{
                              whiteSpace: 'pre-wrap',
                              fontFamily: 'inherit',
                              fontSize: '0.82rem',
                              color: 'var(--text-secondary)',
                              lineHeight: '1.4'
                            }}>
                              {m.body_text}
                            </pre>

                            {m.attachments && m.attachments.length > 0 && (
                              <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-medium)' }}>
                                <span style={{ fontSize: '0.72rem', fontWeight: 700, display: 'block', marginBottom: '4px' }}>Scanned Attachments:</span>
                                {m.attachments.map((a, aIdx) => (
                                  <div key={aIdx} style={{ fontSize: '0.75rem', color: 'var(--text-primary)', background: 'white', padding: '0.35rem 0.6rem', borderRadius: '4px', marginBottom: '3px' }}>
                                    📄 {a.filename} {a.has_match ? '🎯 (Target Matched Inside File!)' : ''}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {}
        <section>
          <button
            onClick={() => setShowBackgroundMails(!showBackgroundMails)}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              fontSize: '0.82rem',
              fontWeight: 600
            }}
          >
            <span>📁 General Circulars Scanned Silently ({backgroundMails.length})</span>
            {showBackgroundMails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showBackgroundMails && (
            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {backgroundMails.length === 0 ? (
                <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  No general notices scanned yet.
                </div>
              ) : (
                backgroundMails.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {item.subject}
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {item.status_summary || 'General circular'}
                      </span>
                    </div>

                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {item.latest_received_at ? new Date(item.latest_received_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
