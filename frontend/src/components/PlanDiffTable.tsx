import React, { useState } from 'react';
import {
  FileOperation,
  OperationType,
} from '../types/api';
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Edit2,
  RefreshCw,
  FolderInput,
  Tag,
  CheckSquare,
  Square,
} from 'lucide-react';

interface PlanDiffTableProps {
  operations: FileOperation[];
  conflictsDetected: number;
  hasUnsavedEdits: boolean;
  isValidating: boolean;
  onToggleApprove: (opId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onEditOperation: (opId: string, newCategory: string, newFilename: string) => void;
  onValidateEdits: () => void;
}

export const PlanDiffTable: React.FC<PlanDiffTableProps> = ({
  operations,
  conflictsDetected,
  hasUnsavedEdits,
  isValidating,
  onToggleApprove,
  onSelectAll,
  onDeselectAll,
  onEditOperation,
  onValidateEdits,
}) => {
  const [editingOpId, setEditingOpId] = useState<string | null>(null);
  const [editCategory, setEditCategory] = useState<string>('');
  const [editFilename, setEditFilename] = useState<string>('');

  const approvedCount = operations.filter((op) => op.is_approved).length;
  const allSelected = approvedCount === operations.length && operations.length > 0;

  const startEditing = (op: FileOperation) => {
    setEditingOpId(op.op_id);
    const parts = op.target_rel_path.split('/');
    if (parts.length > 1) {
      setEditFilename(parts[parts.length - 1]);
      setEditCategory(parts.slice(0, -1).join('/'));
    } else {
      setEditFilename(parts[0]);
      setEditCategory('');
    }
  };

  const saveEdit = (opId: string) => {
    onEditOperation(opId, editCategory.trim(), editFilename.trim());
    setEditingOpId(null);
  };

  const cancelEdit = () => {
    setEditingOpId(null);
  };

  const getOpBadge = (opType: OperationType) => {
    switch (opType) {
      case 'MOVE':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200">MOVE</span>;
      case 'RENAME':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 text-purple-800 border border-purple-200">RENAME</span>;
      case 'MOVE_AND_RENAME':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200">MOVE & RENAME</span>;
      case 'KEEP':
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700 border border-gray-200">KEEP</span>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-cream-200 shadow-sm overflow-hidden space-y-0">
      {/* Table Header & Controls Bar */}
      <div className="p-4 bg-cream-50/70 border-b border-cream-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-forest-900 flex items-center space-x-2">
            <span>Proposed Organization Plan</span>
            <span className="text-xs font-normal text-slate-500">
              ({approvedCount} of {operations.length} operations approved)
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Review proposed category folders and filenames. You can edit any proposal inline before applying.
          </p>
        </div>

        {/* Global Select/Deselect & Validate Buttons */}
        <div className="flex items-center space-x-2">
          {hasUnsavedEdits && (
            <button
              type="button"
              onClick={onValidateEdits}
              disabled={isValidating}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white shadow-sm transition animate-pulse"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />
              <span>Validate Edits</span>
            </button>
          )}

          <button
            type="button"
            onClick={allSelected ? onDeselectAll : onSelectAll}
            className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white border border-cream-300 hover:bg-cream-100 text-slate-700 transition"
          >
            {allSelected ? (
              <>
                <Square className="w-3.5 h-3.5 text-slate-500" />
                <span>Deselect All</span>
              </>
            ) : (
              <>
                <CheckSquare className="w-3.5 h-3.5 text-forest-700" />
                <span>Select All</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Collision Alert Banner */}
      {conflictsDetected > 0 && (
        <div className="p-3.5 bg-red-50/90 border-b border-red-200 flex items-start space-x-2.5 text-xs text-red-900">
          <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <span className="font-bold">
              {conflictsDetected} Destination Conflict(s) Detected!
            </span>
            <p className="mt-0.5 text-red-800">
              Two or more files are mapped to the same target, or a target already exists on disk.
              Execution is safely blocked until conflicting destinations are edited or deselected.
            </p>
          </div>
        </div>
      )}

      {/* Diff Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-cream-200 text-left text-xs">
          <thead className="bg-cream-100/60 font-semibold text-slate-700">
            <tr>
              <th scope="col" className="py-3 pl-4 pr-2 w-10">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={allSelected ? onDeselectAll : onSelectAll}
                  className="rounded border-cream-300 text-forest-700 focus:ring-forest-500"
                  aria-label="Select all operations"
                />
              </th>
              <th scope="col" className="px-3 py-3 font-semibold">
                Original File
              </th>
              <th scope="col" className="px-2 py-3 w-8 text-center text-slate-400">
                Action
              </th>
              <th scope="col" className="px-3 py-3 font-semibold">
                Proposed Target Destination
              </th>
              <th scope="col" className="px-3 py-3 font-semibold text-right w-24">
                Controls
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cream-200 bg-white">
            {operations.map((op) => {
              const isEditing = editingOpId === op.op_id;
              const hasConflict = op.conflicts.length > 0;

              return (
                <tr
                  key={op.op_id}
                  className={`hover:bg-cream-50/60 transition ${
                    hasConflict
                      ? 'bg-red-50/40'
                      : !op.is_approved
                      ? 'opacity-50 bg-gray-50/50'
                      : ''
                  }`}
                >
                  {/* Approval Checkbox */}
                  <td className="py-3 pl-4 pr-2 align-top">
                    <input
                      type="checkbox"
                      checked={op.is_approved}
                      onChange={() => onToggleApprove(op.op_id)}
                      className="rounded border-cream-300 text-forest-700 focus:ring-forest-500 mt-1 cursor-pointer"
                      aria-label={`Approve move for ${op.source_rel_path}`}
                    />
                  </td>

                  {/* Original Source */}
                  <td className="px-3 py-3 align-top font-mono text-slate-800">
                    <div className="font-semibold">{op.source_rel_path}</div>
                  </td>

                  {/* Operation Badge */}
                  <td className="px-2 py-3 align-top text-center">
                    <div className="flex flex-col items-center space-y-1">
                      <ArrowRight className="w-3.5 h-3.5 text-forest-700 mt-0.5" />
                      {getOpBadge(op.op_type)}
                    </div>
                  </td>

                  {/* Proposed Destination / Inline Editor */}
                  <td className="px-3 py-3 align-top">
                    {isEditing ? (
                      <div className="space-y-2 p-2 bg-cream-50 rounded-lg border border-forest-300">
                        <div>
                          <label className="text-[10px] font-bold text-slate-600 flex items-center space-x-1 mb-0.5">
                            <FolderInput className="w-3 h-3 text-forest-700" />
                            <span>Category Subfolder</span>
                          </label>
                          <input
                            type="text"
                            value={editCategory}
                            onChange={(e) => setEditCategory(e.target.value)}
                            placeholder="e.g. Invoices or Documents"
                            className="w-full text-xs font-mono px-2 py-1 bg-white border border-cream-300 rounded focus:ring-1 focus:ring-forest-500"
                          />
                        </div>

                        <div>
                          <label className="text-[10px] font-bold text-slate-600 flex items-center space-x-1 mb-0.5">
                            <Tag className="w-3 h-3 text-forest-700" />
                            <span>Filename</span>
                          </label>
                          <input
                            type="text"
                            value={editFilename}
                            onChange={(e) => setEditFilename(e.target.value)}
                            className="w-full text-xs font-mono px-2 py-1 bg-white border border-cream-300 rounded focus:ring-1 focus:ring-forest-500"
                          />
                        </div>

                        <div className="flex items-center space-x-2 pt-1">
                          <button
                            type="button"
                            onClick={() => saveEdit(op.op_id)}
                            className="px-2.5 py-1 bg-forest-700 hover:bg-forest-800 text-white rounded text-[11px] font-medium"
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            onClick={cancelEdit}
                            className="px-2.5 py-1 bg-white border border-cream-300 text-slate-700 rounded text-[11px]"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <div className="font-mono text-forest-900 font-medium">
                          {op.target_rel_path}
                        </div>

                        {/* Conflicts display */}
                        {hasConflict && (
                          <div className="space-y-0.5 mt-1">
                            {op.conflicts.map((c, i) => (
                              <div
                                key={i}
                                className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-red-100 text-red-800 text-[11px] font-semibold border border-red-200"
                              >
                                <AlertTriangle className="w-3 h-3 text-red-600 flex-shrink-0" />
                                <span>{c.message}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </td>

                  {/* Actions / Edit trigger */}
                  <td className="px-3 py-3 align-top text-right">
                    {!isEditing && (
                      <button
                        type="button"
                        onClick={() => startEditing(op)}
                        className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-cream-100 hover:bg-forest-100 text-slate-700 hover:text-forest-900 text-xs transition"
                        title="Edit category or filename"
                      >
                        <Edit2 className="w-3 h-3 text-forest-700" />
                        <span>Edit</span>
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Safety Notice Footer */}
      <div className="p-3 bg-cream-50 border-t border-cream-200 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <CheckCircle2 className="w-4 h-4 text-forest-700 flex-shrink-0" />
          <span>
            Preview mode active. Files will only move after you explicitly click &ldquo;Apply Approved Changes&rdquo;.
          </span>
        </div>
      </div>
    </div>
  );
};
