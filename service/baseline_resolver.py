from typing import TypedDict, Optional
from pydantic import BaseModel
import logging
import tempfile
import importlib.util
import subprocess
import sys
import yaml
from pathlib import Path
from fastapi import FastAPI

from models.contract import Contract
from models.contract_version import ContractVersion
from database.connection import SessionLocal

import models.contract
import models.contract_version
import models.consumer
import models.consumer_dependency

log = logging.getLogger(__name__)

class GitBase(BaseModel):
    spec: Optional[str]
    
class DbBase(BaseModel):
    spec: str
    source: str
    version: str
    description: Optional[str]
    
class BaselineResolver:
    def resolve(self, 
                contract:str, 
                version: Optional[str] = None, 
                baseline: Optional[str] = "main")->str:
        if ":" in contract:
            spec = self._git_contract_retriever(contract, version, baseline)
            if spec:
                return spec
        return self._db_contract_retriever(contract, version, baseline)
    
    def _git_contract_retriever(self, contract: str,
                                version: Optional[str]= None,
                                baseline:Optional[str] = "main"
                                )-> GitBase:
        """
        Retrieve an OpenAPI spec from a FastAPI app at a Git ref.
        contract:
            Python module path in the form:
                "resource.api.main:app"
        version:
            ContractGuard/PostgreSQL version.
            Never interpreted as a Git ref.
        baseline:
            Git ref such as "main", "develop", or a commit SHA.
        Returns:
            YAML OpenAPI specification, or None if retrieval fails.
        """
        # Version means PostgreSQL, not Git.
        if version is not None:
            log.debug(
                "Version '%s' is not handled by Git retriever.",
                version,
            )
            return None
        # Default Git baseline.
        ref = baseline or "main"
        if not self._git_ref_exists(ref):
            return None

        worktree = None
        worktree_str = None
        tmpdir = None
        try:
            result = self._create_worktree(ref)
            if result is None:
                return None
            tmpdir, worktree, worktree_str = result

            try:
                return self._import_fastapi_app(
                    contract, worktree, worktree_str, ref
                )
            except yaml.YAMLError as exc:
                log.warning(
                    "Failed to serialize OpenAPI schema: %s",
                    exc,
                )
                return None
        finally:
            self._cleanup_worktree(worktree, tmpdir)
            
    
    def _git_ref_exists(self, ref: str) -> bool:
        """
        Validate that a Git ref exists.
        Returns True if the ref is valid, False otherwise.
        """
        # Validate Git ref.
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", ref],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            log.warning("Unable to check Git ref '%s': %s", ref, exc)
            return False
        if result.returncode != 0:
            log.debug("Git ref '%s' does not exist.", ref)
            return False
        return True
        
    
    def _create_worktree(self, ref: str) -> Optional[tuple]:
        """
        Create a temporary Git worktree for the given ref.
        Returns (tmpdir, worktree, worktree_str) on success, or None on failure.
        """
        worktree = None
        worktree_str = None
        try:
            # Create temporary directory.
            tmpdir = tempfile.TemporaryDirectory(
                prefix="contractguard-git-"
            )
            worktree = Path(tmpdir.name) / "repo"
            worktree_str = str(worktree)
            # Create Git worktree.
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "--detach",
                    worktree_str,
                    ref,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return tmpdir, worktree, worktree_str
        except subprocess.TimeoutExpired:
            log.warning(
                "Timed out while creating Git worktree for '%s'.",
                ref,
            )
            return None
        except subprocess.CalledProcessError as exc:
            log.warning(
                "Git worktree creation failed for '%s': %s",
                ref,
                exc.stderr.strip() if exc.stderr else exc,
            )
            return None
        except Exception as exc:
            log.warning(
                "Unexpected Git extraction failure for '%s': %s",
                ref,
                exc,
            )
            return None
        
    def _git_branch_exists(self, branch:str)-> bool:
        """Check if branch exists locally or remotely"""
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True, text=True
        )
        return result.returncode ==0
    
    
    def _import_fastapi_app(
        self,
        contract: str,
        worktree: Path,
        worktree_str: str,
        ref: str,
    ) -> Optional[str]:
        """
        Import a FastAPI app from the given worktree and return its OpenAPI YAML.
        """
        # Validate contract identifier.
        if not contract or ":" not in contract:
            log.warning(
                "Invalid contract '%s'. Expected 'module.path:attribute'.",
                contract,
            )
            return None
        module_path, attr = contract.split(":", 1)
        module_path = module_path.strip()
        attr = attr.strip()
        if not module_path or not attr:
            log.warning(
                "Invalid contract '%s'. Expected 'module.path:attribute'.",
                contract,
            )
            return None
        # Convert:
        # resource.api.main
        #
        # into:
        # resource/api/main.py
        module_file = (
            worktree / Path(*module_path.split("."))
        ).with_suffix(".py")
        if not module_file.is_file():
            log.warning(
                "Module '%s' does not exist at Git ref '%s'.",
                module_file,
                ref,
            )
            return None
        # Allow repository imports.
        sys.path.insert(0, worktree_str)
        try:
            import_spec = importlib.util.spec_from_file_location(
                module_path,
                module_file,
            )
            if import_spec is None or import_spec.loader is None:
                log.warning(
                    "Could not create import spec for '%s'.",
                    module_path,
                )
                return None
            module = importlib.util.module_from_spec(import_spec)
            sys.modules[module_path] = module
            try:
                import_spec.loader.exec_module(module)
            except Exception as exc:
                log.warning(
                    "Failed to import '%s' from Git ref '%s': %s",
                    module_path,
                    ref,
                    exc,
                )
                return None
            app = getattr(module, attr, None)
            if app is None:
                log.warning(
                    "Attribute '%s' not found in '%s'.",
                    attr,
                    module_path,
                )
                return None
            if not isinstance(app, FastAPI):
                log.warning(
                    "'%s:%s' is not a FastAPI application.",
                    module_path,
                    attr,
                )
                return None
            try:
                openapi_schema = app.openapi()
            except Exception as exc:
                log.warning(
                    "OpenAPI generation failed for '%s:%s': %s",
                    module_path,
                    attr,
                    exc,
                )
                return None
            if not isinstance(openapi_schema, dict):
                log.warning(
                    "Invalid OpenAPI schema returned by '%s:%s'.",
                    module_path,
                    attr,
                )
                return None
            return yaml.safe_dump(
                openapi_schema,
                sort_keys=False,
            )
        finally:
            # Remove imported module.
            sys.modules.pop(module_path, None)
            # Remove temporary repo from Python import path.
            if worktree_str in sys.path:
                sys.path.remove(worktree_str)
        
    def _cleanup_worktree(self, worktree: Optional[Path], tmpdir) -> None:
        """
        Always unregister the Git worktree and clean up the temporary directory.
        """
        # Always unregister the Git worktree.
        if worktree is not None:
            try:
                subprocess.run(
                    [
                        "git",
                        "worktree",
                        "remove",
                        "--force",
                        str(worktree),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except Exception as exc:
                log.warning(
                    "Failed to clean up Git worktree '%s': %s",
                    worktree,
                    exc,
                )
        # TemporaryDirectory cleanup.
        if "tmpdir" in locals():
            tmpdir.cleanup()

        
    
    def _db_contract_retriever(self,
                               contract: str,  
                               version: Optional[str] = None, 
                               baseline:Optional[str] = None
                               )-> Optional[str]:
        """
        Retrieves the OpenAPI spec from PostgreSQL database for the given contract.
        If version is provided, attempts exact match first.
        Otherwise (or if exact version not found), falls back through status hierarchy:
        approved -> released -> resolution failure (None)
        """

        db = SessionLocal()
        
        try:
            # Explicit version
            if version is not None:
                result = (
                    db.query(ContractVersion)
                    .join(Contract)
                    .filter(
                        Contract.name == contract,
                        ContractVersion.version == version,
                    )
                    .first()
                )
                return result.spec if result else None

            # Default: newest approved -> newest released
            statuses = ["approved","released"]
            for status in statuses:
                result = (
                    db.query(ContractVersion)
                    .join(Contract)
                    .filter(
                        Contract.name == contract,
                        ContractVersion.status == status,
                    )
                    .order_by(ContractVersion.created_at.desc())
                    .first()
                )
                if result:
                    return result.spec
            log.warning("DB resolution failed for contract '%s' (version='%s')",
                        contract, version)
            return None

        except Exception as e:
            log.error("Database query error for contract '%s': %s",
                      contract, e)
            return None

        finally:
            db.close()

    
