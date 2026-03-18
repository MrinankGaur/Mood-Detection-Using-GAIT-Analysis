'use client';

import { useMoodContext } from './MoodProvider';

const Activity = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
);

const Smile = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>
);

const Frown = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>
);

const Angry = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><path d="M7.5 8 10 9"/><path d="M14 9l2.5-1"/><path d="M9 10h.01"/><path d="M15 10h.01"/></svg>
);

const Loader2 = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
);

export default function MoodCard() {
  const { currentMood, isConnected, sensorData } = useMoodContext();

  const getMoodStyle = (mood: string) => {
    switch (mood.toLowerCase()) {
      case 'happy':
        return {
          bg: 'from-green-500/20 to-emerald-900/40',
          border: 'border-green-500/50',
          text: 'text-green-400',
          shadow: 'shadow-[0_0_30px_rgba(34,197,94,0.3)]',
          icon: <Smile className="w-16 h-16 text-green-400 mb-4 animate-bounce" />,
        };
      case 'sad':
        return {
          bg: 'from-blue-500/20 to-indigo-900/40',
          border: 'border-blue-500/50',
          text: 'text-blue-400',
          shadow: 'shadow-[0_0_30px_rgba(59,130,246,0.3)]',
          icon: <Frown className="w-16 h-16 text-blue-400 mb-4 animate-pulse" />,
        };
      case 'angry':
        return {
          bg: 'from-red-500/20 to-rose-900/40',
          border: 'border-red-500/50',
          text: 'text-red-400',
          shadow: 'shadow-[0_0_30px_rgba(239,68,68,0.3)]',
          icon: <Angry className="w-16 h-16 text-red-500 mb-4 animate-[wiggle_1s_ease-in-out_infinite]" />,
        };
      default:
        return {
          bg: 'from-white/5 to-white/10',
          border: 'border-white/10',
          text: 'text-white/50',
          shadow: '',
          icon: <Loader2 className="w-16 h-16 text-white/50 mb-4 animate-spin" />,
        };
    }
  };

  const style = getMoodStyle(currentMood);

  return (
    <div 
      className={`relative overflow-hidden rounded-[2.5rem] p-10 backdrop-blur-3xl border transition-all duration-700 ease-out bg-gradient-to-br flex flex-col items-center justify-center text-center w-full max-w-md ${style.bg} ${style.border} ${style.shadow}`}
    >
      {/* Background glow orb */}
      <div className={`absolute -top-20 -right-20 w-64 h-64 bg-current rounded-full blur-[100px] opacity-20 ${style.text}`} />
      
      {/* Connection Status Badge */}
      <div className="absolute top-6 right-6 flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-full border border-white/10 backdrop-blur-md">
        <Activity className={`w-4 h-4 ${isConnected ? 'text-green-400 animate-pulse' : 'text-red-500'}`} />
        <span className="text-xs font-medium text-white/80 tracking-wide uppercase">
          {isConnected ? 'Live' : 'Offline'}
        </span>
      </div>

      <div className="z-10 mt-8">
        {style.icon}
      </div>

      <div className="z-10 mb-2">
        <h2 className="text-sm font-bold tracking-[0.2em] text-white/40 uppercase">
          Predicted State
        </h2>
      </div>

      <div className="z-10 mb-2">
        <h1 className={`text-6xl font-black tracking-tighter capitalize drop-shadow-lg ${style.text}`}>
          {currentMood}
        </h1>
      </div>
      
      <div className="mt-6 z-10 flex flex-col items-center gap-2 w-full max-w-[200px]">
        <p className="text-sm text-white/60 font-medium tracking-wide">
          Buffering Next Batch: {sensorData?.buffer_count || 0} / 2400
        </p>
        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
           <div 
             className="h-full bg-cyan-400 transition-all duration-75 shadow-[0_0_10px_cyan]"
             style={{ width: `${Math.min(100, ((sensorData?.buffer_count || 0) / 2400) * 100)}%` }}
           />
        </div>
      </div>
    </div>
  );
}
