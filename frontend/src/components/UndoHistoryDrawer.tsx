import React from 'react';
import { X, RotateCcw, Clock, CheckCircle2, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { RollbackResult, UndoManifest } from '../types/api';

interface UndoHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  manifests: UndoManifest[];
  onRollback: (manifestId: string) => void;
  onRefresh: () => void;
  isRollingBack: boolean;
  activeRollingBackId: string | null;
  lastRollbackResult: RollbackResult | null;
}

export const UndoHistoryDrawer: React.FC<UndoHistoryDrawerProps> = ({
  isOpen,
  onClose,
  manifests,
  onRollback,
  onRefresh,
  isRollingBack,
  activeRollingBackId,
  lastRollbackResult,
}) => {
  if (!isOpen) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ROLLED_BACK':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-600 border border-gray-300">
            ROLLED BACK
          </span>
        );
      case 'PARTIALLY_ROLLED_BACK':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
            PARTIAL ROLLBACK
          </span>
        );
      case 'ROLLBACK_FAILED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 border border-red-300">
            ROLLBACK BLOCKED
          </span>
        );
      case 'APPLIED':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-forest-100 text-forest-800 border border-forest-300">
            APPLIED
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-cream-200">
        {/* Drawer Header */}
        <div className="p-4 border-b border-cream-200 flex items-center justify-between bg-cream-50">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-forest-800" />
            <h2 className="text-base font-bold text-slate-900">
              Organization History & Undo
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onRefresh}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-cream-200 transition"
              title="Refresh history"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-cream-200 transition"
              aria-label="Close history drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Optional Last Rollback Notice */}
        {lastRollbackResult && (
          <div
            className={`m-4 p-3 rounded-lg border text-xs space-y-1 ${
              lastRollbackResult.status === 'ROLLED_BACK'
                ? 'bg-forest-50 border-forest-300 text-forest-900'
                : 'bg-amber-50 border-amber-300 text-amber-900'
            }`}
          >
            <div className="font-bold flex items-center space-x-1.5">
              {lastRollbackResult.status === 'ROLLED_BACK' ? (
                <CheckCircle2 className="w-4 h-4 text-forest-700" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-600" />
              )}
              <span>Rollback Status: {lastRollbackResult.status}</span>
            </div>
            <p className="text-[11px]">
              Restored {lastRollbackResult.restored_count} file(s) to original locations.
              {lastRollbackResult.failed_count > 0 && ` ${lastRollbackResult.failed_count} file(s) failed.`}
            </p>
            {lastRollbackResult.errors.length > 0 && (
              <div className="mt-1 space-y-0.5 text-[10px] text-red-700 font-mono">
                {lastRollbackResult.errors.map((e, i) => (
                  <div key={i}>{e}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {manifests.length === 0 ? (
            <div className="text-center py-12 text-slate-400 space-y-2">
              <Clock className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs">No previous organization batches found.</p>
            </div>
          ) : (
            manifests.map((m) => {
              const isApplied = m.status === 'APPLIED';
              const isWorking = isRollingBack && activeRollingBackId === m.manifest_id;

              return (
                <div
                  key={m.manifest_id}
                  className="p-3.5 rounded-xl border border-cream-200 bg-white hover:border-forest-200 transition space-y-2.5 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-mono text-xs font-bold text-slate-900">
                        {m.manifest_id}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(m.executed_at).toLocaleString()}
                      </div>
                    </div>
                    {getStatusBadge(m.status)}
                  </div>

                  <div className="text-xs text-slate-600 space-y-1">
                    <div className="truncate font-mono text-[11px] text-slate-500">
                      Root: {m.root_path}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800">{m.steps.length}</span> file(s) moved via{' '}
                      <span className="font-mono text-forest-800">{m.provider}</span>
                    </div>
                  </div>

                  {/* 1-Click Rollback */}
                  {isApplied && (
                    <div className="pt-2 border-t border-cream-200 flex justify-end">
                      <button
                        type="button"
                        onClick={() => onRollback(m.manifest_id)}
                        disabled={isRollingBack}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-forest-800 text-white hover:bg-forest-900 active:bg-forest-950 transition disabled:opacity-50"
                      >
                        {isWorking ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Reverting...</span>
                          </>
                        ) : (
                          <>
                            <RotateCcw className="w-3.5 h-3.5" />
                            <span>Undo Batch</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-cream-200 bg-cream-50 text-[11px] text-slate-500">
          Undoing a batch safely restores files to their pre-move locations and removes empty created folders.
        </div>
      </div>
    </div>
  );
};
