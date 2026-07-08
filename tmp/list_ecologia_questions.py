from pathlib import Path
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

questions = json.loads(Path("tmp/ecologia_questions.json").read_text(encoding="utf-8"))
html = Path("index.html").read_text(encoding="utf-8")

for q in questions:
    pos = html.find(q["q"])
    line = html.count("\n", 0, pos) + 1 if pos >= 0 else "?"
    correct = [a[0] for a in q["a"] if a[1] == 1]
    print(f"L{line} #{q['_idx']} {q['d']} p{q['p']} {q['t']}: {q['q']} -> {correct}")
