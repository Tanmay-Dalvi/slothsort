/**
 * Safe, in-memory Interactive Demo Service for public previews (e.g. Render).
 *
 * Simulates the complete SlothSort workflow without making any network requests
 * to localhost and without touching any real files on disk.
 */

import {
  ExecutionResult,
  FileMetadata,
  FileOperation,
  HealthResponse,
  OrganizationOptions,
  OrganizationPlan,
  ProviderHealth,
  RollbackResult,
  ScanResult,
  UndoManifest,
} from '../types/api';

export const DEMO_SAMPLE_FILES: FileMetadata[] = [
  {
    id: 'demo_f01',
    original_rel_path: 'october_financial_statement.pdf',
    filename: 'october_financial_statement.pdf',
    extension: '.pdf',
    size_bytes: 245760,
    modified_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f02',
    original_rel_path: 'client_assets_archive_2026.zip',
    filename: 'client_assets_archive_2026.zip',
    extension: '.zip',
    size_bytes: 14500000,
    modified_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f03',
    original_rel_path: 'raw_telemetry_dump_october.tar.gz',
    filename: 'raw_telemetry_dump_october.tar.gz',
    extension: '.tar.gz',
    size_bytes: 8700000,
    modified_at: new Date(Date.now() - 86400000 * 8).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f04',
    original_rel_path: 'device_firmware_driver_v4.bin',
    filename: 'device_firmware_driver_v4.bin',
    extension: '.bin',
    size_bytes: 4194304,
    modified_at: new Date(Date.now() - 86400000 * 12).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f05',
    original_rel_path: 'app_performance_benchmark.py',
    filename: 'app_performance_benchmark.py',
    extension: '.py',
    size_bytes: 12288,
    modified_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f06',
    original_rel_path: 'quarterly_roadmap_v2.docx',
    filename: 'quarterly_roadmap_v2.docx',
    extension: '.docx',
    size_bytes: 184320,
    modified_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f07',
    original_rel_path: 'team_retrospective_meeting.m4a',
    filename: 'team_retrospective_meeting.m4a',
    extension: '.m4a',
    size_bytes: 19800000,
    modified_at: new Date(Date.now() - 86400000 * 4).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f08',
    original_rel_path: 'architecture_diagram_draft.png',
    filename: 'architecture_diagram_draft.png',
    extension: '.png',
    size_bytes: 1245000,
    modified_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f09',
    original_rel_path: 'product_launch_deck_final.pptx',
    filename: 'product_launch_deck_final.pptx',
    extension: '.pptx',
    size_bytes: 5242880,
    modified_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f10',
    original_rel_path: 'database_migration_v3.sql',
    filename: 'database_migration_v3.sql',
    extension: '.sql',
    size_bytes: 32768,
    modified_at: new Date(Date.now() - 86400000 * 6).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f11',
    original_rel_path: 'website_redesign_preview.jpg',
    filename: 'website_redesign_preview.jpg',
    extension: '.jpg',
    size_bytes: 845000,
    modified_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
  {
    id: 'demo_f12',
    original_rel_path: 'vendor_contract_amendment.pdf',
    filename: 'vendor_contract_amendment.pdf',
    extension: '.pdf',
    size_bytes: 312000,
    modified_at: new Date(Date.now() - 86400000 * 10).toISOString(),
    is_symlink: false,
    is_accessible: true,
  },
];

const INITIAL_DEMO_MANIFESTS: UndoManifest[] = [
  {
    manifest_id: 'manifest_demo_sample_batch',
    plan_id: 'plan_demo_initial',
    root_path: '/tmp/slothsort_demo',
    executed_at: new Date(Date.now() - 3600000 * 3).toISOString(),
    provider: 'ollama (Gemma 3 1B)',
    status: 'APPLIED',
    steps: [
      {
        step_id: 1,
        op_id: 'op_sample_1',
        file_id: 'demo_f01',
        source_abs_path: '/tmp/slothsort_demo/october_financial_statement.pdf',
        target_abs_path: '/tmp/slothsort_demo/Documents/october_financial_statement.pdf',
        file_size_bytes: 245760,
        mtime: 1729600000,
        created_directories: ['/tmp/slothsort_demo/Documents'],
        executed_at: new Date(Date.now() - 3600000 * 3).toISOString(),
      },
      {
        step_id: 2,
        op_id: 'op_sample_2',
        file_id: 'demo_f02',
        source_abs_path: '/tmp/slothsort_demo/client_assets_archive_2026.zip',
        target_abs_path: '/tmp/slothsort_demo/Archives/client_assets_archive_2026.zip',
        file_size_bytes: 14500000,
        mtime: 1729600000,
        created_directories: ['/tmp/slothsort_demo/Archives'],
        executed_at: new Date(Date.now() - 3600000 * 3).toISOString(),
      },
    ],
  },
];

const STORAGE_KEY_MANIFESTS = 'slothsort_demo_manifests';

function loadStoredManifests(): UndoManifest[] {
  if (typeof window === 'undefined') return INITIAL_DEMO_MANIFESTS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY_MANIFESTS);
    if (!raw) return INITIAL_DEMO_MANIFESTS;
    return JSON.parse(raw);
  } catch {
    return INITIAL_DEMO_MANIFESTS;
  }
}

