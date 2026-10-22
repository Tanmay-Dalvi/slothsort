"""Organization planning, validation, and execution API router."""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from backend.app.api.schemas import ExecutePlanRequest, GeneratePlanRequest, ValidatePlanRequest
from backend.app.config import settings
from backend.app.engine.executor import SafePlanExecutor
from backend.app.engine.planner import DeterministicOrganizationPlanner
from backend.app.engine.scanner import SafeFolderScanner
from backend.app.engine.validator import PlanValidator
from backend.app.models.manifest import ExecutionResult
from backend.app.models.plan import OrganizationPlan
from backend.app.providers.manager import ProviderManager
from backend.app.security import default_folder_policy
from backend.app.services.plan_store import plan_store

router = APIRouter(prefix="/plan", tags=["Planning & Execution"])
_provider_manager = ProviderManager()


@router.post(
    "/generate",
    response_model=OrganizationPlan,
    summary="Generate a preview-only organization plan",
    description="Scans the folder, queries the explicitly chosen AI provider for proposals, and constructs a validated preview plan without modifying files.",
)
async def generate_plan(req: GeneratePlanRequest) -> OrganizationPlan:
    # 1. Authorize folder path
    validated_root = default_folder_policy.validate_folder_path(req.folder_path)

    # 2. Scan files
    scanner = SafeFolderScanner()
    scan_result = scanner.scan(validated_root)

    if scan_result.total_files == 0:
        # Return empty validated plan immediately
        planner = DeterministicOrganizationPlanner(validated_root)
        empty_plan = planner.create_preview_plan([], [], provider_used=req.provider_id or "none")
        plan_store.save_plan(empty_plan)
        return empty_plan

    # 3. Generate suggestions using requested provider (zero silent fallback)
    provider_id = (req.provider_id or settings.DEFAULT_PROVIDER).strip().lower()
    try:
        suggestions = await _provider_manager.generate_suggestions(
            provider_id=provider_id,
            files=scan_result.files,
            options=req.options,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI provider '{provider_id}' failed: {str(e)}",
        )

    # 4. Construct deterministic preview plan
    planner = DeterministicOrganizationPlanner(validated_root)
    plan = planner.create_preview_plan(
        files=scan_result.files,
        suggestions=suggestions,
        provider_used=provider_id,
    )

    # 5. Persist plan in server-side session registry
    plan_store.save_plan(plan)
    return plan


@router.post(
    "/validate",
    response_model=OrganizationPlan,
    summary="Validate user-edited operations",
    description="Re-validates an edited set of operations against security rules and collision matrices.",
)
async def validate_plan(req: ValidatePlanRequest) -> OrganizationPlan:
    plan = plan_store.get_plan(req.plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{req.plan_id}' not found or session expired.",
        )

    if plan_store.is_executed(req.plan_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This plan has already been executed. Repeated modification or execution is forbidden.",
        )

    # Re-validate operations against the plan's authorized root
    validator = PlanValidator(Path(plan.root_path))
    validated_ops = validator.validate_operations(req.operations)
    conflicts_count = sum(1 for op in validated_ops if op.has_conflict)

    # Update stored plan
    plan.operations = validated_ops
    plan.conflicts_detected = conflicts_count
    plan.is_validated = True
    plan_store.save_plan(plan)

    return plan


@router.post(
    "/execute",
    response_model=ExecutionResult,
    summary="Execute approved plan operations",
    description="Executes only operations explicitly approved by the user. Refuses unapproved, conflicted, or replayed operations.",
)
async def execute_plan(req: ExecutePlanRequest) -> ExecutionResult:
    plan = plan_store.get_plan(req.plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{req.plan_id}' not found or session expired.",
        )

    if plan_store.is_executed(req.plan_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This plan has already been executed. Repeated execution is forbidden.",
        )

    # Verify folder authorization again at point of execution
    default_folder_policy.validate_folder_path(plan.root_path)

    # Verify that requested approved_op_ids belong to this plan
    plan_op_ids = {op.op_id for op in plan.operations}
    for op_id in req.approved_op_ids:
        if op_id not in plan_op_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operation ID '{op_id}' does not belong to plan '{req.plan_id}'.",
            )

    # Execute plan safely with approval set
    executor = SafePlanExecutor(manifest_dir=settings.MANIFEST_DIR)
    result = executor.execute_plan(
        plan=plan,
        approved_op_ids=set(req.approved_op_ids),
    )

    # Mark plan as permanently executed to prevent replay
    plan_store.mark_executed(plan.plan_id)
    return result
