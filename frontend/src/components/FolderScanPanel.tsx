import React, { useState } from 'react';
import { Folder, Search, Loader2, Sparkles, AlertTriangle, Info } from 'lucide-react';
import { OrganizationOptions } from '../types/api';

interface FolderScanPanelProps {
  folderPath: string;
  onFolderPathChange: (path: string) => void;
  onScan: () => void;
  onGeneratePlan: (options: OrganizationOptions) => void;
  isScanning: boolean;
  isGeneratingPlan: boolean;
  hasScanResults: boolean;
  errorMessage: string | null;
}

export const FolderScanPanel: React.FC<FolderScanPanelProps> = ({
  folderPath,
  onFolderPathChange,
  onScan,
  onGeneratePlan,
  isScanning,
  isGeneratingPlan,
  hasScanResults,
  errorMessage,
}) => {
  const [maxCategories, setMaxCategories] = useState<number>(6);
  const [namingConvention, setNamingConvention] = useState<'preserve' | 'clean_snake' | 'clean_kebab'>('preserve');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Quick preset helper paths
  const presets = [
    { label: 'Demo Folder (/tmp)', path: '/tmp/slothsort_demo' },
    { label: 'Test Scratch (/tmp)', path: '/tmp/slothsort_test' },
  ];

  const handleApplyPreset = (path: string) => {
    onFolderPathChange(path);
  };

  const handleGenerate = () => {
    onGeneratePlan({
      max_categories: maxCategories,
      naming_convention: namingConvention,
      custom_instructions: customInstructions.trim() || null,
    });
  };

  return (
    <div className="bg-white rounded-xl p-5 border border-cream-200 shadow-sm space-y-4">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-forest-900 flex items-center space-x-2">
          <Folder className="w-4 h-4 text-forest-700" />
          <span>Folder to Organize</span>
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Enter an absolute folder path. The local SlothSort engine performs the scan securely.
        </p>
      </div>

      {/* Path Input Form */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <Folder className="h-4 w-4 text-forest-700" />
            </div>
            <input
              type="text"
              value={folderPath}
              onChange={(e) => onFolderPathChange(e.target.value)}
              placeholder="/home/user/Downloads"
              className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-cream-50/50 border border-cream-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent font-mono"
            />
          </div>

          <button
            type="button"
            onClick={onScan}
            disabled={isScanning || !folderPath.trim()}
            className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg bg-forest-800 text-white font-medium text-sm hover:bg-forest-900 active:bg-forest-950 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-sm"
          >
            {isScanning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-forest-200" />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Scan Folder</span>
              </>
            )}
          </button>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span className="font-medium">Presets:</span>
          {presets.map((p) => (
            <button
              key={p.path}
              type="button"
              onClick={() => handleApplyPreset(p.path)}
              className="px-2.5 py-1 rounded-md bg-cream-100 hover:bg-forest-100 text-forest-800 border border-cream-200 hover:border-forest-300 transition text-[11px] font-mono"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Folder Security Policy Disclosure */}
      <div className="p-3 bg-cream-50 rounded-lg border border-cream-200 text-xs text-slate-600 space-y-1">
        <div className="flex items-center space-x-1.5 font-semibold text-forest-900">
          <Info className="w-3.5 h-3.5 text-forest-700" />
          <span>Security & Authorization Policy</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-500">
          Under backend security constraints, scanning is permitted strictly within authorized user trees (User Home and /tmp). System roots (e.g., <code className="bg-cream-200 px-1 py-0.5 rounded text-slate-800">/etc</code>, <code className="bg-cream-200 px-1 py-0.5 rounded text-slate-800">/root</code>) and symbolic link roots are strictly prohibited.
        </p>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <span className="font-semibold">Scan Error: </span>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Advanced Options Accordion */}
      {hasScanResults && (
        <div className="pt-3 border-t border-cream-200 space-y-3">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-forest-800 font-semibold hover:text-forest-900 flex items-center space-x-1"
          >
            <span>{showAdvanced ? '▾ Hide Organization Options' : '▸ Show Organization Options'}</span>
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 p-3.5 bg-cream-50/50 rounded-lg border border-cream-200">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Naming Convention
                </label>
                <select
                  value={namingConvention}
                  onChange={(e) => setNamingConvention(e.target.value as any)}
                  className="w-full text-xs bg-white border border-cream-300 rounded-md py-1.5 px-2.5 text-slate-800 focus:ring-1 focus:ring-forest-500"
                >
                  <option value="preserve">Preserve Original Filenames</option>
                  <option value="clean_snake">clean_snake_case.ext</option>
                  <option value="clean_kebab">clean-kebab-case.ext</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Max Category Folders ({maxCategories})
                </label>
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={maxCategories}
                  onChange={(e) => setMaxCategories(parseInt(e.target.value, 10))}
                  className="w-full accent-forest-700"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Custom Guidance (Optional)
                </label>
                <input
                  type="text"
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  placeholder="e.g. Group receipts into Finance, cluster photos by year"
                  className="w-full text-xs bg-white border border-cream-300 rounded-md py-1.5 px-2.5 text-slate-800 placeholder-slate-400"
                />
              </div>
            </div>
          )}

          {/* Action Trigger for Plan Generation */}
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={isGeneratingPlan || isScanning}
              className="inline-flex items-center space-x-2 px-5 py-2 rounded-lg bg-forest-700 text-white font-medium text-sm hover:bg-forest-800 active:bg-forest-900 disabled:opacity-50 transition shadow-sm"
            >
              {isGeneratingPlan ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-forest-200" />
                  <span>Analyzing with AI...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-forest-300" />
                  <span>Generate Organization Plan</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
