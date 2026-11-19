const defaultUrl = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://localhost:8000'
  : 'https://e-bot-fa9s.onrender.com';

export const API_BASE = (import.meta.env.VITE_API_URL || defaultUrl).replace(/\/$/, '');
export const WS_BASE = API_BASE.replace(/^http/, 'ws');

