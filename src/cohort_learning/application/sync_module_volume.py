"""Use case: Sync a module's content volume from its git repository.

POST /modules/{module_id}/sync  →  SyncModuleVolumeUseCase.execute()

Behaviour:
- Looks up the ModuleProgression; raises LookupError if not found.
- Raises ValueError if repo_url is not configured.
- Calls GitVolumeSync to clone/pull into
  $VOLUMES_BASE_PATH/modules/<module_id>/.
- Returns the absolute path to the local volume directory.

Only the module master may trigger a sync (PermissionError otherwise).
"""

from __future__ import annotations

import os
from pathlib import Path

from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.infrastructure.git_sync import GitVolumeSync


def _get_volumes_base() -> Path:
    return Path(os.environ.get("VOLUMES_BASE_PATH", "./volumes"))


class SyncModuleVolumeUseCase:
    """Clone or pull the git repo attached to a module's content volume."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, module_id: str, caller_id: str) -> Path:
        """Sync the module volume and return its local path.

        Args:
            module_id: ID of the target module.
            caller_id: ID of the authenticated user triggering the sync.

        Returns:
            Path to the local volume directory.

        Raises:
            LookupError: Module not found.
            ValueError: No repo_url configured on the module.
            PermissionError: Caller is not the module master.
            RuntimeError: git clone/pull failed.
        """
        with self._uow as uow:
            module = uow.modules.find_by_id(module_id)
            if module is None:
                raise LookupError(f"Module '{module_id}' not found")
            if module.master_id != caller_id:
                raise PermissionError("Only the module master may trigger a sync")
            if not module.repo_url:
                raise ValueError(
                    f"Module '{module_id}' has no repo_url configured"
                )
            repo_url = module.repo_url

        syncer = GitVolumeSync(volumes_base_path=_get_volumes_base())
        return syncer.sync_module(module_id=module_id, repo_url=repo_url)
