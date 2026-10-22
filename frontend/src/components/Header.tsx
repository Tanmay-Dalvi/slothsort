import React from 'react';
import { History, ShieldCheck, Wifi, WifiOff, Sparkles } from 'lucide-react';
import { SlothMascot } from './SlothMascot';

interface HeaderProps {
  isBackendConnected: boolean;
  historyCount: number;
  onOpenHistory: () => void;
  isDemo?: boolean;
  onToggleDemo?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isBackendConnected,
  historyCount,
  onOpenHistory,
  isDemo = false,
  onToggleDemo,
}) => {
  return (
    <header className="border-b border-cream-200 bg-white shadow-sm sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3.5">
          <SlothMascot size={42} />
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-forest-900 font-sans">
                SlothSort
              </span>
              <span className="hidden sm:inline-flex items-center rounded-full bg-forest-100 px-2 py-0.5 text-xs font-medium text-forest-800 border border-forest-300">
                Slow & Steady
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Let your laptop clean up after you.
            </p>
          </div>
        </div>

        {/* Status Indicators & History Trigger */}
        <div className="flex items-center space-x-2.5 sm:space-x-4">
          {/* Demo Sandbox or Backend Health Badge */}
          {isDemo ? (
            <div className="flex items-center space-x-2">
              <div
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300 shadow-xs"
                title="Running in browser demo sandbox. No real files are modified."
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
                <span>Demo Sandbox</span>
              </div>
              {onToggleDemo && (
                <button
                  type="button"
                  onClick={onToggleDemo}
                  className="hidden sm:inline text-[11px] font-medium text-slate-500 hover:text-slate-800 underline decoration-slate-300 transition"
                  title="Switch to local backend mode"
                >
                  Live Mode
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <div
                className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                  isBackendConnected
                    ? 'bg-forest-50 text-forest-800 border-forest-200'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
                title={
                  isBackendConnected
                    ? 'Backend server connected at 127.0.0.1:8000'
                    : 'Cannot reach backend at 127.0.0.1:8000'
                }
              >
                {isBackendConnected ? (
                  <>
                    <Wifi className="w-3.5 h-3.5 text-forest-600 animate-pulse" />
                    <span className="hidden sm:inline">Engine Online</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3.5 h-3.5 text-red-500" />
                    <span>Engine Offline</span>
                  </>
                )}
              </div>
              {!isBackendConnected && onToggleDemo && (
                <button
                  type="button"
                  onClick={onToggleDemo}
                  className="text-[11px] font-semibold text-forest-700 hover:text-forest-900 bg-forest-50 hover:bg-forest-100 px-2 py-0.5 rounded border border-forest-200 transition"
                  title="Try interactive demo sandbox without running local backend"
                >
                  Try Demo
                </button>
              )}
            </div>
          )}

          {/* Privacy badge */}
          <div className="hidden lg:inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-cream-100 text-slate-600 border border-cream-300">
            <ShieldCheck className="w-3.5 h-3.5 text-forest-700" />
            <span>Advisory AI • Zero Deletion</span>
          </div>

          {/* History / Undo Button */}
          <button
            onClick={onOpenHistory}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white text-forest-800 border border-forest-300 hover:bg-forest-50 active:bg-forest-100 transition shadow-sm"
            aria-label="View organization history and undo batches"
          >
            <History className="w-4 h-4 text-forest-700" />
            <span>History</span>
            {historyCount > 0 && (
              <span className="ml-1 bg-forest-600 text-white rounded-full px-1.5 py-0.2 text-[10px] font-bold">
                {historyCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
