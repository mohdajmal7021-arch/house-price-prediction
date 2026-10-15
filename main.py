from __future__ import annotations

from pathlib import Path

import uvicorn

from auth_db import init_db
from app.main import app

if __name__ == "__main__":
    init_db()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
