# service/main.py
import sys
from pathlib import Path

# Project root = parent of service/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.contract_models import BreakingChangeRequest  # now works
from service.contract_service import ContractService
from tools.contract_tools import *  # noqa: F401
from service.trial import mcp

if __name__ == "__main__":
    mcp.run()