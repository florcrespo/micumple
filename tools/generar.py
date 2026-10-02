"""Genera la grilla del crucigrama a partir de palabras.json -> crucigrama.js"""
import json, random, hashlib, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "tools", "palabras.json"), encoding="utf-8"))
words = [(d["palabra"].upper(), d["pista"]) for d in data]

def try_build(order, rng):
    grid = {}  # (r,c) -> letter
    placed = []  # (word, clue, r, c, dir)

    def can_place(w, r, c, d):
        dr, dc = (0, 1) if d == "A" else (1, 0)
        # cell before / after must be empty
        if (r - dr, c - dc) in grid or (r + dr * len(w), c + dc * len(w)) in grid:
            return -1
        crosses = 0
        for i, ch in enumerate(w):
            rr, cc = r + dr * i, c + dc * i
            g = grid.get((rr, cc))
            if g is not None:
                if g != ch:
                    return -1
                # must not run parallel to an existing word in same direction
                for (pw, _, pr, pc, pd) in placed:
                    if pd == d:
                        pdr, pdc = (0, 1) if pd == "A" else (1, 0)
                        for j in range(len(pw)):
                            if (pr + pdr * j, pc + pdc * j) == (rr, cc):
                                return -1
                crosses += 1
            else:
                # side neighbours must be empty
                if ((rr + dc, cc + dr) in grid) or ((rr - dc, cc - dr) in grid):
                    return -1
        return crosses

    def bounds(extra=None):
        cells = list(grid.keys()) + (extra or [])
        rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
        return min(rs), max(rs), min(cs), max(cs)

    w0, c0 = order[0]
    d0 = rng.choice("AD")
    for i, ch in enumerate(w0):
        grid[(0, i) if d0 == "A" else (i, 0)] = ch
    placed.append((w0, c0, 0, 0, d0))
    pending = list(order[1:])
    stuck = 0
    while pending:
        progress = False
        for item in list(pending):
            w, clue = item
            best = None
            for (gr, gc), gch in list(grid.items()):
                for i, ch in enumerate(w):
                    if ch != gch:
                        continue
                    for d in "AD":
                        r, c = (gr, gc - i) if d == "A" else (gr - i, gc)
                        x = can_place(w, r, c, d)
                        if x < 1:
                            continue
                        dr, dc = (0, 1) if d == "A" else (1, 0)
                        newcells = [(r + dr * k, c + dc * k) for k in range(len(w))]
                        r0, r1, c0_, c1 = bounds(newcells)
                        h, wd = r1 - r0 + 1, c1 - c0_ + 1
                        score = max(h, wd) * 3 + h + wd - x * 4 + abs(h - wd * 1.15) + rng.random() * 3
                        if best is None or score < best[0]:
                            best = (score, r, c, d)
            if best:
                _, r, c, d = best
                dr, dc = (0, 1) if d == "A" else (1, 0)
                for k, ch in enumerate(w):
                    grid[(r + dr * k, c + dc * k)] = ch
                placed.append((w, clue, r, c, d))
                pending.remove(item)
                progress = True
        if not progress:
            return None
    r0, r1, c0_, c1 = bounds()
    return grid, placed, (r0, r1, c0_, c1)

best = None
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rng = random.Random(seed)
for attempt in range(4000):
    order = words[:]
    rng.shuffle(order)
    order.sort(key=lambda x: -len(x[0]) + rng.random() * 6)
    res = try_build(order, rng)
    if not res:
        continue
    grid, placed, (r0, r1, c0, c1) = res
    h, w = r1 - r0 + 1, c1 - c0 + 1
    score = max(w, h) * 10 + w * 3 + h  # width matters most on a phone
    if best is None or score < best[0]:
        best = (score, res)
        print(attempt, "size", w, "x", h, file=sys.stderr)

_, (grid, placed, (r0, r1, c0, c1)) = best
H, W = r1 - r0 + 1, c1 - c0 + 1
# numbering
starts = {}
for (w, clue, r, c, d) in placed:
    starts.setdefault((r - r0, c - c0), []).append((w, clue, d))
num = {}
n = 1
for pos in sorted(starts):
    num[pos] = n; n += 1
entries = []
for (w, clue, r, c, d) in placed:
    pos = (r - r0, c - c0)
    entries.append({"n": num[pos], "dir": d, "row": pos[0], "col": pos[1], "len": len(w),
                    "clue": clue, "h": hashlib.sha256(w.encode()).hexdigest()[:16]})
entries.sort(key=lambda e: (e["dir"], e["n"]))
mask = ["".join("#" if (r + r0, c + c0) in grid else "." for c in range(W)) for r in range(H)]
solution = "".join(grid[(r + r0, c + c0)] for r in range(H) for c in range(W) if (r + r0, c + c0) in grid)
out = {"rows": H, "cols": W, "mask": mask, "entries": entries,
       "hash": hashlib.sha256(solution.encode()).hexdigest()}
with open(os.path.join(ROOT, "crucigrama.js"), "w", encoding="utf-8") as f:
    f.write("// Generado por tools/generar.py — no editar a mano\n")
    f.write("window.CRUCIGRAMA = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")

# Respuestas ofuscadas (solo se cargan cuando alguien abandona)
import base64
KEY = b"flopicretense28"
sol_bytes = solution.encode("utf-8")
enc = base64.b64encode(bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(sol_bytes))).decode()
with open(os.path.join(ROOT, "respuestas.js"), "w", encoding="utf-8") as f:
    f.write("// Generado por tools/generar.py — no editar a mano\n")
    f.write("window.RESPUESTAS = " + json.dumps(enc) + ";\n")
for r in range(H):
    print(" ".join(grid.get((r + r0, c + c0), ".") for c in range(W)))
print(W, "x", H, len(placed), "palabras")
