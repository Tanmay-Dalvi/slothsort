import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ProviderSelector } from './components/ProviderSelector';
import { FolderScanPanel } from './components/FolderScanPanel';
import { ScanOverview } from './components/ScanOverview';
import { PlanDiffTable } from './components/PlanDiffTable';
import { ExecutionModal } from './components/ExecutionModal';
import { UndoHistoryDrawer } from './components/UndoHistoryDrawer';
import { api } from './services/api';
import {
  ExecutionResult,
  FileOperation,
  OrganizationOptions,
  OrganizationPlan,
  ProviderHealth,
  RollbackResult,
  ScanResult,
  UndoManifest,
} from './types/api';
import { AlertCircle, X } from 'lucide-react';

export function App() {
  // Connectivity & Providers
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string>('ollama');

  // Scanning & Folder State
  const [folderPath, setFolderPath] = useState<string>('/tmp/slothsort_demo');
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);

  // Planning State
  const [organizationPlan, setOrganizationPlan] = useState<OrganizationPlan | null>(null);
  const [hasUnsavedEdits, setHasUnsavedEdits] = useState<boolean>(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Execution & Rollback State
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [isPlanExecuted, setIsPlanExecuted] = useState<boolean>(false);
  const [historyManifests, setHistoryManifests] = useState<UndoManifest[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [lastRollbackResult, setLastRollbackResult] = useState<RollbackResult | null>(null);

  // Loading States
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState<boolean>(false);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [isRollingBack, setIsRollingBack] = useState<boolean>(false);
  const [activeRollingBackId, setActiveRollingBackId] = useState<string | null>(null);

  // 1. Initial Load: Check health, providers, and previous history
  const loadInitialData = useCallback(async () => {
    try {
      const health = await api.getHealth();
      setIsBackendConnected(health.status === 'ok');

      const providerList = await api.getProviders();
      setProviders(providerList);

      // Default to Ollama if available, otherwise mock
      const ollama = providerList.find((p) => p.provider_name.toLowerCase().includes('ollama'));
      if (ollama && ollama.is_available) {
        setSelectedProviderId('ollama');
      } else {
        setSelectedProviderId('mock');
      }

      const history = await api.getHistory();
      setHistoryManifests(history);
    } catch {
      setIsBackendConnected(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Refresh history records
  const handleRefreshHistory = async () => {
    try {
      const history = await api.getHistory();
      setHistoryManifests(history);
    } catch (err: any) {
      setGeneralError(`Failed to refresh history: ${err.message}`);
    }
  };

  // 2. Scan Folder Action
  const handleScan = async () => {
    if (!folderPath.trim()) return;
    setIsScanning(true);
    setScanError(null);
    setOrganizationPlan(null);
    setExecutionResult(null);
    setIsPlanExecuted(false);
    setHasUnsavedEdits(false);

    try {
      const result = await api.scanFolder(folderPath.trim());
      setScanResult(result);
    } catch (err: any) {
      setScanError(err.message);
      setScanResult(null);
    } finally {
      setIsScanning(false);
    }
  };

  // 3. Generate Plan Action
  const handleGeneratePlan = async (options: OrganizationOptions) => {
    if (!folderPath.trim()) return;
    setIsGeneratingPlan(true);
    setGeneralError(null);
    setExecutionResult(null);
    setIsPlanExecuted(false);
    setHasUnsavedEdits(false);

    try {
      const plan = await api.generatePlan(folderPath.trim(), selectedProviderId, options);
      setOrganizationPlan(plan);
    } catch (err: any) {
      setGeneralError(`Failed to generate organization plan: ${err.message}`);
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  // 4. Toggle operation approval
  const handleToggleApprove = (opId: string) => {
    if (!organizationPlan || isPlanExecuted) return;
    const updatedOps = organizationPlan.operations.map((op) =>
      op.op_id === opId ? { ...op, is_approved: !op.is_approved } : op
    );
    setOrganizationPlan({
      ...organizationPlan,
      operations: updatedOps,
    });
  };

  // 5. Select All / Deselect All
  const handleSelectAll = () => {
    if (!organizationPlan || isPlanExecuted) return;
    const updatedOps = organizationPlan.operations.map((op) => ({ ...op, is_approved: true }));
    setOrganizationPlan({ ...organizationPlan, operations: updatedOps });
  };

  const handleDeselectAll = () => {
    if (!organizationPlan || isPlanExecuted) return;
    const updatedOps = organizationPlan.operations.map((op) => ({ ...op, is_approved: false }));
    setOrganizationPlan({ ...organizationPlan, operations: updatedOps });
  };

  // 6. Edit operation category or filename
  const handleEditOperation = (opId: string, newCategory: string, newFilename: string) => {
    if (!organizationPlan || isPlanExecuted) return;

    let targetRel = newFilename;
    if (newCategory && newCategory !== '.') {
      targetRel = `${newCategory.replace(/^\/+|\/+$/g, '')}/${newFilename}`;
    }

    const updatedOps: FileOperation[] = organizationPlan.operations.map((op) => {
      if (op.op_id === opId) {
        return {
          ...op,
          target_rel_path: targetRel,
          op_type: (op.source_rel_path === targetRel ? 'KEEP' : 'MOVE') as any,
        };
      }
      return op;
    });

    setOrganizationPlan({
      ...organizationPlan,
      operations: updatedOps,
    });
    setHasUnsavedEdits(true);
  };

  // 7. Validate edits with backend
  const handleValidateEdits = async () => {
    if (!organizationPlan || !hasUnsavedEdits) return;
    setIsValidating(true);
    setGeneralError(null);

    try {
      const updatedPlan = await api.validatePlan(
        organizationPlan.plan_id,
        organizationPlan.operations
      );
      setOrganizationPlan(updatedPlan);
      setHasUnsavedEdits(false);
    } catch (err: any) {
      setGeneralError(`Validation failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  // 8. Execute approved operations
  const handleExecute = async () => {
    if (!organizationPlan || isPlanExecuted) return;

    const approvedIds = organizationPlan.operations
      .filter((op) => op.is_approved)
      .map((op) => op.op_id);

    if (approvedIds.length === 0) {
      setGeneralError('No files selected for organization.');
      return;
    }

    setIsExecuting(true);
    setGeneralError(null);

    try {
      const result = await api.executePlan(organizationPlan.plan_id, approvedIds);
      setExecutionResult(result);
      setIsPlanExecuted(true);

      // Refresh history records after execution
      await handleRefreshHistory();
    } catch (err: any) {
      setGeneralError(`Execution failed: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  // 9. Rollback batch by manifest ID
  const handleRollback = async (manifestId: string) => {
    setIsRollingBack(true);
    setActiveRollingBackId(manifestId);
    setGeneralError(null);

    try {
      const result = await api.rollbackBatch(manifestId);
      setLastRollbackResult(result);
      await handleRefreshHistory();

      // If we just rolled back the active batch, update local state
      if (executionResult?.undo_manifest_id === manifestId) {
        setExecutionResult(null);
        setIsPlanExecuted(false);
      }
    } catch (err: any) {
      setGeneralError(`Undo failed: ${err.message}`);
    } finally {
      setIsRollingBack(false);
      setActiveRollingBackId(null);
    }
  };

  const approvedCount = organizationPlan
    ? organizationPlan.operations.filter((op) => op.is_approved).length
    : 0;
  const conflictsCount = organizationPlan ? organizationPlan.conflicts_detected : 0;

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col font-sans">
      <Header
        isBackendConnected={isBackendConnected}
        historyCount={historyManifests.length}
        onOpenHistory={() => setIsHistoryOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Global Error Banner */}
        {generalError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-900 flex items-start justify-between shadow-sm">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
              <span>{generalError}</span>
            </div>
            <button
              onClick={() => setGeneralError(null)}
              className="text-red-500 hover:text-red-800"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Top Grid: Providers & Folder Scan */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6 space-y-6">
            <ProviderSelector
              providers={providers}
              selectedProviderId={selectedProviderId}
              onSelectProvider={setSelectedProviderId}
              isLoading={isGeneratingPlan || isScanning}
            />
          </div>

          <div className="lg:col-span-6 space-y-6">
            <FolderScanPanel
              folderPath={folderPath}
              onFolderPathChange={setFolderPath}
              onScan={handleScan}
              onGeneratePlan={handleGeneratePlan}
              isScanning={isScanning}
              isGeneratingPlan={isGeneratingPlan}
              hasScanResults={scanResult !== null}
              errorMessage={scanError}
            />
          </div>
        </div>

        {/* Scan Overview Stats */}
        {scanResult && <ScanOverview scanResult={scanResult} />}

        {/* Plan Diff Table */}
        {organizationPlan && (
          <PlanDiffTable
            operations={organizationPlan.operations}
            conflictsDetected={conflictsCount}
            hasUnsavedEdits={hasUnsavedEdits}
            isValidating={isValidating}
            onToggleApprove={handleToggleApprove}
            onSelectAll={handleSelectAll}
            onDeselectAll={handleDeselectAll}
            onEditOperation={handleEditOperation}
            onValidateEdits={handleValidateEdits}
          />
        )}

        {/* Execution & Confirmation Controls */}
        {organizationPlan && (
          <ExecutionModal
            approvedCount={approvedCount}
            totalCount={organizationPlan.operations.length}
            conflictsCount={conflictsCount}
            hasUnsavedEdits={hasUnsavedEdits}
            isExecuting={isExecuting}
            isPlanExecuted={isPlanExecuted}
            executionResult={executionResult}
            onConfirmExecute={handleExecute}
            onUndoBatch={handleRollback}
            isUndoing={isRollingBack}
          />
        )}
      </main>

      {/* Undo History Drawer */}
      <UndoHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        manifests={historyManifests}
        onRollback={handleRollback}
        onRefresh={handleRefreshHistory}
        isRollingBack={isRollingBack}
        activeRollingBackId={activeRollingBackId}
        lastRollbackResult={lastRollbackResult}
      />
    </div>
  );
}

export default App;
