import sys
from pathlib import Path

# ensure backend directory is always in sys.path during test execution
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
