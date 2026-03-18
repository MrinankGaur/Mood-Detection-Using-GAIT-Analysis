'use client';

import React, { useRef, useEffect } from 'react';
import { useMoodContext } from './MoodProvider';

// Jet colormap roughly mapping 0-4096 (12-bit ADC)
function getJetColor(value: number, maxVal = 4096) {
  // If pressure is near zero, make it completely transparent so the insoles show through
  if (value < 50) return [0, 0, 0, 0];
  
  const v = Math.max(0, Math.min(1, value / maxVal));
  let r = 0, g = 0, b = 0;
  if (v < 0.125) {
    b = 0.5 + 4 * v;
  } else if (v < 0.375) {
    b = 1;
    g = 4 * (v - 0.125);
  } else if (v < 0.625) {
    r = 4 * (v - 0.375);
    g = 1;
    b = 1 - 4 * (v - 0.375);
  } else if (v < 0.875) {
    r = 1;
    g = 1 - 4 * (v - 0.625);
  } else {
    r = Math.max(0.5, 1 - 4 * (v - 0.875));
  }
  // We use full opacity (255) for areas with pressure
  return [Math.floor(r * 255), Math.floor(g * 255), Math.floor(b * 255), 255];
}

export default function HeatmapCanvas() {
  const { sensorData } = useMoodContext();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!sensorData || !canvasRef.current) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // We receive a flattened 50x50 array (z_rounded) from the Python Server
    const { heatmap, grid_size } = sensorData;
    const width = grid_size; 
    const height = grid_size; 

    // Create ImageData object directly for extreme performance
    const imageData = ctx.createImageData(width, height);
    
    for (let i = 0; i < heatmap.length; i++) {
        // map raw 12-bit value to RGBA
        const [r, g, b, a] = getJetColor(heatmap[i]);
        imageData.data[i * 4] = r;      
        imageData.data[i * 4 + 1] = g;  
        imageData.data[i * 4 + 2] = b;  
        imageData.data[i * 4 + 3] = a;  
    }

    // We draw the raw 50x50 image data on a temporary canvas, 
    // then scale it up onto the main canvas with CSS scaling for interpolation
    ctx.putImageData(imageData, 0, 0);

  }, [sensorData]);

  return (
    <div className="w-full h-full flex justify-center items-center overflow-hidden p-2 min-w-0 min-h-0">
      <div 
        className="relative rounded-3xl overflow-hidden border border-white/10 shadow-2xl bg-white shrink-0"
        style={{ height: '100%', minHeight: '0', aspectRatio: '430 / 563', maxWidth: '100%' }}
      >
        {/* Background Image of the insoles */}
        <div 
          className="absolute inset-0 bg-no-repeat bg-center" 
          style={{ backgroundImage: 'url("/insoles.png")', backgroundSize: '100% 100%' }} 
        />

        {/* The Actual Heatmap Canvas */}
        <canvas 
          ref={canvasRef}
          width={50}
          height={50}
          // CSS scaling applies browser's default smooth interpolation
          // Opacity 0.7 for standard matplotlib blending and blur-md for edge smoothing
          className="absolute inset-0 w-full h-full opacity-70 blur-md transform-gpu"
          style={{ imageRendering: 'auto' }}
        />
      </div>
    </div>
  );
}
