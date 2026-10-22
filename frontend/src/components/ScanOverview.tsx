import React from 'react';
import { Files, HardDrive, FileType, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { ScanResult } from '../types/api';

interface ScanOverviewProps {
  scanResult: ScanResult;
}

export const ScanOverview: React.FC<ScanOverviewProps> = ({ scanResult }) => {
  const [showSkipped, setShowSkipped] = React.useState(false);

  // Format bytes helper
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Group files by extension
  const extensionCounts: { [ext: string]: number } = {};
  for (const f of scanResult.files) {
    const ext = f.extension || 'no-ext';
    extensionCounts[ext] = (extensionCounts[ext] || 0) + 1;
  }

  // Sort extensions by frequency
  const sortedExtensions = Object.entries(extensionCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  return (
    <div className="bg-white rounded-xl p-5 border border-cream-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-forest-900">
            Scanned Contents Overview
          </h2>
          <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-xl">
            {scanResult.root_path}
          </p>
        </div>
        <span className="text-xs text-slate-400">
          {new Date(scanResult.scanned_at).toLocaleTimeString()}
        </span>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-cream-50 rounded-lg border border-cream-200">
          <div className="flex items-center space-x-2 text-forest-700 mb-1">
            <Files className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Discovered Files</span>
          </div>
          <span className="text-2xl font-bold text-slate-900 font-mono">
            {scanResult.total_files}
          </span>
        </div>

        <div className="p-3 bg-cream-50 rounded-lg border border-cream-200">
          <div className="flex items-center space-x-2 text-forest-700 mb-1">
            <HardDrive className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Total Size</span>
          </div>
          <span className="text-2xl font-bold text-slate-900 font-mono">
            {formatBytes(scanResult.total_bytes)}
          </span>
        </div>

        <div className="p-3 bg-cream-50 rounded-lg border border-cream-200">
          <div className="flex items-center space-x-2 text-forest-700 mb-1">
            <FileType className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">File Types</span>
          </div>
          <span className="text-2xl font-bold text-slate-900 font-mono">
            {Object.keys(extensionCounts).length}
          </span>
        </div>

        <div className="p-3 bg-cream-50 rounded-lg border border-cream-200">
          <div className="flex items-center space-x-2 text-slate-600 mb-1">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">Skipped Items</span>
          </div>
          <span className="text-2xl font-bold text-slate-700 font-mono">
            {scanResult.skipped_files.length + scanResult.errors.length}
          </span>
        </div>
      </div>

      {/* Extension Badges */}
      {sortedExtensions.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-600">File Formats Detected:</span>
          <div className="flex flex-wrap gap-1.5">
            {sortedExtensions.map(([ext, count]) => (
              <span
                key={ext}
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs bg-forest-50 text-forest-900 border border-forest-200 font-mono"
              >
                <span className="font-bold">.{ext}</span>
                <span className="text-[10px] bg-forest-200/80 px-1.5 py-0.2 rounded-full font-sans">
                  {count}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Skipped Items Accordion */}
      {(scanResult.skipped_files.length > 0 || scanResult.errors.length > 0) && (
        <div className="border-t border-cream-200 pt-3">
          <button
            type="button"
            onClick={() => setShowSkipped(!showSkipped)}
            className="w-full flex items-center justify-between text-xs text-slate-600 hover:text-slate-900 font-medium py-1"
          >
            <span className="flex items-center space-x-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>
                {scanResult.skipped_files.length} items skipped for safety (symlinks / system dirs)
                {scanResult.errors.length > 0 && ` • ${scanResult.errors.length} filesystem errors`}
              </span>
            </span>
            {showSkipped ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showSkipped && (
            <div className="mt-2 max-h-40 overflow-y-auto space-y-1 p-2 bg-cream-50 rounded border border-cream-200 text-xs font-mono">
              {scanResult.skipped_files.map((s, idx) => (
                <div key={idx} className="flex justify-between text-slate-600 text-[11px]">
                  <span className="truncate max-w-sm">{s.path}</span>
                  <span className="text-amber-700 italic flex-shrink-0">{s.reason}</span>
                </div>
              ))}
              {scanResult.errors.map((e, idx) => (
                <div key={idx} className="flex justify-between text-red-600 text-[11px]">
                  <span className="truncate max-w-sm">{e.path}</span>
                  <span className="font-semibold flex-shrink-0">{e.error_message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
