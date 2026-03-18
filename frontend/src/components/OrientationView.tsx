'use client';
import { useMoodContext } from './MoodProvider';

export default function OrientationView({ side }: { side: 'left' | 'right' }) {
  const { sensorData } = useMoodContext();
  const data = sensorData?.[side];

  // Default neutral
  let dx = 0;
  let dy = 0;
  let tilt = 0;

  if (data) {
    dx = data.dx * 50; // Scale up the normalized vector for visual magnitude
    dy = data.dy * 50;
    tilt = data.tilt;
  }

  // A sleek glassmorphism compass card
  return (
    <div className="flex flex-col items-center justify-center p-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-lg w-full max-w-[200px]">
      <h3 className="text-white/70 uppercase tracking-widest text-sm font-semibold mb-6">
        {side} Foot
      </h3>
      
      {/* The Compass Circle */}
      <div className="relative w-20 h-20 rounded-full border-2 border-white/20 flex items-center justify-center mb-6">
        <div className="absolute w-full h-full rounded-full border border-dashed border-white/20 animate-[spin_10s_linear_infinite]" />
        
        {/* The vector arrow */}
        <div 
          className="w-1 h-12 bg-cyan-400 absolute bottom-1/2 origin-bottom rounded-full transition-all duration-100 ease-linear shadow-[0_0_15px_rgba(34,211,238,0.6)]"
          style={{ 
            transform: `rotate(${Math.atan2(dx, -dy)}rad)`,
            height: `${Math.min(48, Math.sqrt(dx*dx + dy*dy))}px`
          }}
        >
          {/* Arrowhead */}
          <div className="absolute -top-1 -left-1 w-3 h-3 bg-cyan-400 rotate-45" />
        </div>

        {/* Center dot */}
        <div className="w-2 h-2 rounded-full bg-white z-10 shadow-[0_0_10px_white]" />
      </div>

      <div className="text-2xl font-black text-white font-mono tracking-tighter drop-shadow-md">
        {tilt.toFixed(1)}°
      </div>
      <div className="text-white/40 text-xs mt-1">TILT ANGLE</div>
    </div>
  );
}
