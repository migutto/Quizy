from pathlib import Path
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

base = Path("Quiz z marketingu") / "uploads"

for arg in sys.argv[1:]:
    path = base / arg
    doc = fitz.open(str(path))
    for i, page in enumerate(doc, start=1):
        print(f"\n===== {arg} page {i} =====")
        print(page.get_text("text")[:3000])