function saveStoredManifests(manifests: UndoManifest[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY_MANIFESTS, JSON.stringify(manifests));
  } catch {
    // Ignore storage quota errors
  }
}

export const demoService = {
  async getHealth(): Promise<HealthResponse> {
    await new Promise((r) => setTimeout(r, 60));
    return {
      status: 'ok',
      project: 'SlothSort (Interactive Demo Sandbox)',
      version: '0.1.0-demo',
      default_provider: 'ollama',
    };
  },

  async getProviders(): Promise<ProviderHealth[]> {
    await new Promise((r) => setTimeout(r, 80));
    return [
      {
        is_available: true,
        provider_name: 'Deterministic Mock',
        model_name: 'deterministic-rules-v1',
        latency_ms: 0.5,
        error_message: null,
        is_cloud: false,
        privacy_notice: '100% Local Heuristics (Browser Demo Sandbox)',
      },
      {
        is_available: true,
        provider_name: 'Local Ollama',
        model_name: 'gemma3:1b',
        latency_ms: 26.4,
        error_message: null,
        is_cloud: false,
        privacy_notice: '100% Offline Local Engine (Simulated responses in demo)',
      },
      {
        is_available: true,
        provider_name: 'Google Gemini',
        model_name: 'gemini-2.5-flash',
        latency_ms: 210.8,
        error_message: null,
        is_cloud: true,
        privacy_notice: 'Cloud AI API simulation (No network requests sent)',
      },
    ];
  },

  async scanFolder(folderPath: string, _maxDepth?: number): Promise<ScanResult> {
    await new Promise((r) => setTimeout(r, 220));
    const totalBytes = DEMO_SAMPLE_FILES.reduce((acc, f) => acc + f.size_bytes, 0);
    return {
      root_path: folderPath || '/tmp/slothsort_demo',
      scanned_at: new Date().toISOString(),
      total_files: DEMO_SAMPLE_FILES.length,
      total_bytes: totalBytes,
      files: DEMO_SAMPLE_FILES,
      skipped_files: [],
      errors: [],
    };
  },

  async generatePlan(
    folderPath: string,
    providerId: string,
    _options?: OrganizationOptions
  ): Promise<OrganizationPlan> {
    await new Promise((r) => setTimeout(r, 450));
    const normalizedProvider = providerId.toLowerCase();

    // Map files to realistic target categories
    const operations: FileOperation[] = DEMO_SAMPLE_FILES.map((f, idx) => {
      let targetFolder = 'Miscellaneous';
      const ext = f.extension.toLowerCase();

      if (['.pdf', '.docx', '.pptx', '.txt', '.xlsx'].includes(ext)) {
        targetFolder = 'Documents';
      } else if (['.zip', '.tar.gz', '.tar', '.gz', '.7z'].includes(ext)) {
        targetFolder = 'Archives';
      } else if (['.py', '.sql', '.bin', '.sh', '.ts', '.js'].includes(ext)) {
        targetFolder = 'Code';
      } else if (['.png', '.jpg', '.jpeg', '.svg', '.gif'].includes(ext)) {
        targetFolder = 'Images';
      } else if (['.m4a', '.mp3', '.mp4', '.wav'].includes(ext)) {
        targetFolder = 'Media';
      }

      return {
        op_id: `op_demo_${idx + 1}_${Math.random().toString(36).substring(2, 7)}`,
        file_id: f.id,
        source_rel_path: f.original_rel_path,
        target_rel_path: `${targetFolder}/${f.filename}`,
        op_type: 'MOVE',
        status: 'PENDING',
        is_approved: true,
        conflicts: [],
      };
    });

    return {
      plan_id: `plan_demo_${Date.now()}`,
      root_path: folderPath || '/tmp/slothsort_demo',
      created_at: new Date().toISOString(),
      provider_used: normalizedProvider,
      total_files: operations.length,
      operations,
      conflicts_detected: 0,
      is_validated: true,
      requires_approval: true,
    };
  },

  async validatePlan(
    planId: string,
    operations: FileOperation[]
  ): Promise<OrganizationPlan> {
    await new Promise((r) => setTimeout(r, 120));

    // Check for target collisions
    const targetMap = new Map<string, string[]>();
    for (const op of operations) {
      if (op.is_approved) {
        const clean = op.target_rel_path.trim().toLowerCase();
        const existing = targetMap.get(clean) || [];
        existing.push(op.op_id);
        targetMap.set(clean, existing);
      }
    }

    let conflictsCount = 0;
    const validatedOps = operations.map((op) => {
      const clean = op.target_rel_path.trim().toLowerCase();
      const shared = targetMap.get(clean) || [];
      const conflicts = [];
      if (shared.length > 1) {
        conflictsCount++;
        conflicts.push({
          conflict_type: 'COLLISION',
          message: `Target destination collision: multiple files mapped to ${op.target_rel_path}`,
          conflicting_path: op.target_rel_path,
        });
      }
      return {
        ...op,
        conflicts,
      };
    });

    return {
      plan_id: planId,
      root_path: '/tmp/slothsort_demo',
      created_at: new Date().toISOString(),
      provider_used: 'interactive-demo',
      total_files: operations.length,
      operations: validatedOps,
      conflicts_detected: conflictsCount,
      is_validated: conflictsCount === 0,
      requires_approval: true,
    };
  },

  async executePlan(
    planId: string,
    approvedOpIds: string[]
  ): Promise<ExecutionResult> {
    await new Promise((r) => setTimeout(r, 380));

    const manifestId = `manifest_demo_${Date.now()}`;
    const executedOps = DEMO_SAMPLE_FILES.slice(0, approvedOpIds.length);

    const steps = executedOps.map((f, idx) => ({
      step_id: idx + 1,
      op_id: approvedOpIds[idx] || `op_exec_${idx}`,
      file_id: f.id,
      source_abs_path: `/tmp/slothsort_demo/${f.filename}`,
      target_abs_path: `/tmp/slothsort_demo/Organized/${f.filename}`,
      file_size_bytes: f.size_bytes,
      mtime: Math.floor(Date.now() / 1000),
      created_directories: ['/tmp/slothsort_demo/Organized'],
      executed_at: new Date().toISOString(),
    }));

    const newManifest: UndoManifest = {
      manifest_id: manifestId,
      plan_id: planId,
      root_path: '/tmp/slothsort_demo',
      executed_at: new Date().toISOString(),
      provider: 'Interactive Demo Sandbox',
      status: 'APPLIED',
      steps,
    };

    const current = loadStoredManifests();
    saveStoredManifests([newManifest, ...current]);

    return {
      batch_id: `batch_demo_${Date.now()}`,
      plan_id: planId,
      status: 'SUCCESS',
      executed_count: approvedOpIds.length,
      failed_count: 0,
      undo_manifest_id: manifestId,
      errors: [],
    };
  },

  async rollbackBatch(manifestId: string): Promise<RollbackResult> {
    await new Promise((r) => setTimeout(r, 260));

    const current = loadStoredManifests();
    const target = current.find((m) => m.manifest_id === manifestId);
    const restoredCount = target ? target.steps.length : 1;

    const updated = current.map((m) => {
      if (m.manifest_id === manifestId) {
        return { ...m, status: 'ROLLED_BACK' as const };
      }
      return m;
    });
    saveStoredManifests(updated);

    return {
      manifest_id: manifestId,
      status: 'ROLLED_BACK',
      restored_count: restoredCount,
      failed_count: 0,
      errors: [],
    };
  },

  async getHistory(): Promise<UndoManifest[]> {
    await new Promise((r) => setTimeout(r, 90));
    return loadStoredManifests();
  },
};
