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
import { demoService } from './demoService';

/**
 * Determine whether the frontend should run in safe Interactive Demo Mode.
 *
 * Rules:
 * 1. Explicit build-time or runtime environment flag (VITE_PUBLIC_DEMO_MODE="true")
 * 2. User preference saved in localStorage ('slothsort_demo_mode')
 * 3. SAFETY GUARD: If running on a public remote host (e.g. Render, Vercel, Netlify)
 *    and no custom VITE_BACKEND_URL was configured, automatically use Demo Mode
 *    to prevent making accidental cross-origin or mixed-content calls to localhost
 *    on a visitor's computer.
 */
export function isDemoMode(): boolean {
  if (typeof window === 'undefined') return false;

  // 1. Explicit environment variable
  if ((import.meta as any).env?.VITE_PUBLIC_DEMO_MODE === 'true') {
    return true;
  }

  // 2. User manual toggle
  const stored = localStorage.getItem('slothsort_demo_mode');
  if (stored === 'true') return true;
  if (stored === 'false') return false;

  // 3. Safety guard on remote domains
  const hostname = window.location.hostname;
  const isLocalhost =
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '[::1]' ||
    hostname === '';

  const explicitBackendUrl = (import.meta as any).env?.VITE_BACKEND_URL;
  if (!isLocalhost && !explicitBackendUrl) {
    return true;
  }

  return false;
}

export function setDemoMode(enabled: boolean): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('slothsort_demo_mode', enabled ? 'true' : 'false');
    window.dispatchEvent(new Event('slothsort_mode_change'));
  }
}

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
      try {
        const text = await res.text();
        if (text) errorMessage = text;
      } catch {
        // use fallback status
      }
    }
    throw new Error(errorMessage);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    if (isDemoMode()) {
      return demoService.getHealth();
    }
    const res = await fetch(`${BASE_URL}/api/health`);
    return handleResponse<HealthResponse>(res);
  },

  async getProviders(): Promise<ProviderHealth[]> {
    if (isDemoMode()) {
      return demoService.getProviders();
    }
    const res = await fetch(`${BASE_URL}/api/providers`);
    return handleResponse<ProviderHealth[]>(res);
  },

  async scanFolder(folderPath: string, maxDepth?: number): Promise<ScanResult> {
    if (isDemoMode()) {
      return demoService.scanFolder(folderPath, maxDepth);
    }
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
    if (isDemoMode()) {
      return demoService.generatePlan(folderPath, providerId, options);
    }
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
    if (isDemoMode()) {
      return demoService.validatePlan(planId, operations);
    }
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
    if (isDemoMode()) {
      return demoService.executePlan(planId, approvedOpIds);
    }
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
    if (isDemoMode()) {
      return demoService.rollbackBatch(manifestId);
    }
    const res = await fetch(`${BASE_URL}/api/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ manifest_id: manifestId }),
    });
    return handleResponse<RollbackResult>(res);
  },

  async getHistory(): Promise<UndoManifest[]> {
    if (isDemoMode()) {
      return demoService.getHistory();
    }
    const res = await fetch(`${BASE_URL}/api/history`);
    return handleResponse<UndoManifest[]>(res);
  },
};
