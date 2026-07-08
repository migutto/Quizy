from __future__ import annotations

import collections
import json
import math
import re
import statistics
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import fitz


ROOT = Path(".")
QUESTIONS_PATH = ROOT / "tmp" / "ecologia_questions.json"
UPLOADS = ROOT / "Quiz z marketingu" / "uploads"
PDFS = [
    UPLOADS / "egz eko (1).pdf",
    UPLOADS / "EZS-NS-W1-W2.pdf",
    UPLOADS / "EZS-NS-W3-W4.pdf",
    UPLOADS / "EZS-NS-W5-W6.pdf",
    UPLOADS / "EZS-NS-W7.pdf",
]
REPORT_PATH = ROOT / "tmp" / "ecologia_audit_report.md"
FINDINGS_PATH = ROOT / "tmp" / "ecologia_audit_findings.json"

STOPWORDS = {
    "albo", "ale", "bez", "byc", "byla", "bylo", "byly", "czy", "dla", "gdy",
    "ich", "jak", "jaka", "jakie", "jakich", "jako", "jest", "jego", "jej",
    "ktore", "ktora", "ktory", "lub", "miedzy", "moga", "moze", "nad", "nie",
    "oraz", "pod", "polega", "poniewaz", "przez", "przy", "sie", "takie",
    "tego", "tej", "ten", "tym", "tych", "we", "wedlug", "wraz", "wsrod",
    "zeby", "ekologia", "ekologii", "ekologiczna", "ekologiczne", "srodowiska",
    "srodowisko", "srodowiskiem", "ochrona", "ochrony", "system", "systemu",
    "dotyczy", "obejmuje", "oznacza", "najczesciej", "przede", "wszystkim",
}


