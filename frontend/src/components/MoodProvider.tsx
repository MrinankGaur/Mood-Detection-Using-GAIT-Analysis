'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

type SensorData = {
  heatmap: number[]; // the 50x50 integer values
  grid_size: number;
  right: { dx: number; dy: number; tilt: number };
  left: { dx: number; dy: number; tilt: number };
  buffer_count: number;
};

type MoodContextType = {
  sensorData: SensorData | null;
  currentMood: string;
  isConnected: boolean;
  isCollecting: boolean;
  startCollection: () => Promise<void>;
  stopCollection: () => Promise<void>;
};

const MoodContext = createContext<MoodContextType>({
  sensorData: null,
  currentMood: 'waiting...',
  isConnected: false,
  isCollecting: false,
  startCollection: async () => {},
  stopCollection: async () => {},
});

export const MoodProvider = ({ children }: { children: React.ReactNode }) => {
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [currentMood, setCurrentMood] = useState<string>('waiting...');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isCollecting, setIsCollecting] = useState<boolean>(false);

  const fetchState = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/state');
      if (res.ok) {
        const data = await res.json();
        setIsCollecting(data.is_collecting);
      }
    } catch (e) {
      console.error("Failed to fetch state", e);
    }
  };

  const startCollection = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/start', { method: 'POST' });
      if (res.ok) setIsCollecting(true);
    } catch (e) {
      console.error("Failed to start collection", e);
    }
  };

  const stopCollection = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/stop', { method: 'POST' });
      if (res.ok) setIsCollecting(false);
    } catch (e) {
      console.error("Failed to stop collection", e);
    }
  };

  useEffect(() => {
    fetchState();
    
    // Connect to the Python FastAPI WebSockets
    const streamWs = new WebSocket('ws://localhost:8000/ws/stream');
    const moodWs = new WebSocket('ws://localhost:8000/ws/mood');

    streamWs.onopen = () => setIsConnected(true);
    streamWs.onclose = () => setIsConnected(false);
    
    streamWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'sensor_frame') {
          setSensorData(data);
        } else if (data.type === 'error') {
          alert(data.message);
          setIsCollecting(false);
        }
      } catch (err) {
        console.error('Error parsing stream data', err);
      }
    };

    moodWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'mood_prediction') {
          setCurrentMood(data.mood);
        }
      } catch (err) {
        console.error('Error parsing mood data', err);
      }
    };

    return () => {
      streamWs.close();
      moodWs.close();
    };
  }, []);

  return (
    <MoodContext.Provider value={{ sensorData, currentMood, isConnected, isCollecting, startCollection, stopCollection }}>
      {children}
    </MoodContext.Provider>
  );
};

export const useMoodContext = () => useContext(MoodContext);
