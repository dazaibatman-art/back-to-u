"""
Root convenience launcher for Group No1 Global Lost & Found Management System.
Allows running the project seamlessly from either the repository root or the group-no1 directory.
"""

import sys
from pathlib import Path

# Add group-no1 to Python path
PROJECT_DIR = Path(__file__).resolve().parent / "group-no1"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Import and execute the app runner
from run import app, db, host, port, debug

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    print("\n" + "=" * 60)
    print(" Group No1 — Global Lost & Found Management System")
    print(f" Running at: http://{host}:{port}")
    print(" Press CTRL+C to quit the server")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug)
