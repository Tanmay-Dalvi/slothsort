import {
  ExecutionResult,
  FileOperation,
  HealthResponse,
  OrganizationOptions,
  OrganizationPlan,
  ProviderHealth,
  RollbackResult,
  ScanResult,
  UndoManifest,
} from '../types/api';

const BASE_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
        }
      }
    } catch {
      // Fallback to text or generic status
      try {
        const text = await res.text();
        if (text) errorMessage = text;
      } catch {
        // use status text
      }
    }
    throw new Error(errorMessage);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${BASE_URL}/api/health`);
    return handleResponse<HealthResponse>(res);
  },

  async getProviders(): Promise<ProviderHealth[]> {
    const res = await fetch(`${BASE_URL}/api/providers`);
    return handleResponse<ProviderHealth[]>(res);
  },

  async scanFolder(folderPath: string, maxDepth?: number): Promise<ScanResult> {
    const res = await fetch(`${BASE_URL}/api/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_path: folderPath,
        max_depth: maxDepth,
      }),
    });
    return handleResponse<ScanResult>(res);
  },

  async generatePlan(
    folderPath: string,
    providerId: string,
    options?: OrganizationOptions
  ): Promise<OrganizationPlan> {
    const res = await fetch(`${BASE_URL}/api/plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_path: folderPath,
        provider_id: providerId,
        options: options || { max_categories: 6, naming_convention: 'preserve' },
      }),
    });
    return handleResponse<OrganizationPlan>(res);
  },

  async validatePlan(
    planId: string,
    operations: FileOperation[]
  ): Promise<OrganizationPlan> {
    const res = await fetch(`${BASE_URL}/api/plan/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan_id: planId,
        operations,
      }),
    });
    return handleResponse<OrganizationPlan>(res);
  },

  async executePlan(
    planId: string,
    approvedOpIds: string[]
  ): Promise<ExecutionResult> {
    const res = await fetch(`${BASE_URL}/api/plan/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan_id: planId,
        approved_op_ids: approvedOpIds,
      }),
    });
    return handleResponse<ExecutionResult>(res);
  },

  async rollbackBatch(manifestId: string): Promise<RollbackResult> {
    const res = await fetch(`${BASE_URL}/api/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ manifest_id: manifestId }),
    });
    return handleResponse<RollbackResult>(res);
  },

  async getHistory(): Promise<UndoManifest[]> {
    const res = await fetch(`${BASE_URL}/api/history`);
    return handleResponse<UndoManifest[]>(res);
  },
};
