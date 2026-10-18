#!/usr/bin/env python3
"""Require the actual module APK to avoid the framework's parallel multi-DEX path."""
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile


apk = Path(sys.argv[1])
with zipfile.ZipFile(apk) as archive:
    dex = sorted(name for name in archive.namelist() if re.fullmatch(r"classes(?:[0-9]+)?\.dex", name))
assert dex == ["classes.dex"], f"Module must contain exactly one DEX, found {dex}"
print(json.dumps({"apk": str(apk), "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
                  "dex": dex, "result": "PASS"}))
