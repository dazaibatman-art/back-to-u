"""
Root convenience seeder for Group No1 Global Lost & Found Management System.
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent / "group-no1"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from seed import seed_database

if __name__ == "__main__":
    seed_database()
