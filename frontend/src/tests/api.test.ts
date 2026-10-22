import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';

describe('Frontend API Client Service', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getHealth returns health status on success', async () => {
    const mockHealth = {
      status: 'ok',
      project: 'SlothSort',
      version: '0.1.0',
      default_provider: 'ollama',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await api.getHealth();
    expect(result.status).toBe('ok');
    expect(result.project).toBe('SlothSort');
  });

  it('scanFolder sends folder_path and parses ScanResult', async () => {
    const mockScanResult = {
      root_path: '/home/user/Downloads',
      scanned_at: '2026-10-22T10:00:00Z',
      total_files: 2,
      total_bytes: 4096,
      files: [],
      skipped_files: [],
      errors: [],
    };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockScanResult,
    } as Response);

    const result = await api.scanFolder('/home/user/Downloads', 5);
    expect(result.total_files).toBe(2);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/scan'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          folder_path: '/home/user/Downloads',
          max_depth: 5,
        }),
      })
    );
  });

  it('handles backend error with detail string', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      json: async () => ({ detail: 'Access denied: protected system path' }),
    } as Response);

    await expect(api.scanFolder('/etc')).rejects.toThrow(
      'Access denied: protected system path'
    );
  });

  it('handles backend error with validation detail array', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({
        detail: [{ msg: 'Field required: folder_path' }],
      }),
    } as Response);

    await expect(api.scanFolder('')).rejects.toThrow(
      'Field required: folder_path'
    );
  });

  it('executePlan sends approved operation IDs only', async () => {
    const mockExecution = {
      batch_id: 'batch_123',
      plan_id: 'plan_abc',
      status: 'SUCCESS',
      executed_count: 3,
      failed_count: 0,
      undo_manifest_id: 'man_123',
      errors: [],
    };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockExecution,
    } as Response);

    const res = await api.executePlan('plan_abc', ['op_1', 'op_2']);
    expect(res.status).toBe('SUCCESS');
    expect(res.executed_count).toBe(3);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/plan/execute'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          plan_id: 'plan_abc',
          approved_op_ids: ['op_1', 'op_2'],
        }),
      })
    );
  });
});
