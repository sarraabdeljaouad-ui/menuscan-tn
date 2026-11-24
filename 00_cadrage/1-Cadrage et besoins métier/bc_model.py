# -*- coding: utf-8 -*-
"""Modèle du business case MenuScan TN (MS-DATA-BC-001). Usage : python bc_model.py 185 (coût d'une journée interne en DT)."""
import json, sys

ACTIFS, MRR, MKT = 265, 8510, 11135
ARPA = MRR / ACTIFS
JOURS_BUILD, JOURS_MAINT, SERVEUR = 80, 24, 600
SCEN = {"Prudent": (0.003, 0.05, 5, 2), "Central": (0.005, 0.10, 10, 4), "Optimiste": (0.008, 0.15, 15, 5)}


def scenario(tj, dc, mk, up, h):
    build, rec = JOURS_BUILD * tj, JOURS_MAINT * tj + SERVEUR
    l = [ACTIFS * dc * 12 * ARPA * 12, MKT * mk, up * 20 * 6, h * 46 / 8 * tj]
    b = sum(l)
    f = [-build, 0.5 * b - rec, b - rec, b - rec]
    cum = [sum(f[:i + 1]) for i in range(4)]
    cout = build + 3 * rec
    roi = 100 * (2.5 * b - cout) / cout
    van = sum(x / 1.1 ** t for t, x in enumerate(f))
    pay = next((i - 1 + (-cum[i - 1]) / f[i] for i in range(1, 4) if cum[i] >= 0 > cum[i - 1]), None)
    return dict(l=l, b=b, f=f, cum=cum, cout=cout, build=build, rec=rec, roi=roi, van=van, pay=pay, gains3=2.5 * b, retenus=ACTIFS * dc * 12)


def seuil(tj):
    lo, hi = 0.0, 0.02
    for _ in range(60):
        m = (lo + hi) / 2
        if scenario(tj, m, *SCEN["Central"][1:])["roi"] < 0:
            lo = m
        else:
            hi = m
    return 100 * hi


if __name__ == "__main__":
    tj = float(sys.argv[1])
    R = {k: scenario(tj, *v) for k, v in SCEN.items()}
    R["sens_dc"] = {str(d): scenario(tj, d, *SCEN["Central"][1:]) for d in (0.002, 0.003, 0.005, 0.008, 0.01)}
    R["sens_tj"] = {str(t): scenario(t, *SCEN["Central"]) for t in (100, 150, 185, 200, 250)}
    R["seuil"] = seuil(tj)
    R["tj"] = tj
    json.dump(R, open(f"bc_{int(tj)}.json", "w"), indent=1)
    for k in ("Prudent", "Central", "Optimiste"):
        r = R[k]; print(k, round(r["b"], 1), [round(x) for x in r["l"]], "roi", round(r["roi"], 1), "van", round(r["van"], 1), "pay", r["pay"] and round(r["pay"], 2), [round(x) for x in r["cum"]])
    print("cout", R["Central"]["build"], R["Central"]["rec"], R["Central"]["cout"], "seuil", round(R["seuil"], 3))
    for d, r in R["sens_dc"].items(): print("dc", d, round(r["roi"], 1), round(r["van"]))
    for t, r in R["sens_tj"].items(): print("tj", t, round(r["roi"], 1), round(r["van"]))
