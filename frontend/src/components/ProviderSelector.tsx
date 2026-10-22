import React from 'react';
import { Cpu, Cloud, FlaskConical, AlertCircle, ShieldCheck } from 'lucide-react';
import { ProviderHealth } from '../types/api';

interface ProviderSelectorProps {
  providers: ProviderHealth[];
  selectedProviderId: string;
  onSelectProvider: (providerId: string) => void;
  isLoading: boolean;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  providers,
  selectedProviderId,
  onSelectProvider,
  isLoading,
}) => {
  // Map provider IDs to icons and descriptors
  const getProviderMeta = (provider: ProviderHealth) => {
    const nameLower = provider.provider_name.toLowerCase();
    if (nameLower.includes('ollama')) {
      return {
        id: 'ollama',
        icon: Cpu,
        title: 'Local Ollama',
        subtitle: `${provider.model_name}`,
        badge: '100% Offline & Private',
        badgeColor: 'bg-forest-50 text-forest-800 border-forest-200',
        detail: 'Inference runs entirely on your CPU/GPU. No metadata or filenames leave your laptop.',
      };
    } else if (nameLower.includes('gemini')) {
      return {
        id: 'gemini',
        icon: Cloud,
        title: 'Hosted Gemini',
        subtitle: `${provider.model_name}`,
        badge: 'Cloud API (Metadata Only)',
        badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
        detail: 'Sends filenames and file sizes over HTTPS to Google Gemini. File contents are NEVER sent.',
      };
    } else {
      return {
        id: 'mock',
        icon: FlaskConical,
        title: 'Deterministic Mock',
        subtitle: 'Rule-based heuristics',
        badge: 'Instant & Offline',
        badgeColor: 'bg-slate-100 text-slate-700 border-slate-200',
        detail: 'Fast rule-based categorization without LLM inference. Great for quick testing.',
      };
    }
  };

  const selectedProvider = providers.find((p) => {
    const meta = getProviderMeta(p);
    return meta.id === selectedProviderId;
  });

  return (
    <div className="bg-white rounded-xl p-5 border border-cream-200 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-forest-900 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-forest-700" />
            <span>AI Provider Selection</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Choose your intelligence engine. SlothSort guarantees zero silent fallback between providers.
          </p>
        </div>
      </div>

      {/* Provider Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {providers.map((p) => {
          const meta = getProviderMeta(p);
          const isSelected = meta.id === selectedProviderId;
          const isDisabled = !p.is_available && meta.id !== 'mock';

          return (
            <button
              key={meta.id}
              type="button"
              disabled={isDisabled || isLoading}
              onClick={() => onSelectProvider(meta.id)}
              className={`text-left p-3.5 rounded-xl border transition relative flex flex-col justify-between ${
                isSelected
                  ? 'border-forest-600 bg-forest-50/60 ring-2 ring-forest-500/20 shadow-sm'
                  : isDisabled
                  ? 'border-gray-200 bg-gray-50/70 opacity-60 cursor-not-allowed'
                  : 'border-cream-200 bg-white hover:border-forest-300 hover:bg-cream-50/50'
              }`}
            >
              <div>
                {/* Header row: Icon + Title + Status Pill */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center space-x-2 min-w-0">
                    <meta.icon
                      className={`w-4 h-4 shrink-0 ${
                        isSelected ? 'text-forest-700' : 'text-slate-500'
                      }`}
                    />
                    <span className="font-semibold text-sm text-slate-900 truncate">
                      {meta.title}
                    </span>
                  </div>
                  {isSelected ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 whitespace-nowrap bg-forest-600 text-white border-forest-700 shadow-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-white" />
                      Active
                    </span>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0 whitespace-nowrap ${
                        p.is_available
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-slate-100 text-slate-500 border-slate-200'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          p.is_available ? 'bg-emerald-500' : 'bg-slate-400'
                        }`}
                      />
                      {p.is_available ? 'Available' : 'Unavailable'}
                    </span>
                  )}
                </div>

                {/* Sub-row: Model info & privacy tags */}
                <div className="flex flex-wrap items-center gap-1.5 mb-2.5">
                  <span className="font-mono text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200 shrink-0">
                    {meta.subtitle}
                  </span>
                  <span
                    className={`inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0 whitespace-nowrap ${meta.badgeColor}`}
                  >
                    {meta.badge}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  {meta.detail}
                </p>
              </div>

              {p.error_message && (
                <div className="mt-3 pt-2 border-t border-gray-200 text-[11px] text-amber-700 flex items-start space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-600" />
                  <span className="line-clamp-2">{p.error_message}</span>
                </div>
              )}

              {p.is_available && p.latency_ms > 0 && (
                <div className="mt-3 pt-1 text-[11px] text-forest-700 font-medium flex items-center space-x-1">
                  <span className="text-slate-400">Response latency:</span>
                  <span className="font-semibold">~{p.latency_ms} ms</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Active Privacy Notice Banner */}
      {selectedProvider && (
        <div
          className={`p-3 rounded-lg text-xs flex items-start space-x-2.5 border ${
            selectedProvider.is_cloud
              ? 'bg-amber-50/70 border-amber-200 text-amber-900'
              : 'bg-forest-50/60 border-forest-200 text-forest-900'
          }`}
        >
          <ShieldCheck className="w-4 h-4 mt-0.5 flex-shrink-0 text-forest-700" />
          <div>
            <span className="font-semibold">Privacy Policy for this scan: </span>
            <span>{selectedProvider.privacy_notice}</span>
          </div>
        </div>
      )}
    </div>
  );
};
