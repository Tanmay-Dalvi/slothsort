import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, isDemoMode, setDemoMode } from '../services/api';
import { demoService, DEMO_SAMPLE_FILES } from '../services/demoService';

describe('Demo Mode & Safety Guard', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('DEMO_SAMPLE_FILES contains 12 realistic files', () => {
    expect(DEMO_SAMPLE_FILES).toHaveLength(12);
    expect(DEMO_SAMPLE_FILES.some((f) => f.extension === '.pdf')).toBe(true);
    expect(DEMO_SAMPLE_FILES.some((f) => f.extension === '.zip')).toBe(true);
    expect(DEMO_SAMPLE_FILES.some((f) => f.extension === '.py')).toBe(true);
  });

  it('demoService returns valid health, providers, and scan data', async () => {
    const health = await demoService.getHealth();
    expect(health.status).toBe('ok');
    expect(health.project).toContain('Demo Sandbox');

    const providers = await demoService.getProviders();
    expect(providers).toHaveLength(3);
    expect(providers.every((p) => p.is_available)).toBe(true);

    const scan = await demoService.scanFolder('/tmp/slothsort_demo');
    expect(scan.total_files).toBe(12);
    expect(scan.files).toHaveLength(12);
    expect(scan.total_bytes).toBeGreaterThan(0);
  });

  it('demoService generates realistic plans and detects collisions on validation', async () => {
    const plan = await demoService.generatePlan('/tmp/slothsort_demo', 'ollama');
    expect(plan.operations).toHaveLength(12);
    expect(plan.is_validated).toBe(true);
    expect(plan.conflicts_detected).toBe(0);

    // Create a collision intentionally
    const collidingOps = plan.operations.map((op, idx) => {
      if (idx === 1) {
        return { ...op, target_rel_path: plan.operations[0].target_rel_path };
      }
      return op;
    });

    const validated = await demoService.validatePlan(plan.plan_id, collidingOps);
    expect(validated.is_validated).toBe(false);
    expect(validated.conflicts_detected).toBeGreaterThan(0);
  });

  it('demoService executes simulated plan and records undo manifest', async () => {
    const plan = await demoService.generatePlan('/tmp/slothsort_demo', 'ollama');
    const approvedIds = plan.operations.map((o) => o.op_id);

    const execResult = await demoService.executePlan(plan.plan_id, approvedIds);
    expect(execResult.status).toBe('SUCCESS');
    expect(execResult.executed_count).toBe(12);
    expect(execResult.undo_manifest_id).toBeTruthy();

    const history = await demoService.getHistory();
    expect(history.some((m) => m.manifest_id === execResult.undo_manifest_id)).toBe(true);

    // Rollback batch
    const rollback = await demoService.rollbackBatch(execResult.undo_manifest_id!);
    expect(rollback.status).toBe('ROLLED_BACK');
    expect(rollback.restored_count).toBeGreaterThan(0);
  });

  it('api service routes to demoService and NEVER calls fetch in demo mode', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    setDemoMode(true);
    expect(isDemoMode()).toBe(true);

    const scan = await api.scanFolder('/tmp/test');
    expect(scan.total_files).toBe(12);

    const plan = await api.generatePlan('/tmp/test', 'mock');
    expect(plan.operations.length).toBe(12);

    const exec = await api.executePlan(plan.plan_id, [plan.operations[0].op_id]);
    expect(exec.executed_count).toBe(1);

    // ZERO network fetch calls must occur in demo mode!
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
