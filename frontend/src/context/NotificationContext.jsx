import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { soundPlayer } from '../utils/audioAlerts';
import { WS_BASE } from '../utils/apiConfig';

const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [wsConnected, setWsConnected] = useState(false);
  const [latestAlert, setLatestAlert] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [selectedSound, setSelectedSound] = useState('urgent_ping');
  const [notificationHistory, setNotificationHistory] = useState([]);

  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(`${WS_BASE}/api/ws`);

        ws.onopen = () => {
          setWsConnected(true);
          console.log('[WebSocket] Connected to E-Bot Realtime Service');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'NEW_ALERT') {
              setLatestAlert(data);
              setNotificationHistory((prev) => [data, ...prev]);

              if (soundEnabled) {
                if (data.priority === 'Critical') {
                  soundPlayer.playCriticalAlarm();
                } else if (data.priority === 'High') {
                  soundPlayer.playHighPriorityChime();
                } else {
                  soundPlayer.playSoundByName(selectedSound);
                }
              }
            }
          } catch (err) {
            console.error('[WebSocket] Message parsing error:', err);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
          ws.close();
        };
      } catch (err) {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [soundEnabled, selectedSound]);

  const testSound = useCallback((soundName = selectedSound) => {
    soundPlayer.playSoundByName(soundName);
  }, [selectedSound]);

  const dismissAlert = () => setLatestAlert(null);

  return (
    <NotificationContext.Provider
      value={{
        wsConnected,
        latestAlert,
        dismissAlert,
        soundEnabled,
        setSoundEnabled,
        selectedSound,
        setSelectedSound,
        testSound,
        notificationHistory
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => useContext(NotificationContext);
