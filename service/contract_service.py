import tempfile
import json
import yaml
import subprocess
from typing import Optional
from pathlib import Path

from models.contract_models import BreakingChangeRequest, BreakingChangeResponse, BreakingSummary, BreakingChange


class ContractService:
    def __init__(self):
        pass
    
    def _write_spec_to_temp(self, spec_str: str)->Path:
        """Parse JSON/YAML string and write as normalized YAML to temp file"""
        try:
           data = json.loads(spec_str) 
        except json.JSONDecodeError:
            try: 
                data = yaml.safe_load(spec_str)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid spec format: {e}")
        
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(data, tmp, sort_keys=False, Dumper=yaml.SafeDumper)
        tmp.close()
        return Path(tmp.name)
    
    def _location_change(self, item:dict)->str:
        """Build a human-readable location string from an oasdiff change item."""
        path = item.get("path")
        operation = item.get("operation")
        section = item.get("section")

        if path and operation:
            return f"{operation} {path}"
        if path:
            return path
        if section:
            return section
        return ""
            
    
    def _parse_oasdiff_output(self, output:str)-> tuple[list[BreakingChange], BreakingSummary]:
        """Normalize oasdiff JSON output to BreakingChangeResponse format"""
        changes_data = json.loads(output or "[]")
        if not isinstance(changes_data, list):
            changes_data = []
            
        changes: list[BreakingChange] = []
        critical= high = low = 0
        
        for item in changes_data:
            raw_level = item.get("level")

            # handle both numeric and string forms
            if raw_level in (3,"error","ERR", "ERROR"):
                severity = "critical"
                critical += 1
            elif raw_level in (2, "warn", "WARN", "WARNING"):
                severity = "high"
                high +=1
            else:
                # 1/ info / INFO or unknown
                severity = "low"
                low+=1
            
            changes.append(BreakingChange(
                category=item.get("id") or item.get("type", "UNKNOWN"),
                severity =severity,
                message=item.get("text") or item.get("message",""),
                location=self._location_change(item)
            ))
            
        summary = BreakingSummary(
            total_changes= len(changes),
            critical=critical,
            high = high,
            low = low
        )
        return changes, summary
        
    def check_breaking_changes(self, request: BreakingChangeRequest, contract_title:Optional[str], mode:str="breaking")->BreakingChangeResponse:
        if mode not in {"breaking", "diff"}:
            raise ValueError("mode must be 'breaking' or 'diff'")
        
        old_path = self._write_spec_to_temp(request.old_spec)
        new_path = self._write_spec_to_temp(request.new_spec)
        try:
            # 1. oasdiff breaking
            breaking_res = subprocess.run(
                ["oasdiff", "breaking", "--format", "json", str(old_path), str(new_path)],
                capture_output=True, text=True, timeout=60
            )
            if breaking_res.returncode !=0:
                raise RuntimeError(f"oasdiff failed (code {breaking_res.returncode}): {breaking_res.stderr}")
                
            changes, summary = self._parse_oasdiff_output(breaking_res.stdout or "[]")
            
            # 2. Run oasdiff only if diff mode is explicitly requested
            diff_data= None
            if mode == "diff":
                diff_res = subprocess.run(
                    ["oasdiff", "diff", "--format", "json", str(old_path), str(new_path)],
                    capture_output=True, text=True, timeout=60
                )
                if diff_res.returncode!=0:
                    raise RuntimeError(f"oasdiff diff failed: {diff_res.stderr}")
                diff_data= json.loads(diff_res.stdout or "{}")
            
            # 3. Connect to Consumer Impace Engine
            impacted_consumers=[]
            if changes and contract_title:
                from service.impact_engine import ImpactEngine
                impact_engine = ImpactEngine()
                impact_res = impact_engine.analyze_impact(contract_title, changes)
                impacted_consumers = impact_res.impacted_consumers
                
            return BreakingChangeResponse(
                breaking=len(changes) > 0,
                changes=changes,
                summary=summary,
                diff=diff_data,
                impacted_consumers=impacted_consumers
            )
        finally:
            old_path.unlink(missing_ok=True)
            new_path.unlink(missing_ok=True)
        
        