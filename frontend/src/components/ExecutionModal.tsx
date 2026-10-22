import React from 'react';
import {
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Loader2,
  Lock,
  Sparkles,
} from 'lucide-react';
import { ExecutionResult } from '../types/api';

interface ExecutionModalProps {
  approvedCount: number;
  totalCount: number;
  conflictsCount: number;
  hasUnsavedEdits: boolean;
  isExecuting: boolean;
  isPlanExecuted: boolean;
  executionResult: ExecutionResult | null;
  onConfirmExecute: () => void;
  onUndoBatch: (manifestId: string) => void;
  isUndoing: boolean;
  isDemo?: boolean;
}

export const ExecutionModal: React.FC<ExecutionModalProps> = ({
  approvedCount,
  totalCount,
  conflictsCount,
  hasUnsavedEdits,
  isExecuting,
  isPlanExecuted,
  executionResult,
  onConfirmExecute,
  onUndoBatch,
  isUndoing,
  isDemo = false,
}) => {
  const isBlockedByConflicts = conflictsCount > 0;
  const isBlockedByEdits = hasUnsavedEdits;
  const isBlockedByCount = approvedCount === 0;

  const canExecute =
    !isExecuting &&
    !isPlanExecuted &&
    !isBlockedByConflicts &&
    !isBlockedByEdits &&
    !isBlockedByCount;

  return (
    <div className="bg-white rounded-xl p-5 border border-cream-200 shadow-md space-y-4">
      {/* Active State / Post-Execution Result */}
      {executionResult && (
        <div
          className={`p-4 rounded-xl border space-y-3 ${
            executionResult.status === 'SUCCESS'
              ? 'bg-forest-50/80 border-forest-200 text-forest-950'
              : executionResult.status === 'PARTIAL_FAILURE'
              ? 'bg-amber-50 border-amber-200 text-amber-950'
              : 'bg-red-50 border-red-200 text-red-950'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-forest-700 flex-shrink-0" />
              <div>
                <h3 className="font-bold text-sm">
                  {isDemo
                    ? `Simulated Execution Complete (${executionResult.executed_count} files)`
                    : `Execution Complete (${executionResult.executed_count} files moved)`}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  {isDemo
                    ? 'In this public browser sandbox, operations were simulated in memory. No real files were altered.'
                    : 'Safe move batch finished. Audit manifest logged for full rollback support.'}
                </p>
              </div>
            </div>

            {executionResult.undo_manifest_id && (
              <span className="text-[11px] font-mono bg-white/80 px-2 py-0.5 rounded border border-forest-200 text-forest-800">
                Manifest: {executionResult.undo_manifest_id.slice(0, 16)}...
              </span>
            )}
          </div>

          {executionResult.errors.length > 0 && (
            <div className="text-xs text-red-700 bg-white/70 p-2.5 rounded-lg border border-red-200 space-y-1">
              <div className="font-semibold">Operation errors encountered:</div>
              <ul className="list-disc pl-4 space-y-0.5">
                {executionResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Quick Undo Action Trigger */}
          {executionResult.undo_manifest_id && (
            <div className="pt-2 flex items-center justify-between border-t border-forest-200/60">
              <span className="text-xs text-forest-800 font-medium">
                Changed your mind? Restore all items instantly.
              </span>
              <button
                type="button"
                onClick={() => onUndoBatch(executionResult.undo_manifest_id!)}
                disabled={isUndoing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-forest-900 border border-forest-300 hover:bg-forest-100 transition shadow-xs"
              >
                {isUndoing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-forest-700" />
                    <span>Rolling back...</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3.5 h-3.5 text-forest-700" />
                    <span>Undo This Batch Now</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Pre-Execution Action Controls */}
      {!isPlanExecuted && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-sm text-slate-900">
                Approval Required
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cream-100 text-slate-700 border border-cream-300">
                {approvedCount} of {totalCount} files selected
              </span>
              {isDemo && (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                  Sandbox Simulation
                </span>
              )}
            </div>

            <p className="text-xs text-slate-500">
              {isDemo
                ? 'Simulated moves only. In public demo mode, no real files on your computer or servers are modified.'
                : 'Deterministic moves only. SlothSort will never overwrite or delete files.'}
            </p>

            {isBlockedByConflicts && (
              <p className="text-xs text-red-600 font-semibold flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Blocked: Resolve {conflictsCount} destination conflict(s) before applying.</span>
              </p>
            )}

            {isBlockedByEdits && (
              <p className="text-xs text-amber-700 font-medium">
                Unsaved edits: Click &ldquo;Validate Edits&rdquo; in the table above before executing.
              </p>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={onConfirmExecute}
              disabled={!canExecute}
              className={`inline-flex items-center space-x-2 px-6 py-2.5 rounded-lg font-bold text-sm shadow-sm transition ${
                canExecute
                  ? 'bg-forest-800 hover:bg-forest-900 active:bg-forest-950 text-white'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isExecuting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-forest-300" />
                  <span>{isDemo ? 'Simulating Move Batch...' : 'Applying Changes...'}</span>
                </>
              ) : (
                <>
                  {isDemo ? (
                    <Sparkles className="w-4 h-4 text-amber-300" />
                  ) : (
                    <Lock className="w-4 h-4 text-forest-300" />
                  )}
                  <span>
                    {isDemo
                      ? `Simulate Execution (${approvedCount})`
                      : `Apply Approved Changes (${approvedCount})`}
                  </span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
