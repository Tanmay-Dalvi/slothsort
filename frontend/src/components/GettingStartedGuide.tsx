import React from 'react';
import {
  FolderSearch,
  Sparkles,
  CheckCircle2,
  RotateCcw,
  ShieldCheck,
  ArrowRight,
  Play,
  Info,
} from 'lucide-react';

interface GettingStartedGuideProps {
  onSelectDemoPath: (path: string) => void;
  onTriggerScan: () => void;
  isDemo?: boolean;
}

export const GettingStartedGuide: React.FC<GettingStartedGuideProps> = ({
  onSelectDemoPath,
  onTriggerScan,
  isDemo = false,
}) => {
  const steps = [
    {
      number: '01',
      title: 'Select Folder',
      description: isDemo
        ? 'Browse simulated Downloads. SlothSort confines operations strictly to this root.'
        : 'Enter any directory path. SlothSort strictly confines operations within this root.',
      icon: FolderSearch,
    },
    {
      number: '02',
      title: 'Scan Metadata',
      description: 'Collects filenames, extensions, and timestamps. Never reads file contents or bytes.',
      icon: ShieldCheck,
    },
    {
      number: '03',
      title: 'AI Plan Preview',
      description: isDemo
        ? 'Simulated Gemma/Gemini logic proposes clean categories and sensible folder targets.'
        : 'Local Gemma 3 1B proposes neat categories and cleaner filenames without mutating disk.',
      icon: Sparkles,
    },
    {
      number: '04',
      title: 'Approve & Undo',
      description: isDemo
        ? 'Review diffs, approve operations, and simulate execution. Test 1-click rollback in memory.'
        : 'You approve every change. Every executed batch logs a full manifest for 1-click rollback.',
      icon: RotateCcw,
    },
  ];

  const handleUseDemo = () => {
    onSelectDemoPath('/tmp/slothsort_demo');
    // Give state a moment to settle, then scan
    setTimeout(() => {
      onTriggerScan();
    }, 50);
  };

  return (
    <div className="bg-white rounded-xl border border-cream-200 shadow-sm p-6 space-y-6">
      {/* Public Demo Mode Sandbox Notice */}
      {isDemo && (
        <div className="p-4 rounded-lg bg-amber-50/80 border border-amber-200 text-amber-950 text-xs flex items-start space-x-3">
          <Info className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <p className="font-bold text-amber-900">
              Interactive Public Demo Sandbox
            </p>
            <p className="text-amber-800 leading-relaxed">
              You are exploring SlothSort in a safe, simulated browser environment populated with 12 sample files.
              <strong> No real files on your computer or on any remote server are scanned or modified.</strong> SlothSort is a local-first application designed to run entirely on your own laptop with local AI models.
            </p>
          </div>
        </div>
      )}

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cream-200">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-forest-50 text-forest-800 border border-forest-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-forest-600" />
            <span>{isDemo ? 'Interactive Simulation Ready' : 'Ready to Organize'}</span>
          </div>
          <h2 className="text-lg font-bold text-forest-950">
            {isDemo
              ? 'Experience SlothSort: Safe In-Browser Simulation'
              : 'How SlothSort Works: Slow, Steady & 100% Safe'}
          </h2>
          <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
            {isDemo
              ? 'Test the full workflow: scan sample files, select an AI provider, preview proposed folder structures, edit paths, and simulate 1-click execution and undo.'
              : 'SlothSort keeps all AI processing on your device using local open-weight models. The language model only proposes changes; deterministic code validates paths, and you have final approval.'}
          </p>
        </div>

        {/* Demo Call to Action Button */}
        <div className="flex-shrink-0">
          <button
            type="button"
            onClick={handleUseDemo}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg text-xs font-bold bg-forest-800 hover:bg-forest-900 active:bg-forest-950 text-white shadow-sm transition group"
          >
            <Play className="w-3.5 h-3.5 text-forest-300 group-hover:text-white transition" />
            <span>{isDemo ? 'Scan 12 Sample Files' : 'Load Demo & Scan'}</span>
            <ArrowRight className="w-3.5 h-3.5 text-forest-300 group-hover:translate-x-0.5 transition" />
          </button>
        </div>
      </div>

      {/* 4 Steps Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <div
              key={step.number}
              className="p-4 rounded-xl bg-cream-50/70 border border-cream-200 space-y-2 hover:border-forest-300 transition"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-forest-600 bg-forest-100/60 px-1.5 py-0.5 rounded border border-forest-200">
                  STEP {step.number}
                </span>
                <Icon className="w-4 h-4 text-forest-700" />
              </div>
              <h3 className="text-xs font-bold text-slate-900 pt-1">
                {step.title}
              </h3>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                {step.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
