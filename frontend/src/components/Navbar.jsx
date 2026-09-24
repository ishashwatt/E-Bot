import React from 'react';
import { Volume2, VolumeX, RefreshCw } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

export const Navbar = ({ profile, onSyncNow }) => {
  const { soundEnabled, setSoundEnabled } = useNotifications();
  const [syncing, setSyncing] = React.useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await onSyncNow();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          E-Bot
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {}
        <button
          onClick={() => setSoundEnabled(!soundEnabled)}
          style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            color: soundEnabled ? 'var(--accent-emerald)' : 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0.45rem 0.8rem',
            fontSize: '0.78rem',
            fontWeight: 600
          }}
        >
          {soundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          <span>{soundEnabled ? 'Alert Sound ON' : 'Muted'}</span>
        </button>

        {}
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '0.45rem 0.8rem' }}
        >
          <RefreshCw className={syncing ? 'animate-spin' : ''} size={14} />
          {syncing ? 'Checking...' : 'Check Mails'}
        </button>

        {}
        <div style={{
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-light)',
          padding: '0.4rem 0.8rem',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.78rem',
          fontWeight: 700,
          color: 'var(--text-primary)'
        }}>
          {profile?.name || 'Shashwat Pratap Singh'} ({profile?.roll_number || '23BAI11174'})
        </div>
      </div>
    </header>
  );
};
