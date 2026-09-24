import React, { useState } from 'react';
import { 
  Bell, 
  FileText, 
  Calendar, 
  CheckCircle2, 
  AlertTriangle, 
  Building2, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  ExternalLink,
  ShieldAlert,
  Volume2
} from 'lucide-react';

export const AlertFeed = ({ threads, loading, onSelectThread, onRefresh }) => {
  const [activeFilter, setActiveFilter] = useState('All');
  const [expandedThreadId, setExpandedThreadId] = useState(null);

  const filterThreads = () => {
    if (activeFilter === 'Critical') return threads.filter(t => t.priority === 'Critical');
    if (activeFilter === 'Applied') return threads.filter(t => t.is_applied_company || t.priority === 'High');
    if (activeFilter === 'Silenced') return threads.filter(t => t.priority === 'Low' || t.priority === 'Medium');
    return threads;
  };

  const filtered = filterThreads();

  const getPriorityBadge = (priority, category, hasIdentity) => {
    if (priority === 'Critical' || hasIdentity) {
      return (
        <span className="badge-critical">
          <ShieldAlert size={12} /> 🎯 SHORTLIST MATCH (Roll No / Name)
        </span>
      );
    }
    if (priority === 'High' || (category && category.includes('Eligible'))) {
      return (
        <span className="badge-high">
          <CheckCircle2 size={12} /> ✅ ELIGIBLE DRIVE
        </span>
      );
    }
    if (category && category.includes('Not Shortlisted')) {
      return (
        <span className="badge-medium" style={{ background: '#fef3c7', color: '#b45309', borderColor: '#fde68a' }}>
          <AlertTriangle size={12} /> ℹ️ NOT SHORTLISTED
        </span>
      );
    }
    if (category && category.includes('Ineligible')) {
      return (
        <span className="badge-medium" style={{ background: '#fee2e2', color: '#b91c1c', borderColor: '#fca5a5' }}>
          <AlertTriangle size={12} /> ❌ INELIGIBLE FOR DRIVE
        </span>
      );
    }
    return (
      <span className="badge-silent">
        <Clock size={12} /> 🔕 SILENT / GENERAL
      </span>
    );
  };


  const toggleExpand = (threadId, e) => {
    e.stopPropagation();
    setExpandedThreadId(expandedThreadId === threadId ? null : threadId);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        background: 'var(--bg-secondary)',
        padding: '1rem 1.25rem',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-light)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={() => setActiveFilter('All')}
            className={`nav-tab-btn ${activeFilter === 'All' ? 'active' : ''}`}
          >
            All Stream ({threads.length})
          </button>
          <button
            onClick={() => setActiveFilter('Critical')}
            className={`nav-tab-btn ${activeFilter === 'Critical' ? 'active' : ''}`}
            style={activeFilter === 'Critical' ? { color: 'var(--accent-ruby)', background: 'var(--accent-ruby-light)', borderColor: 'var(--accent-ruby-border)' } : {}}
          >
            🔴 Critical Matches ({threads.filter(t => t.priority === 'Critical').length})
          </button>
          <button
            onClick={() => setActiveFilter('Applied')}
            className={`nav-tab-btn ${activeFilter === 'Applied' ? 'active' : ''}`}
            style={activeFilter === 'Applied' ? { color: 'var(--accent-amber)', background: 'var(--accent-amber-light)', borderColor: 'var(--accent-amber-border)' } : {}}
          >
            🟡 Applied Companies ({threads.filter(t => t.is_applied_company || t.priority === 'High').length})
          </button>
          <button
            onClick={() => setActiveFilter('Silenced')}
            className={`nav-tab-btn ${activeFilter === 'Silenced' ? 'active' : ''}`}
          >
            🔇 Silenced / General ({threads.filter(t => t.priority === 'Low' || t.priority === 'Medium').length})
          </button>
        </div>

        <button
          onClick={onRefresh}
          className="btn-secondary"
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
        >
          ↻ Refresh Inbox
        </button>
      </div>

      {}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading email stream & scanning attachments...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px dashed var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          padding: '4rem 2rem',
          textAlign: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'var(--bg-tertiary)',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto'
          }}>
            <Bell size={24} />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>No Emails Found</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '400px', margin: '0 auto' }}>
            {activeFilter === 'Critical' 
              ? 'No critical identity matches detected yet. Trigger a test scenario to see real-time detection!'
              : 'No emails match this filter.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filtered.map((thread) => {
            const isExpanded = expandedThreadId === thread.thread_id;
            const latestMsg = thread.messages && thread.messages.length > 0 ? thread.messages[thread.messages.length - 1] : null;
            const hasAttachments = thread.messages?.some(m => m.attachments && m.attachments.length > 0);
            const isCritical = thread.priority === 'Critical' || thread.has_identity_match;

            return (
              <div
                key={thread.id}
                className="light-card"
                style={{
                  padding: '1.25rem',
                  borderLeft: isCritical 
                    ? '4px solid var(--accent-ruby)' 
                    : thread.is_applied_company || thread.priority === 'High' 
                      ? '4px solid var(--accent-amber)' 
                      : '4px solid var(--border-medium)',
                  position: 'relative'
                }}
              >
                {}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                      {getPriorityBadge(thread.priority, thread.category, thread.has_identity_match)}
                      
                      {thread.company_name && (
                        <span style={{
                          background: 'var(--bg-tertiary)',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-medium)',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 700
                        }}>
                          {thread.company_name}
                        </span>
                      )}

                      {thread.message_count > 1 && (
                        <span style={{
                          background: 'var(--accent-emerald-light)',
                          color: 'var(--accent-emerald)',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          border: '1px solid var(--accent-emerald-border)'
                        }}>
                          🧵 {thread.message_count} Mails in Thread
                        </span>
                      )}
                    </div>

                    <h3 style={{
                      fontSize: '1.05rem',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      marginTop: '0.25rem'
                    }}>
                      {thread.subject}
                    </h3>
                  </div>

                  <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {thread.latest_received_at ? new Date(thread.latest_received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                    </span>
                  </div>
                </div>

                {}
                <div style={{
                  background: isCritical ? 'var(--accent-ruby-light)' : thread.is_applied_company ? 'var(--accent-amber-light)' : 'var(--bg-tertiary)',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '0.85rem',
                  fontSize: '0.82rem',
                  color: isCritical ? 'var(--accent-ruby)' : thread.is_applied_company ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  {isCritical ? <ShieldAlert size={16} /> : <CheckCircle2 size={16} />}
                  <span>{thread.status_summary || 'Analyzed by E-Bot Relevance Engine.'}</span>
                </div>

                {}
                {latestMsg && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: '1.4' }}>
                    <p style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {latestMsg.body_text}
                    </p>
                  </div>
                )}

                {}
                {hasAttachments && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.85rem' }}>
                    {thread.messages.flatMap(m => m.attachments || []).map((att, i) => (
                      <div
                        key={i}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          background: att.has_match ? 'var(--accent-ruby-light)' : 'white',
                          border: `1px solid ${att.has_match ? 'var(--accent-ruby-border)' : 'var(--border-medium)'}`,
                          color: att.has_match ? 'var(--accent-ruby)' : 'var(--text-secondary)',
                          padding: '0.35rem 0.65rem',
                          borderRadius: '8px',
                          fontSize: '0.75rem',
                          fontWeight: 600
                        }}
                      >
                        <FileText size={14} />
                        <span>{att.filename}</span>
                        {att.has_match && (
                          <span style={{
                            background: 'var(--accent-ruby)',
                            color: 'white',
                            fontSize: '0.65rem',
                            padding: '1px 5px',
                            borderRadius: '4px',
                            fontWeight: 700
                          }}>
                            🎯 Roll No Found ({att.total_pages} Pages)
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
                  <button
                    onClick={(e) => toggleExpand(thread.thread_id, e)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--accent-emerald)',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {isExpanded ? <><ChevronUp size={16} /> Hide Trailing Conversation</> : <><ChevronDown size={16} /> View Conversation Timeline ({thread.message_count})</>}
                  </button>

                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Recipient: 23BAI11174@college.edu.in
                  </span>
                </div>

                {}
                {isExpanded && (
                  <div style={{ marginTop: '1rem', borderTop: '1px dashed var(--border-medium)', paddingTop: '1rem' }}>
                    <div className="thread-tree">
                      {thread.messages?.map((msg, idx) => {
                        const isHit = msg.matched_identity;
                        return (
                          <div key={msg.id} className="thread-node">
                            <div className={`thread-node-dot ${isHit ? 'critical' : msg.is_trailing_mail ? 'trailing' : ''}`} />
                            
                            <div style={{
                              background: isHit ? 'var(--accent-ruby-light)' : 'var(--bg-tertiary)',
                              border: `1px solid ${isHit ? 'var(--accent-ruby-border)' : 'var(--border-light)'}`,
                              borderRadius: 'var(--radius-md)',
                              padding: '1rem'
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.75rem' }}>
                                <div>
                                  <strong style={{ color: 'var(--text-primary)' }}>From: {msg.sender}</strong>
                                  {msg.is_trailing_mail && (
                                    <span style={{ marginLeft: '8px', color: 'var(--accent-amber)', fontWeight: 700 }}>
                                      [Trailing Follow-up #{idx + 1}]
                                    </span>
                                  )}
                                </div>
                                <span style={{ color: 'var(--text-muted)' }}>
                                  {msg.received_at ? new Date(msg.received_at).toLocaleString() : ''}
                                </span>
                              </div>

                              {msg.change_summary && (
                                <div style={{
                                  background: 'white',
                                  padding: '0.4rem 0.6rem',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  color: 'var(--accent-amber)',
                                  marginBottom: '0.5rem',
                                  border: '1px solid var(--accent-amber-border)'
                                }}>
                                  {msg.change_summary}
                                </div>
                              )}

                              <pre style={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'inherit',
                                fontSize: '0.82rem',
                                color: 'var(--text-secondary)',
                                lineHeight: '1.4'
                              }}>
                                {msg.body_text}
                              </pre>

                              {}
                              {msg.attachments && msg.attachments.length > 0 && (
                                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-light)' }}>
                                  <div style={{ fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
                                    Attachments ({msg.attachments.length}):
                                  </div>
                                  {msg.attachments.map((a, aIdx) => (
                                    <div key={aIdx} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', background: 'white', padding: '0.4rem', borderRadius: '6px', border: '1px solid var(--border-light)', marginBottom: '4px' }}>
                                      📄 <strong>{a.filename}</strong> — {a.has_match ? '🎯 Match verified on Row/Page index' : 'Clean document scanned'}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
