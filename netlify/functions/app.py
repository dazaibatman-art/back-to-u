"""
Netlify Serverless Function Handler for Group No1 Flask Application.

Netlify builds from the repo root, so paths must be resolved relative
to this file's real location inside the built Lambda package.
"""

import os
import sys
from pathlib import Path

# ─── Path setup ──────────────────────────────────────────────────────────────
# This file lives at: <repo-root>/netlify/functions/app.py
# After Netlify's build, included_files puts group-no1 at the same
# repo-root level inside the Lambda package.
_HERE = Path(__file__).resolve().parent          # .../netlify/functions/
_REPO = _HERE.parent.parent                      # repo root
_APP  = _REPO / "group-no1"                      # Flask app package root

for _p in [str(_REPO), str(_APP)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Ensure /tmp dirs exist (Lambda has read-only FS except /tmp) ─────────────
os.makedirs("/tmp/uploads", exist_ok=True)

# ─── App factory ─────────────────────────────────────────────────────────────
import serverless_wsgi  # noqa: E402
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

flask_app = create_app("production")

# Initialise database tables on cold start (SQLite in /tmp)
with flask_app.app_context():
    try:
        db.create_all()
    except Exception as exc:
        # Non-fatal — log and continue; the function will still start
        print(f"[group-no1] DB init warning on cold start: {exc}", flush=True)


# ─── Handler ─────────────────────────────────────────────────────────────────
def handler(event, context):
    """AWS Lambda / Netlify Functions entry point."""
    return serverless_wsgi.handle_request(flask_app, event, context)
