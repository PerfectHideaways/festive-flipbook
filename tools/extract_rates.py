import fitz, re, json, sys

SRC = sys.argv[1]
OUT = sys.argv[2]
d = fitz.open(SRC)

SECTION_LABEL = {
    "KAROO": "Karoo", "GARDEN ROUTE": "Garden Route", "WEST COAST": "West Coast", "WINELANDS": "Winelands",
    "OVERBERG": "Overberg", "CAPE TOWN (SURROUNDS)": "Cape Town and surrounds", "KWAZULU-NATAL": "KwaZulu-Natal",
    "SAFARI": "Safari", "OTHER": "Other",
}
COLS = ["HIDEAWAY", "LOCATION", "SLEEPS", "RATE PER NIGHT", "AVAILABILITY"]


def clean(t):
    t = t.replace("�", "’").replace("‑", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


result = {}
problems = []
for pi, p in enumerate(d):
    if "RATE PER NIGHT" not in p.get_text():
        continue
    k = pi + 1                      # PDF page number (1-based)
    first_img = 2 * k - 3           # 0-based index of the left-hand page image of this spread
    lines = []
    for b in p.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = clean("".join(s["text"] for s in l["spans"]))
            if t:
                lines.append((t, l["bbox"]))
    H = {t: (bb[0] + bb[2]) / 2 for t, bb in lines if t in COLS}
    if len(H) != 5:
        problems.append((k, "header columns found: %s" % list(H)))
        continue
    cols = sorted(H.items(), key=lambda kv: kv[1])
    hy = [bb[3] for t, bb in lines if t == "HIDEAWAY"][0]
    section = None
    for t, bb in lines:
        if t in SECTION_LABEL:
            section = SECTION_LABEL[t]
    body = [(t, bb) for t, bb in lines
            if bb[1] > hy and t not in H and t != "Rates & Dates" and t not in SECTION_LABEL]
    names = sorted([(bb, t) for t, bb in body if abs((bb[0] + bb[2]) / 2 - H["HIDEAWAY"]) < 70], key=lambda x: (x[0][1] + x[0][3]) / 2)
    rows = [{"y": (bb[1] + bb[3]) / 2, "bb": bb, "c": {"hideaway": t}} for bb, t in names]
    key = {"LOCATION": "location", "SLEEPS": "sleeps", "RATE PER NIGHT": "rate", "AVAILABILITY": "availability"}
    for t, bb in body:
        cx = (bb[0] + bb[2]) / 2
        cy = (bb[1] + bb[3]) / 2
        col = min(cols, key=lambda kv: abs(kv[1] - cx))[0]
        if col == "HIDEAWAY":
            continue
        r = min(rows, key=lambda r: abs(r["y"] - cy))
        f = key[col]
        r["c"][f] = (r["c"].get(f, "") + " " + t).strip() if f in r["c"] else t
    links = [(fitz.Rect(l["from"]), l["uri"]) for l in p.get_links() if l.get("uri")]
    out_rows = []
    for r in rows:
        c = r["c"]
        rect = fitz.Rect(r["bb"])
        url = next((u for lr, u in links if lr.intersects(rect)), None)
        for f in ("location", "sleeps", "rate", "availability"):
            if f not in c:
                problems.append((k, "%s missing %s" % (c["hideaway"], f)))
        out_rows.append({"hideaway": c["hideaway"], "url": url, "location": c.get("location", ""),
                         "sleeps": c.get("sleeps", ""), "rate": c.get("rate", ""), "availability": c.get("availability", "")})
        if not url:
            problems.append((k, "%s has no link" % c["hideaway"]))
    result[str(first_img)] = {"pdfPage": k, "section": section, "rows": out_rows}

if OUT.endswith(".js"):
    header = "// Rates tables for the phone layout. Generated from the PDF by tools/extract_rates.py; do not edit by hand.\n"
    body = "window.RATES = " + json.dumps(result, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(OUT, "w", encoding="utf-8").write(header + body)
else:
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("table spreads:", len(result), "| rows:", sum(len(v["rows"]) for v in result.values()))
for fi, v in result.items():
    print("PDF page %2d -> images %s-%s | %-24s | %d rows" % (v["pdfPage"], int(fi) + 1, int(fi) + 2, v["section"], len(v["rows"])))
print("problems:", problems or "none")
