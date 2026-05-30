"""Git synchronisation helper for content volumes.

Handles cloning and pulling a git repository into a local directory.
The repo URL is expected to contain any required credentials
(e.g. ``https://<token>@github.com/org/repo.git``).

Usage::

    syncer = GitVolumeSync(volumes_base_path=Path("./volumes"))
    syncer.sync_module(module_id="mod-1", repo_url="https://token@github.com/org/repo")
    syncer.sync_project(project_id="proj-1", repo_url="https://token@github.com/org/docs")
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_GIT = "git"


def _run(args: list[str], cwd: Path | None = None) -> None:
    """Run a git sub-command and raise RuntimeError on non-zero exit."""
    result = subprocess.run(  # noqa: S603
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {' '.join(args)}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class GitVolumeSync:
    """Clones or pulls a git repository into the local volumes tree.

    Directory layout::

        <volumes_base_path>/
            modules/<module_id>/   ← module content repos
            projects/<project_id>/ ← project docs repos
    """

    def __init__(self, volumes_base_path: Path) -> None:
        self._base = volumes_base_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync_module(self, module_id: str, repo_url: str) -> Path:
        """Clone or pull the module content repo. Returns the volume path."""
        target = self._base / "modules" / module_id
        return self._sync(repo_url=repo_url, target=target)

    def sync_project(self, project_id: str, repo_url: str) -> Path:
        """Clone or pull the project docs repo. Returns the volume path."""
        target = self._base / "projects" / project_id
        return self._sync(repo_url=repo_url, target=target)

    def volume_path_for_module(self, module_id: str) -> Path:
        """Return the local volume path for a module (may not yet exist)."""
        return self._base / "modules" / module_id

    def volume_path_for_project(self, project_id: str) -> Path:
        """Return the local volume path for a project (may not yet exist)."""
        return self._base / "projects" / project_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync(self, repo_url: str, target: Path) -> Path:
        """Clone if target doesn't exist; pull if it does."""
        if (target / ".git").exists():
            logger.info("git pull: %s", target)
            _run([_GIT, "pull", "--ff-only"], cwd=target)
        else:
            target.mkdir(parents=True, exist_ok=True)
            logger.info("git clone %s -> %s", repo_url, target)
            _run([_GIT, "clone", repo_url, str(target)])
        return target
