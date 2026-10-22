import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../components/Header';
import { ProviderSelector } from '../components/ProviderSelector';
import { ScanOverview } from '../components/ScanOverview';
import { ExecutionModal } from '../components/ExecutionModal';
import { GettingStartedGuide } from '../components/GettingStartedGuide';
import { ProviderHealth, ScanResult } from '../types/api';

describe('Frontend Component Tests', () => {
  it('Header renders branding and online status', () => {
    render(
      <Header
        isBackendConnected={true}
        historyCount={3}
        onOpenHistory={vi.fn()}
      />
    );

    expect(screen.getByText('SlothSort')).toBeTruthy();
    expect(screen.getByText('Engine Online')).toBeTruthy();
    expect(screen.getByText('3')).toBeTruthy();
  });

  it('Header shows offline indicator when backend is down', () => {
    render(
      <Header
        isBackendConnected={false}
        historyCount={0}
        onOpenHistory={vi.fn()}
      />
    );

    expect(screen.getByText('Engine Offline')).toBeTruthy();
  });

  it('ProviderSelector renders providers and calls selection handler', () => {
    const mockProviders: ProviderHealth[] = [
      {
        is_available: true,
        provider_name: 'Local Ollama',
        model_name: 'gemma3:1b',
        latency_ms: 12.5,
        error_message: null,
        is_cloud: false,
        privacy_notice: '100% Local Inference',
      },
      {
        is_available: false,
        provider_name: 'Google Gemini',
        model_name: 'gemini-2.5-flash',
        latency_ms: 0,
        error_message: 'GEMINI_API_KEY is not configured',
        is_cloud: true,
        privacy_notice: 'Cloud API',
      },
      {
        is_available: true,
        provider_name: 'Deterministic Mock',
        model_name: 'mock-rules',
        latency_ms: 0.2,
        error_message: null,
        is_cloud: false,
        privacy_notice: 'Local heuristics',
      },
    ];

    const onSelect = vi.fn();
    render(
      <ProviderSelector
        providers={mockProviders}
        selectedProviderId="ollama"
        onSelectProvider={onSelect}
        isLoading={false}
      />
    );

    expect(screen.getByText('Local Ollama')).toBeTruthy();
    expect(screen.getByText('Hosted Gemini')).toBeTruthy();

    // Click mock provider
    const mockBtn = screen.getByText('Deterministic Mock');
    fireEvent.click(mockBtn);
    expect(onSelect).toHaveBeenCalledWith('mock');
  });

  it('ScanOverview renders file statistics and formats bytes', () => {
    const mockScan: ScanResult = {
      root_path: '/home/user/Downloads',
      scanned_at: '2026-10-22T12:00:00Z',
      total_files: 5,
      total_bytes: 1048576, // 1 MB
      files: [
        {
          id: '1',
          original_rel_path: 'report.pdf',
          filename: 'report.pdf',
          extension: 'pdf',
          size_bytes: 524288,
          modified_at: '2026-10-22T00:00:00Z',
          is_symlink: false,
          is_accessible: true,
        },
      ],
      skipped_files: [],
      errors: [],
    };

    render(<ScanOverview scanResult={mockScan} />);

    expect(screen.getByText('5')).toBeTruthy();
    expect(screen.getByText('1 MB')).toBeTruthy();
    expect(screen.getByText('.pdf')).toBeTruthy();
  });

  it('ExecutionModal blocks apply button when conflicts exist', () => {
    render(
      <ExecutionModal
        approvedCount={3}
        totalCount={3}
        conflictsCount={1}
        hasUnsavedEdits={false}
        isExecuting={false}
        isPlanExecuted={false}
        executionResult={null}
        onConfirmExecute={vi.fn()}
        onUndoBatch={vi.fn()}
        isUndoing={false}
      />
    );

    const applyBtn = screen.getByRole('button', { name: /apply approved changes/i });
    expect(applyBtn.hasAttribute('disabled')).toBe(true);
    expect(screen.getByText(/Blocked: Resolve 1 destination conflict/i)).toBeTruthy();
  });

  it('ExecutionModal enables apply button when valid and approved', () => {
    const onExecute = vi.fn();
    render(
      <ExecutionModal
        approvedCount={3}
        totalCount={3}
        conflictsCount={0}
        hasUnsavedEdits={false}
        isExecuting={false}
        isPlanExecuted={false}
        executionResult={null}
        onConfirmExecute={onExecute}
        onUndoBatch={vi.fn()}
        isUndoing={false}
      />
    );

    const applyBtn = screen.getByRole('button', { name: /apply approved changes/i });
    expect(applyBtn.hasAttribute('disabled')).toBe(false);

    fireEvent.click(applyBtn);
    expect(onExecute).toHaveBeenCalled();
  });

  it('GettingStartedGuide renders 4 steps and demo button', () => {
    const onSelectDemo = vi.fn();
    const onTriggerScan = vi.fn();

    render(
      <GettingStartedGuide
        onSelectDemoPath={onSelectDemo}
        onTriggerScan={onTriggerScan}
      />
    );

    expect(screen.getByText(/How SlothSort Works/i)).toBeTruthy();
    expect(screen.getByText('Select Folder')).toBeTruthy();
    expect(screen.getByText('Scan Metadata')).toBeTruthy();
    expect(screen.getByText('AI Plan Preview')).toBeTruthy();
    expect(screen.getByText('Approve & Undo')).toBeTruthy();

    const demoBtn = screen.getByRole('button', { name: /load demo & scan/i });
    expect(demoBtn).toBeTruthy();
    fireEvent.click(demoBtn);
    expect(onSelectDemo).toHaveBeenCalledWith('/tmp/slothsort_demo');
  });
});
