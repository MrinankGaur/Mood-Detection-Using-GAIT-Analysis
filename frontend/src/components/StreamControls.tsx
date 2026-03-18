'use client';
import { useMoodContext } from './MoodProvider';

export default function StreamControls() {
  const { isCollecting, startCollection, stopCollection } = useMoodContext();

  return (
    <div className="flex items-center gap-3">
      {isCollecting ? (
        <button 
          onClick={stopCollection}
          className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/50 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-red-500/30 transition-colors shadow-[0_0_15px_rgba(239,68,68,0.2)] flex items-center gap-2"
        >
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Stop Data Stream
        </button>
      ) : (
        <button 
          onClick={startCollection}
          className="px-4 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-emerald-500/30 transition-colors shadow-[0_0_15px_rgba(16,185,129,0.2)] flex items-center gap-2"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          Start Data Stream
        </button>
      )}
    </div>
  );
}
