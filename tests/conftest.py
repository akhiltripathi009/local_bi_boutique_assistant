import sys
from pathlib import Path
import tempfile
import pytest

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.data.db_manager import DatabaseManager
from src.core.catalog import CATALOG

def get_test_database():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    return DatabaseManager(db_path=tmp.name)
