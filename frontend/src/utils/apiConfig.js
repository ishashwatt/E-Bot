export const API_BASE = (import.meta.env.VITE_API_URL || 'https://e-bot-fa9s.onrender.com').replace(/\/$/, '');
export const WS_BASE = API_BASE.replace(/^http/, 'ws');
