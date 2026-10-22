"""Deterministic organization planner producing preview-only plans."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from backend.app.engine.validator import PlanValidator, sanitize_component, validate_filename
from backend.app.models.file import FileMetadata
from backend.app.models.operation import (
    FileOperation,
    OperationStatus,
    OperationType,
    generate_operation_id,
)
from backend.app.models.plan import (
    FileSuggestion,
    OrganizationPlan,
    generate_plan_id,
)


class DeterministicOrganizationPlanner:
    """
    Constructs and validates preview-only organization plans.
    Strictly read-only; never touches the filesystem.
    """

    def __init__(self, root_path: Union[str, Path]):
        self.root_path = Path(root_path).resolve()
        self.validator = PlanValidator(self.root_path)

    def create_preview_plan(
        self,
        files: List[FileMetadata],
        suggestions: List[FileSuggestion],
        provider_used: str = "mock",
    ) -> OrganizationPlan:
        """
        Creates an OrganizationPlan by pairing FileMetadata with FileSuggestion.
        Validates all operations and attaches conflict flags.
        """
        suggestions_by_id: Dict[str, FileSuggestion] = {
            s.file_id: s for s in suggestions
        }

        unvalidated_ops: List[FileOperation] = []

        for file_meta in files:
            source_rel = file_meta.original_rel_path.replace("\\", "/").strip("/")
            suggestion = suggestions_by_id.get(file_meta.id)

            if suggestion is None:
                # No suggestion provided; default to KEEP in current location
                target_rel = source_rel
                op_type = OperationType.KEEP
            else:
                cat = suggestion.suggested_category.strip().strip("/")
                new_filename = suggestion.suggested_filename.strip() or file_meta.filename

                # Compose target relative path without masking traversal or invalid tokens
                if cat and cat != ".":
                    cat_parts = []
                    for p in cat.split("/"):
                        if not p or p == ".":
                            continue
                        cat_parts.append(p)
                    target_rel = "/".join(cat_parts + [new_filename])
                else:
                    target_rel = new_filename

                # Determine operation type
                source_parent = str(Path(source_rel).parent).replace("\\", "/")
                target_parent = str(Path(target_rel).parent).replace("\\", "/")
                source_name = Path(source_rel).name
                target_name = Path(target_rel).name

                if source_rel == target_rel:
                    op_type = OperationType.KEEP
                elif source_parent == target_parent and source_name != target_name:
                    op_type = OperationType.RENAME
                elif source_parent != target_parent and source_name == target_name:
                    op_type = OperationType.MOVE
                else:
                    op_type = OperationType.MOVE_AND_RENAME

            op = FileOperation(
                op_id=generate_operation_id(),
                file_id=file_meta.id,
                source_rel_path=source_rel,
                target_rel_path=target_rel,
                op_type=op_type,
                status=OperationStatus.PENDING,
                is_approved=True,
                conflicts=[],
            )
            unvalidated_ops.append(op)

        # Run deterministic validation across all operations
        validated_ops = self.validator.validate_operations(unvalidated_ops)
        conflicts_count = sum(1 for op in validated_ops if op.has_conflict)

        return OrganizationPlan(
            plan_id=generate_plan_id(),
            root_path=str(self.root_path),
            provider_used=provider_used,
            total_files=len(files),
            operations=validated_ops,
            conflicts_detected=conflicts_count,
            is_validated=True,
            requires_approval=True,
        )
