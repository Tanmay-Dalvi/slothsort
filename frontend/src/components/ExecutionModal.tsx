import React from 'react';
import {
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Loader2,
  Lock,
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
              ? 'bg-forest-50/70 border-forest-300'
              : executionResult.status === 'PARTIAL_FAILURE'
              ? 'bg-amber-50 border-amber-300'
              : 'bg-red-50 border-red-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {executionResult.status === 'SUCCESS' ? (
                <CheckCircle className="w-5 h-5 text-forest-700" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              )}
              <span className="font-bold text-sm text-slate-900">
                Batch Result: {executionResult.status}
              </span>
            </div>

            {executionResult.undo_manifest_id && (
              <span className="text-xs font-mono bg-white px-2 py-0.5 rounded border border-forest-200 text-forest-900">
                {executionResult.undo_manifest_id}
              </span>
            )}
          </div>

          <p className="text-xs text-slate-700 leading-relaxed">
            Successfully moved {executionResult.executed_count} file(s).
            {executionResult.failed_count > 0 && ` ${executionResult.failed_count} file(s) failed.`}
          </p>

          {executionResult.errors.length > 0 && (
            <div className="space-y-1 text-xs text-red-700 font-mono bg-white/70 p-2 rounded border border-red-200">
              {executionResult.errors.map((err, i) => (
                <div key={i}>{err}</div>
              ))}
            </div>
          )}

          {/* Quick 1-Click Rollback Action */}
          {executionResult.undo_manifest_id && (
            <div className="pt-2 flex items-center justify-between border-t border-forest-200/60">
              <span className="text-xs text-slate-600 font-medium">
                Regret this organization? Restore files immediately.
              </span>
              <button
                type="button"
                onClick={() => onUndoBatch(executionResult.undo_manifest_id!)}
                disabled={isUndoing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-forest-900 border border-forest-400 hover:bg-forest-100 shadow-sm transition"
              >
                {isUndoing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Reverting...</span>
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
            </div>

            <p className="text-xs text-slate-500">
              Deterministic moves only. SlothSort will never overwrite or delete files.
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
                  <span>Applying Changes...</span>
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4 text-forest-300" />
                  <span>Apply Approved Changes ({approvedCount})</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