def strip_accents(text: str) -> str:
    text = text.replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm(text: str) -> str:
    text = strip_accents(text).lower()
    text = text.replace("�", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    out = []
    for tok in norm(text).split():
        if tok in STOPWORDS:
            continue
        if len(tok) < 4 and not tok.isdigit():
            continue
        out.append(tok)
    return out


@dataclass
class PageText:
    pdf: str
    page: int
    text: str
    norm_text: str
    token_set: set[str]


def extract_pdf_pages() -> list[PageText]:
    pages: list[PageText] = []
    for path in PDFS:
        doc = fitz.open(str(path))
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            pages.append(PageText(path.name, i, text, norm(text), set(tokens(text))))
    return pages


def find_line_numbers(questions: list[dict]) -> dict[int, int | None]:
    html = Path("index.html").read_text(encoding="utf-8")
    line_map = {}
    for q in questions:
        pos = html.find(q["q"])
        line_map[q["_idx"]] = None if pos < 0 else html.count("\n", 0, pos) + 1
    return line_map


def correct_indices(q: dict) -> list[int]:
    return [i for i, opt in enumerate(q["a"]) if opt[1] == 1]


def source_match(questions: list[dict], pages: list[PageText]) -> list[dict]:
    doc_freq = collections.Counter()
    for p in pages:
        doc_freq.update(p.token_set)
    total_pages = len(pages)
    idf = {tok: math.log((1 + total_pages) / (1 + df)) + 1 for tok, df in doc_freq.items()}

    matches = []
    for q in questions:
        ci = correct_indices(q)
        correct_text = " ".join(q["a"][i][0] for i in ci)
        query = f"{q.get('d', '')} {q.get('q', '')} {correct_text} {q.get('e', '')}"
        qtokens = sorted(set(tokens(query)))
        if not qtokens:
            matches.append({"idx": q["_idx"], "score": 0, "pdf": None, "page": None, "hits": []})
            continue
        denom = sum(idf.get(t, 1.0) for t in qtokens)
        best = None
        for p in pages:
            hits = [t for t in qtokens if t in p.token_set]
            if not hits:
                score = 0.0
            else:
                score = sum(idf.get(t, 1.0) for t in hits) / denom
            if best is None or score > best["score"]:
                best = {
                    "idx": q["_idx"],
                    "score": round(score, 3),
                    "pdf": p.pdf,
                    "page": p.page,
                    "hits": hits[:20],
                }
        matches.append(best)
    return matches


def option_length_stats(questions: list[dict]) -> dict:
    single = [q for q in questions if q["t"] == "single"]
    multi = [q for q in questions if q["t"] == "multi"]
    tf = [q for q in questions if q["t"] == "tf"]

    single_longest_correct = []
    single_suspicious = []
    correct_lens = []
    incorrect_lens = []
    source_correct_pos = collections.Counter()
    multi_grouped = 0

    for q in single:
        ci = correct_indices(q)
        if len(ci) != 1:
            continue
        c = ci[0]
        source_correct_pos[c + 1] += 1
        lens = [len(opt[0]) for opt in q["a"]]
        correct_lens.append(lens[c])
        incorrect_lens.extend(lens[i] for i in range(len(lens)) if i != c)
        max_len = max(lens)
        unique_max = lens.count(max_len) == 1
        if lens[c] == max_len:
            single_longest_correct.append(q["_idx"])
        avg_incorrect = statistics.mean(lens[i] for i in range(len(lens)) if i != c)
        ratio = lens[c] / avg_incorrect if avg_incorrect else 0
        if unique_max and lens[c] == max_len and ratio >= 1.35 and lens[c] - max(lens[i] for i in range(len(lens)) if i != c) >= 10:
            single_suspicious.append({
                "idx": q["_idx"],
                "ratio": round(ratio, 2),
                "correct_len": lens[c],
                "max_incorrect_len": max(lens[i] for i in range(len(lens)) if i != c),
                "q": q["q"],
                "correct": q["a"][c][0],
            })

    for q in multi:
        ci = correct_indices(q)
        if ci:
            first_bad = min((i for i, opt in enumerate(q["a"]) if opt[1] != 1), default=len(q["a"]))
            if max(ci) < first_bad:
                multi_grouped += 1

    tf_truth = collections.Counter()
    tf_first_correct = 0
    for q in tf:
        ci = correct_indices(q)
        if len(ci) == 1:
            label = norm(q["a"][ci[0]][0])
            tf_truth[label] += 1
            if ci[0] == 0:
                tf_first_correct += 1

    return {
        "single_count": len(single),
        "multi_count": len(multi),
        "tf_count": len(tf),
        "single_source_correct_position": dict(source_correct_pos),
        "single_correct_is_longest_count": len(single_longest_correct),
        "single_correct_is_longest_pct": round(100 * len(single_longest_correct) / len(single), 1) if single else 0,
        "single_suspicious_long_correct": single_suspicious[:40],
        "single_avg_correct_len": round(statistics.mean(correct_lens), 1) if correct_lens else 0,
        "single_avg_incorrect_len": round(statistics.mean(incorrect_lens), 1) if incorrect_lens else 0,
        "multi_grouped_correct_first_count": multi_grouped,
        "multi_grouped_correct_first_pct": round(100 * multi_grouped / len(multi), 1) if multi else 0,
        "tf_correct_labels": dict(tf_truth),
        "tf_first_option_correct_count": tf_first_correct,
        "tf_first_option_correct_pct": round(100 * tf_first_correct / len(tf), 1) if tf else 0,
    }


def duplicate_stats(questions: list[dict]) -> dict:
    normalized = collections.defaultdict(list)
    for q in questions:
        normalized[norm(q["q"])].append(q["_idx"])
    exact = {k: v for k, v in normalized.items() if len(v) > 1}

    similar = []
    qnorm = [(q["_idx"], norm(q["q"]), q["q"]) for q in questions]
    for i in range(len(qnorm)):
        idx1, n1, raw1 = qnorm[i]
        if len(n1) < 25:
            continue
        for j in range(i + 1, len(qnorm)):
            idx2, n2, raw2 = qnorm[j]
            if abs(len(n1) - len(n2)) > max(35, 0.45 * max(len(n1), len(n2))):
                continue
            ratio = SequenceMatcher(None, n1, n2).ratio()
            if ratio >= 0.86:
                similar.append({"idx1": idx1, "idx2": idx2, "ratio": round(ratio, 3), "q1": raw1, "q2": raw2})
    similar.sort(key=lambda x: x["ratio"], reverse=True)
    return {"exact": exact, "similar": similar[:50]}


def source_stats(matches: list[dict]) -> dict:
    by_pdf = collections.Counter(m["pdf"] for m in matches)
    low = [m for m in matches if m["score"] < 0.16]
    weak = [m for m in matches if 0.16 <= m["score"] < 0.24]
    strong = [m for m in matches if m["score"] >= 0.36]
    return {
        "best_source_by_pdf": dict(by_pdf),
        "low_support_count": len(low),
        "weak_support_count": len(weak),
        "strong_support_count": len(strong),
        "low_support": low[:80],
    }


def main() -> None:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    pages = extract_pdf_pages()
    line_numbers = find_line_numbers(questions)

    by_type = collections.Counter(q["t"] for q in questions)
    by_d = collections.Counter(q["d"] for q in questions)
    by_p = collections.Counter(q["p"] for q in questions)
    bad_correct_counts = [q for q in questions if (q["t"] in {"single", "tf"} and len(correct_indices(q)) != 1) or (q["t"] == "multi" and len(correct_indices(q)) < 1)]
    matches = source_match(questions, pages)
    match_by_idx = {m["idx"]: m for m in matches}
    len_stats = option_length_stats(questions)
    dupes = duplicate_stats(questions)
    src = source_stats(matches)

    low_examples = []
    for m in src["low_support"][:25]:
        q = questions[m["idx"]]
        low_examples.append({
            "idx": q["_idx"],
            "line": line_numbers[q["_idx"]],
            "d": q["d"],
            "t": q["t"],
            "q": q["q"],
            "score": m["score"],
            "best_source": f"{m['pdf']} s. {m['page']}" if m["pdf"] else None,
            "hits": m["hits"],
        })

    findings = {
        "total_questions": len(questions),
        "pdf_pages": [{"pdf": p.name, "pages": len(fitz.open(str(p)))} for p in PDFS],
        "by_type": dict(by_type),
        "by_category": dict(by_d),
        "by_difficulty": dict(by_p),
        "bad_correct_counts": [{"idx": q["_idx"], "q": q["q"], "correct_count": len(correct_indices(q))} for q in bad_correct_counts],
        "length_stats": len_stats,
        "duplicates": dupes,
        "source_stats": src,
        "low_support_examples": low_examples,
        "matches": matches,
    }
    FINDINGS_PATH.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Audyt modułu Ekologia\n")
    lines.append("## Zakres\n")
    lines.append(f"- Pytania z `index.html`: {len(questions)}.\n")
    lines.append("- Źródła PDF:\n")
    for item in findings["pdf_pages"]:
        lines.append(f"  - `{item['pdf']}`: {item['pages']} stron\n")
    lines.append("\n## Statystyki banku\n")
    lines.append(f"- Typy pytań: {dict(by_type)}\n")
    lines.append(f"- Trudność: {dict(sorted(by_p.items()))}\n")
    lines.append("- Kategorie:\n")
    for k, v in sorted(by_d.items()):
        lines.append(f"  - `{k}`: {v}\n")
    lines.append("\n## Kontrola odpowiedzi i biasów\n")
    lines.append(f"- Prawidłowa liczba odpowiedzi: problemów formalnych {len(bad_correct_counts)}.\n")
    lines.append(f"- Prawda/Fałsz: {len_stats['tf_count']} pytań, poprawne etykiety {len_stats['tf_correct_labels']}, pierwsza opcja poprawna w {len_stats['tf_first_option_correct_count']} przypadkach ({len_stats['tf_first_option_correct_pct']}%).\n")
    lines.append(f"- Single w źródle: rozkład pozycji poprawnej odpowiedzi {len_stats['single_source_correct_position']}. W praktyce aplikacja losuje single/multi, ale przy wyłączonym `shuffleAnswers` wszystkie single miałyby poprawną odpowiedź jako A.\n")
    lines.append(f"- Single: poprawna odpowiedź jest najdłuższa w {len_stats['single_correct_is_longest_count']} z {len_stats['single_count']} pytań ({len_stats['single_correct_is_longest_pct']}%). Średnia długość poprawnej: {len_stats['single_avg_correct_len']} znaków, błędnej: {len_stats['single_avg_incorrect_len']} znaków.\n")
    lines.append(f"- Multi: poprawne odpowiedzi są zapisane przed błędnymi w {len_stats['multi_grouped_correct_first_count']} z {len_stats['multi_count']} pytań ({len_stats['multi_grouped_correct_first_pct']}%). W runtime single/multi są losowane, TF nie są losowane.\n")
    lines.append("\n### Najbardziej podejrzane długie poprawne odpowiedzi single\n")
    for item in len_stats["single_suspicious_long_correct"][:20]:
        ln = line_numbers[item["idx"]]
        lines.append(f"- L{ln}, ratio {item['ratio']}: {item['q']} -> {item['correct']}\n")
    lines.append("\n## Duplikaty i podobieństwa\n")
    lines.append(f"- Dokładne duplikaty pytań: {len(dupes['exact'])}.\n")
    lines.append(f"- Silnie podobne pary (>=0.86): {len(dupes['similar'])} pokazanych w JSON.\n")
    for item in dupes["similar"][:15]:
        l1 = line_numbers[item["idx1"]]
        l2 = line_numbers[item["idx2"]]
        lines.append(f"- {item['ratio']}: L{l1} `{item['q1']}` / L{l2} `{item['q2']}`\n")
    lines.append("\n## Dopasowanie do źródeł PDF\n")
    lines.append(f"- Najlepsze źródło według dopasowania tokenów: {src['best_source_by_pdf']}.\n")
    lines.append(f"- Mocne dopasowanie >=0.36: {src['strong_support_count']}; słabe 0.16-0.24: {src['weak_support_count']}; bardzo słabe <0.16: {src['low_support_count']}.\n")
    lines.append("- Przykłady bardzo słabo podpartych automatycznie, do ręcznej kontroli:\n")
    for item in low_examples[:20]:
        lines.append(f"  - L{item['line']} [{item['d']}/{item['t']}] score {item['score']} best {item['best_source']}: {item['q']}\n")

    lines.append("\n## Ręczne wnioski merytoryczne\n")
    lines.append("- Nie znalazłem twardych błędów formalnych odpowiedzi względem podanych PDF-ów: każde pytanie ma właściwą liczbę odpowiedzi poprawnych, a automatyczne dopasowanie wskazuje źródło dla wszystkich 280 pytań.\n")
    lines.append("- Kilka pytań jest poprawnych względem wykładu, ale może być nieaktualnych lub zbyt absolutnych, jeżeli quiz ma sprawdzać aktualną wiedzę, a nie materiał z PDF-ów: CO2 ok. 0,035%, energetyka jądrowa 16% energii świata i zerowa emisja CO2, bilans CO2 biomasy równy zero, oraz nazwy organów/nadzoru w części KOBiZE.\n")
    lines.append("- Pytanie o CO2 w atmosferze (`L1517`) jest zgodne ze slajdem W3-W4, ale warto oznaczyć je jako historyczne/wykładowe albo zaktualizować do współczesnego poziomu.\n")
    lines.append("- Pytanie o energetykę jądrową (`L1547`) jest zgodne ze slajdem W3-W4, ale lepiej doprecyzować jako `ok. 16% według wykładu / dawnych danych` albo zmienić pytanie na jakościowe: `energetyka jądrowa ma bardzo niską emisję operacyjną CO2`.\n")
    lines.append("- Pytanie o biomasę (`L1545`) jest zgodne ze slajdem, lecz `bilans CO2 = zero` jest uproszczeniem. Bezpieczniejsze brzmienie: `w uproszczonym bilansie obiegu krótkiego węgla`.\n")
    lines.append("- Pary podobnych pytań w większości są dydaktycznie uzasadnione: porównują typy zależności, krzywe przeżywania albo typy biomów. Nie są duplikatami, ale zwiększają pamięciowy charakter banku.\n")

    lines.append("\n## Rekomendacje\n")
    lines.append("1. Dodać 6-10 pytań TF z poprawną odpowiedzią `Fałsz`, albo losować kolejność `Prawda/Fałsz`, bo teraz strategia `wybieraj Prawdę` daje 75% trafień.\n")
    lines.append("2. W single skrócić lub wyrównać 8 wskazanych odpowiedzi, gdzie poprawna jest wyraźnie dłuższa od dystraktorów.\n")
    lines.append("3. Utrzymać losowanie odpowiedzi jako obowiązkowe dla single/multi; przy wyłączeniu losowania wszystkie single mają poprawne A, a wszystkie multi mają poprawne odpowiedzi zgrupowane przed błędnymi.\n")
    lines.append("4. Zdecydować, czy quiz ma być `egzamin z tych PDF-ów`, czy `aktualna ekologia i prawo środowiskowe`. Dla wersji aktualnej trzeba zrewidować liczby i nazwy instytucji.\n")

    REPORT_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {FINDINGS_PATH}")
    print(json.dumps({
        "total": len(questions),
        "by_type": dict(by_type),
        "tf": len_stats["tf_correct_labels"],
        "tf_first_correct_pct": len_stats["tf_first_option_correct_pct"],
        "single_longest_pct": len_stats["single_correct_is_longest_pct"],
        "multi_grouped_pct": len_stats["multi_grouped_correct_first_pct"],
        "low_support": src["low_support_count"],
        "similar_pairs": len(dupes["similar"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
