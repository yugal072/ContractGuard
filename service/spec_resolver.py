from typing import Optional
from pathlib import Path
import importlib.util
from fastapi import FastAPI
import yaml
import logging

log = logging.getLogger(__name__)

class SpecResolver:
    def resolve(self, contract: str) -> Optional[str]:
        """
        Resolves the current OpenAPI spec of a contract.
        
        Explicit Order:
          1. Contains ":" -> FastAPI module (e.g. "resource.api.main:app")
          2. Existing file -> OpenAPI file (.yaml / .json)
          3. Otherwise -> Raw YAML / JSON spec string
        """
        if not contract or not isinstance(contract, str):
            return None

        # 1. FastAPI module path ("module.path:attr")
        if ":" in contract:
            module_path, _, attr = contract.partition(":")
            module_path = module_path.strip()
            attr = attr.strip() or "app"
            
            try:
                module = importlib.import_module(module_path)
                app = getattr(module, attr, None)
                if isinstance(app, FastAPI):
                    openapi_schema = app.openapi()
                    if isinstance(openapi_schema, dict):
                        return yaml.safe_dump(openapi_schema, sort_keys=False)
                log.warning("'%s' is not a valid FastAPI app instance", contract)
            except Exception as exc:
                log.warning("Failed to import FastAPI app from '%s': %s", contract, exc)
            return None

        # 2. Local file path
        file_path = Path(contract)
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8")
                data = yaml.safe_load(content)
                if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                    return content
                log.warning("File '%s' does not contain a valid OpenAPI schema", contract)
            except Exception as exc:
                log.warning("Failed to read spec file '%s': %s", contract, exc)
            return None

        # 3. Raw YAML/JSON string
        try:
            data = yaml.safe_load(contract)
            if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                return contract
        except Exception:
            pass

        log.warning("SpecResolver could not resolve spec for '%s'", contract)
        return None