'use client';

import { MoodProvider } from '@/components/MoodProvider';
import HeatmapCanvas from '@/components/HeatmapCanvas';
import OrientationView from '@/components/OrientationView';
import MoodCard from '@/components/MoodCard';
import StreamControls from '@/components/StreamControls';

export default function Home() {
  return (
    <MoodProvider>
      <main className="h-screen w-screen bg-[#05050A] text-white p-2 md:p-4 font-sans selection:bg-cyan-500/30 overflow-hidden flex flex-col">
        
        {/* Header Section */}
        <header className="mb-2 border-b border-white/10 pb-2 shrink-0">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight bg-gradient-to-br from-white to-white/40 bg-clip-text text-transparent mb-0.5">
                GAIT Analysis
              </h1>
              <p className="text-white/40 font-medium tracking-wide text-xs">
                Real-time Biometric Mood Detection System
              </p>
            </div>
            <StreamControls />
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1700px] mx-auto w-full">
          
          {/* Left Column: Mood & Analytics */}
          <div className="lg:col-span-3 flex flex-col gap-4 h-full min-h-0">
            <div className="flex-1 min-h-0 w-full flex justify-center items-center">
              <MoodCard />
            </div>
            
            <div className="shrink-0 p-4 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl shadow-2xl">
              <h3 className="text-white/70 font-semibold mb-3 uppercase tracking-wider text-[10px] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_10px_cyan]"></span>
                System Metrics
              </h3>
              
              <div className="space-y-2 font-medium text-[11px]">
                <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                  <span className="text-white/40">Sensor Stream</span>
                  <span className="font-mono text-cyan-400 bg-cyan-950/30 px-2 py-0.5 rounded-full border border-cyan-900/50">100 Hz</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                  <span className="text-white/40">Socket Source</span>
                  <span className="font-mono text-white/80">192.168.4.1</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                  <span className="text-white/40">Model Pipeline</span>
                  <span className="font-mono text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded-full border border-emerald-900/50">RandomForest</span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-white/40">Batch Check</span>
                  <span className="font-mono text-white/80">2,400 Ticks</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Visualization */}
          <div className="lg:col-span-9 flex justify-center items-center h-full min-h-0">
            <div className="relative w-full h-full max-h-[88vh] max-w-[1200px] py-4 px-4 lg:px-6 rounded-[3rem] bg-gradient-to-b from-[#131422] to-[#0A0B14] border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col items-center justify-between overflow-hidden">
                
                {/* Ambient glow behind feet */}
                <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-cyan-500/10 rounded-full blur-[80px] pointer-events-none mix-blend-screen" />
                <div className="absolute top-1/2 right-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-[80px] pointer-events-none mix-blend-screen" />

                <div className="w-full flex justify-between items-center px-4 z-20 shrink-0">
                    <h2 className="text-white/60 font-semibold tracking-widest uppercase text-[10px]">Realtime Heatmap</h2>
                    <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-[9px] font-mono text-white/40">ACTIVE WEBSOCKET</span>
                    </div>
                </div>

                {/* Main Visuals: Left Quiver | Canvas Heatmap | Right Quiver */}
                <div className="flex-1 flex flex-col md:flex-row items-center justify-between w-full z-10 px-2 min-h-0 py-2 min-w-0 gap-2">
                  
                  <div className="flex justify-center shrink-0 min-w-0 w-[120px] lg:w-[160px]">
                    <OrientationView side="left" />
                  </div>

                  <div className="flex-1 flex justify-center h-full min-h-0 min-w-0 p-2 overflow-hidden">
                    <HeatmapCanvas /> 
                  </div>

                  <div className="flex justify-center shrink-0 min-w-0 w-[120px] lg:w-[160px]">
                    <OrientationView side="right" />
                  </div>
                  
                </div>
            </div>
          </div>

        </div>
      </main>
    </MoodProvider>
  );
}
