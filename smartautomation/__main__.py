"""Read-only diagnostics entrypoint: python -m smartautomation."""
from __future__ import annotations
import json
from smartautomation.diagnostics import check_readiness

if __name__ == "__main__":
    print(json.dumps(check_readiness(), indent=2, ensure_ascii=False))
