"""Render entry point.

The Campus Connect application itself remains in ``backend/app.py``. This
small wrapper supports Render services that are configured with the repository
root as their working directory.
"""

import os

from backend.app import app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
