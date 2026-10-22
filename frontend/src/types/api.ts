/**
 * Strict TypeScript interfaces mirroring SlothSort backend Pydantic models.
 */

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
  default_provider: string;
}

export interface ProviderHealth {
  is_available: boolean;
  provider_name: string;
  model_name: string;
  latency_ms: number;
  error_message: string | null;
  is_cloud: boolean;
  privacy_notice: string;
}

export interface FileMetadata {
  id: string;
  original_rel_path: string;
  filename: string;
  extension: string;
  size_bytes: number;
  modified_at: string;
  is_symlink: boolean;
  is_accessible: boolean;
}

export interface SkippedFile {
  path: string;
  reason: string;
}

export interface ScanError {
  path: string;
  error_message: string;
}

export interface ScanResult {
  root_path: string;
  scanned_at: string;
  total_files: number;
  total_bytes: number;
  files: FileMetadata[];
  skipped_files: SkippedFile[];
  errors: ScanError[];
}

export type OperationType = 'MOVE' | 'RENAME' | 'MOVE_AND_RENAME' | 'KEEP';
export type OperationStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'FAILED' | 'ROLLED_BACK';

export interface ConflictNotice {
  conflict_type: string;
  message: string;
  conflicting_path: string | null;
}

export interface FileOperation {
  op_id: string;
  file_id: string;
  source_rel_path: string;
  target_rel_path: string;
  op_type: OperationType;
  status: OperationStatus;
  is_approved: boolean;
  conflicts: ConflictNotice[];
}

export interface OrganizationOptions {
  max_categories: number;
  naming_convention: 'preserve' | 'clean_snake' | 'clean_kebab';
  custom_instructions?: string | null;
}

export interface OrganizationPlan {
  plan_id: string;
  root_path: string;
  created_at: string;
  provider_used: string;
  total_files: number;
  operations: FileOperation[];
  conflicts_detected: number;
  is_validated: boolean;
  requires_approval: boolean;
}

export interface ExecutionResult {
  batch_id: string;
  plan_id: string;
  status: 'SUCCESS' | 'PARTIAL_FAILURE' | 'FAILED';
  executed_count: number;
  failed_count: number;
  undo_manifest_id: string | null;
  errors: string[];
}

export type UndoStatus = 'PENDING' | 'APPLIED' | 'ROLLED_BACK' | 'PARTIALLY_ROLLED_BACK' | 'ROLLBACK_FAILED';

export interface RollbackResult {
  manifest_id: string;
  status: UndoStatus;
  restored_count: number;
  failed_count: number;
  errors: string[];
}

export interface ExecutedStep {
  step_id: number;
  op_id: string;
  file_id: string;
  source_abs_path: string;
  target_abs_path: string;
  file_size_bytes: number;
  mtime: number;
  created_directories: string[];
  executed_at: string;
}

export interface UndoManifest {
  manifest_id: string;
  plan_id: string;
  root_path: string;
  executed_at: string;
  provider: string;
  steps: ExecutedStep[];
  status: UndoStatus;
}
