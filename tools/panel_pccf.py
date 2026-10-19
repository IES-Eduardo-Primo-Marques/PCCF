#!/usr/bin/env python3
"""Panel de control de les Programacions: programacions/5_panel/panel.html.

Un sol fitxer HTML autocontingut (CSS, JS i dades dins), que s'obri amb
doble clic des de la carpeta sincronitzada d'OneDrive (file://, sense
servidor ni internet). Mostra l'estat de cada PD per departament i per
cicle, el docent, la FE, el PCCF, l'historial d'esdeveniments del poller
(panel_events), les alertes de sincronització d'OneDrive i la cua del log.

El crida el poller (pccf_sync_poller.py) al final de cada passada:
`actualitza()` només recalcula si hi ha hagut esdeveniments, si ha canviat
alguna font (comprovació barata per mtime) o si fa més de HEARTBEAT segons;
i només reescriu el fitxer si les dades han canviat o pel HEARTBEAT, perquè
OneDrive no el pugue a cada passada.

Ús manual:
    python3 tools/panel_pccf.py --root /home/PCCF/pccf_sync [--centre IESEPM]
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import time
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pccf_utils import (CICLES_INF, CICLES_SCO, DEPARTAMENTS, STATE_DIR, DIR_ESBORRANY_CICLE, DIR_ESBORRANY_DEPT,  # noqa: E402
                        DIR_FE, DIR_MODULS, DIR_PANEL, DIR_REPORT, DIR_REPORT_CICLE, DIR_REPORT_DEPT,
                        OPTATIVES_DIRNAME, get_curs, get_familia, get_hoja_label, get_moduls_del_cicle,
                        get_optatives_del_cicle)
import panel_events  # noqa: E402

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CICLES_ALL = CICLES_INF + CICLES_SCO
TEMPLATE = os.path.join(PROJECT_DIR, "templates", "panel", "panel.html.j2")
# Configuració del panel: fitxer extern, fora de git (mateix patró que
# department_emails.json i curs_actual.json). Sense fitxer, valors per defecte.
CONFIG_PATH = os.environ.get("PANEL_CONFIG_FILE", os.path.join(PROJECT_DIR, "panel_config.json"))
LOG_DIR = os.environ.get("PANEL_LOG_DIR", os.path.join(PROJECT_DIR, "temp", "logs"))
LOG_POLLER = os.path.join(LOG_DIR, "pccf_poller.log")
LOG_ONEDRIVE = os.path.join(LOG_DIR, "onedrive_pccf.log")
# Dades de l'últim panel (per a `activitat()`, que només canvia la capçalera)
# i estat de la generació (empremtes i hora).
CACHE_PATH = os.path.join(PROJECT_DIR, "temp", "panel_dades.json")
ESTAT_PATH = os.path.join(PROJECT_DIR, "temp", "panel_estat.json")
# Mòduls amb l'última compilació fallida: {"CICLE/CODI": {"t", "error"}}.
# L'escriu el poller (pccf_sync_poller.registra_resultat).
KO_PATH = os.path.join(STATE_DIR, "pd_ko_state.json")
PD_BUILD_STATE_PATH = os.path.join(STATE_DIR, "pd_build_state.json")
HEARTBEAT = 1800
LOG_MAX, LOG_CONSERVA = 5_000_000, 1_000_000
DOCENT_RE = re.compile(r"(?m)^\s*\**Docent\**\s*:\s*\**\s*(.+?)\s*$")
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)$")
NOMS_DEPT = {"INF": "Informàtica", "SCO": "Serveis a la Comunitat", "ANG": "Anglés", "FOL": "FOL"}
COLORS = ("verd", "blau", "groc", "gris", "roig")


# --- utilitats ----------------------------------------------------------------

def _llig_json(path, defecte=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {} if defecte is None else defecte


def _guarda_json(path, dades):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dades, f, ensure_ascii=False)


def escriu_atomic(path, text):
    """Escriu en un temporal ocult del mateix directori i el reanomena: OneDrive
    no veu mai el fitxer a mitges."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), f".{os.path.basename(path)}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _hora(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else None


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _enllac(prog_root, path):
    """Enllaç relatiu des de 5_panel/ (funciona en local, dins d'OneDrive)."""
    if not path or not os.path.exists(path):
        return None
    rel = os.path.relpath(path, os.path.join(prog_root, DIR_PANEL))
    return quote(rel.replace(os.sep, "/"))


def _docent(md):
    try:
        with open(md, encoding="utf-8") as f:
            m = DOCENT_RE.search(f.read())
    except OSError:
        return None
    return m.group(1).strip("* ") if m and "[" not in m.group(1) else None


def commit():
    """Commit desplegat: env GIT_COMMIT o .git del repositori."""
    if os.environ.get("GIT_COMMIT"):
        return os.environ["GIT_COMMIT"][:7]
    git = os.path.join(PROJECT_DIR, ".git")
    try:
        with open(os.path.join(git, "HEAD"), encoding="utf-8") as f:
            head = f.read().strip()
        if not head.startswith("ref: "):
            return head[:7]
        ref = head[5:]
        path = os.path.join(git, ref)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip()[:7]
        with open(os.path.join(git, "packed-refs"), encoding="utf-8") as f:
            for linia in f:
                if linia.strip().endswith(ref):
                    return linia[:7]
    except OSError:
        pass
    return None


def config():
    return _llig_json(CONFIG_PATH)


def curs_academic():
    path = os.environ.get("CURS_ACTUAL_FILE", os.path.join(PROJECT_DIR, "curs_actual.json"))
    return _llig_json(path).get("curs")


# --- logs ---------------------------------------------------------------------

def retalla_log(path, maxim=LOG_MAX, conserva=LOG_CONSERVA):
    """Si el log passa de `maxim` bytes, en deixa els últims `conserva`. El `tee`
    de l'entrypoint l'obri en mode append i continua escrivint al final."""
    try:
        if os.path.getsize(path) <= maxim:
            return
        with open(path, "rb") as f:
            f.seek(-conserva, os.SEEK_END)
            cua_bytes = f.read()
        cua_bytes = cua_bytes[cua_bytes.find(b"\n") + 1:]
        with open(path, "r+b") as f:
            f.truncate(0)
            f.write(cua_bytes)
    except OSError:
        pass


def cua(path, n=200, bytes_max=400_000):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            mida = f.tell()
            f.seek(max(0, mida - bytes_max))
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    linies = text.splitlines()
    if mida > bytes_max:
        linies = linies[1:]
    return linies[-n:]


def _ruta_onedrive(text):
    """Ruta relativa a 'General/PCCF i Programacions/' d'una línia d'onedrive."""
    i = text.find("PCCF i Programacions/")
    return text[i + len("PCCF i Programacions/"):].strip() if i >= 0 else text.strip()


def alertes_onedrive(linies):
    """Alertes a partir del log del client onedrive (línies amb hora):
    llibres bloquejats per un altre usuari (pendents mentre no es pugen),
    safeBackups creats i errors."""
    bloquejats, alertes = {}, []
    for linia in linies:
        m = TS_RE.match(linia)
        if not m:
            continue
        t, text = m.groups()
        if "locked for editing by another user:" in text:
            ruta = _ruta_onedrive(text.split("locked for editing by another user:", 1)[1])
            bloquejats[ruta] = bloquejats.get(ruta) or t
        elif text.startswith(("Uploading modified file:", "Uploading new file:")) and text.endswith("done"):
            ruta = _ruta_onedrive(text.split(":", 1)[1].rsplit(" ... ", 1)[0])
            if ruta in bloquejats:
                alertes.append({"t": t, "nivell": "ok", "tipus": "Desbloquejat i pujat",
                                "fitxer": ruta, "des_de": bloquejats.pop(ruta)})
        elif "safeBackup" in text and text.startswith("Moving "):
            ruta = _ruta_onedrive(text[len("Moving "):].split(" to ", 1)[0])
            bloquejats.pop(ruta, None)  # el bloqueig s'ha resolt amb un conflicte
            alertes.append({"t": t, "nivell": "roig", "tipus": "Conflicte (safeBackup)", "fitxer": ruta})
        elif text.startswith("Downloading file:") and text.endswith("done"):
            # S'ha baixat la versió del núvol: la local ja no està pendent de pujar
            ruta = _ruta_onedrive(text.split(":", 1)[1].rsplit(" ... ", 1)[0])
            if ruta in bloquejats:
                alertes.append({"t": t, "nivell": "groc", "tipus": "Bloqueig resolt baixant la versió del núvol",
                                "fitxer": ruta, "des_de": bloquejats.pop(ruta)})
        elif "failed!" in text and _ruta_onedrive(text.split(":", 1)[-1].rsplit(" ... ", 1)[0]) in bloquejats:
            continue
        elif re.search(r"\bERROR\b", text) or "failed!" in text:
            alertes.append({"t": t, "nivell": "groc", "tipus": "Error d'OneDrive", "fitxer": _ruta_onedrive(text)})
    for ruta, t in bloquejats.items():
        alertes.append({"t": t, "nivell": "roig", "tipus": "Bloquejat a Excel Online: no es pot pujar",
                        "fitxer": ruta, "pendent": True})
    return sorted(alertes, key=lambda a: a["t"], reverse=True)[:60]


def fitxers_conflicte(sync_root):
    """safeBackup i «conflicted copy» que hi ha ara mateix a la carpeta."""
    res = []
    for arrel, dirs, fitxers in os.walk(sync_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in fitxers:
            if "safeBackup" in f or "conflicted copy" in f:
                p = os.path.join(arrel, f)
                res.append({"fitxer": os.path.relpath(p, sync_root), "t": _hora(_mtime(p))})
    return sorted(res, key=lambda x: x["fitxer"])


# --- dades ----------------------------------------------------------------------

def _color(m):
    if m["ko"]:
        return "roig"
    if m["estat"] == "FALTA":
        return "gris"
    if m["estat"] == "BORRADOR":
        return "groc"
    return "verd" if m["verificat"] else "blau"


def _resum(moduls):
    r = {c: 0 for c in COLORS}
    for m in moduls:
        r[m["color"]] += 1
    r["total"] = len(moduls)
    r["pct"] = round(100 * r["verd"] / len(moduls)) if moduls else 0
    r["compilar"] = sum(1 for m in moduls if m["compila"])
    return r


def _moduls_cicle(cicle, sync_root, prog_root, centre, ara, cfg, build_state, ko_state, debounce):
    from report_pccf import compute_pd_status, estat_moduls_cicle, modul_verificat
    import pd_build
    familia = get_familia(cicle)
    pd_dir = os.path.join(prog_root, cicle)
    if not os.path.isdir(pd_dir):
        return [], None
    status = compute_pd_status(cicle, familia, pd_dir)
    fitxers = {p["codi"]: os.path.join(pd_dir, p["filename"]) for p in status["borrador"] + status["ok"]}
    for o in status.get("optatives", []):
        if o["fitxer"]:
            fitxers[str(o["codi"])] = os.path.join(prog_root, OPTATIVES_DIRNAME, o["fitxer"])
    json_moduls = {str(c): m for c, m in get_moduls_del_cicle(cicle, familia).items()}
    json_moduls.update({str(c): m for c, m in get_optatives_del_cicle(cicle, familia)})
    try:
        fps = pd_build.empremtes(cicle, prog_root)
    except Exception:
        fps = {}
    dies_max = cfg.get("dies_sense_canvis", 14)

    moduls = []
    for m in estat_moduls_cicle(cicle, prog_root, status):
        codi = str(m["codi"])
        md = fitxers.get(codi)
        modul = json_moduls.get(codi, {})
        pdfs = glob.glob(os.path.join(prog_root, DIR_MODULS, m["departament"], f"PD_{cicle}_{codi}_*.pdf"))
        compila = None
        fp = fps.get(codi)
        if fp and build_state.get(f"{cicle}/{codi}") != fp["empremta"]:
            compila = "espera" if ara - fp["mtime"] < debounce else "pendent"
        md_t = _mtime(md) if md else 0
        ko = ko_state.get(f"{cicle}/{codi}")
        m2 = {
            "cicle": cicle, "codi": codi, "nom": m["nom"], "sigla": get_hoja_label(m["nom"]),
            "departament": m["departament"], "curs": get_curs(modul) or (2 if codi in dict(
                get_optatives_del_cicle(cicle, familia)) else None),
            "optativa": codi not in {str(c) for c in get_moduls_del_cicle(cicle, familia)},
            "estat": m["estat"], "marques": m["marques"], "llocs": m["llocs"][:15],
            "excel": m["excel"], "fe": m["fe"], "verificat": modul_verificat(m),
            "docent": _docent(md) if md else None,
            "fitxer": os.path.basename(md) if md else None, "md": _enllac(prog_root, md),
            "md_t": _hora(md_t), "dies": int((ara - md_t) // 86400) if md_t else None,
            "pdf": _enllac(prog_root, pdfs[0]) if pdfs else None,
            "pdf_t": _hora(_mtime(pdfs[0])) if pdfs else None,
            "compila": compila, "emp": fp["empremta"] if fp else None, "ko": ko,
        }
        m2["vell"] = bool(m2["dies"] is not None and m2["dies"] >= dies_max and not m2["verificat"])
        m2["color"] = _color(m2)
        m2["incid"] = m2["marques"] + len(m2["excel"]) + len(m2["fe"])
        moduls.append(m2)
    return moduls, status


def _arbre(moduls_per_cicle, agrupa_per_dept, prog_root, centre):
    """Departament → cicle → curs → mòduls (o cicle → curs → mòduls)."""
    def cursos(ms):
        per = {}
        for m in ms:
            per.setdefault(m["curs"], []).append(m)
        return [{"curs": c, "nom": f"{c}r curs" if c == 1 else f"{c}n curs" if c == 2 else "Sense curs",
                 "moduls": sorted(v, key=lambda m: (m["optativa"], m["codi"])), "resum": _resum(v)}
                for c, v in sorted(per.items(), key=lambda kv: kv[0] or 9)]

    def node_cicle(cicle, ms):
        fam = get_familia(cicle)
        return {
            "cicle": cicle, "nom": _nom_cicle(cicle), "resum": _resum(ms), "cursos": cursos(ms),
            "pdf": _enllac(prog_root, os.path.join(prog_root, DIR_ESBORRANY_CICLE, f"Programaciones_{centre}_{cicle}.pdf")),
            "report": _enllac(prog_root, os.path.join(prog_root, DIR_REPORT, DIR_REPORT_CICLE, f"{fam}_{cicle}.txt")),
            "llibre": _enllac(prog_root, os.path.join(prog_root, cicle, f"libro_{cicle}.xlsx")),
        }

    if not agrupa_per_dept:
        return [node_cicle(c, ms) for c, ms in moduls_per_cicle.items() if ms]
    arbre = []
    for dept in DEPARTAMENTS:
        cicles = [node_cicle(c, [m for m in ms if m["departament"] == dept])
                  for c, ms in moduls_per_cicle.items()]
        cicles = [c for c in cicles if c["resum"]["total"]]
        if not cicles:
            continue
        tots = [m for c in cicles for cu in c["cursos"] for m in cu["moduls"]]
        arbre.append({
            "dept": dept, "nom": NOMS_DEPT.get(dept, dept), "resum": _resum(tots), "cicles": cicles,
            "pdf": _enllac(prog_root, os.path.join(prog_root, DIR_ESBORRANY_DEPT, f"Programaciones_{centre}_{dept}.pdf")),
            "report": _enllac(prog_root, os.path.join(prog_root, DIR_REPORT, DIR_REPORT_DEPT, dept, f"report_{dept}.txt")),
        })
    return arbre


def _nom_cicle(cicle):
    try:
        import genera_fe
        nom = genera_fe.nom_cicle(cicle)
        return nom.split(" — ", 1)[1] if " — " in nom else ""
    except Exception:
        return ""


def _docents(moduls):
    per = {}
    for m in moduls:
        per.setdefault(m["docent"] or "", []).append(m)
    res = [{"nom": nom or "Sense docent assignat", "sense": not nom,
            "moduls": sorted(ms, key=lambda m: (m["cicle"], m["codi"])), "resum": _resum(ms)}
           for nom, ms in per.items()]
    return sorted(res, key=lambda d: (not d["sense"], -d["resum"]["total"] + d["resum"]["verd"], d["nom"]))


def _fe(sync_root, prog_root, curs_acad, cfg):
    import genera_fe
    objectius = cfg.get("objectiu_fe", {}).get(curs_acad or "", {})
    res = []
    for cicle in CICLES_ALL:
        if not os.path.isdir(os.path.join(prog_root, cicle)):
            continue
        try:
            moduls = genera_fe.estat_cicle(cicle, sync_root)
        except Exception as e:
            res.append({"cicle": cicle, "error": str(e), "cursos": []})
            continue
        if not moduls:
            continue
        cursos = []
        for curs in sorted({m["curs"] for m in moduls}, key=lambda c: c or 9):
            ms = [m for m in moduls if m["curs"] == curs]
            sufix = {1: "1r", 2: "2n"}.get(curs, "sense_curs")
            hores = round(sum(m["hores"] or 0 for m in ms), 1)
            objectiu = objectius.get(cicle, {}).get(str(curs))
            cursos.append({
                "curs": curs, "nom": {1: "1r curs", 2: "2n curs"}.get(curs, "Sense curs"),
                "hores": hores, "objectiu": objectiu,
                "pct": min(100, round(100 * hores / objectiu)) if objectiu else None,
                "complets": sum(1 for m in ms if not m["incidencies"]), "total": len(ms),
                "pendents": [{"codi": m["codi"], "nom": m["nom"], "docent": m["docent"],
                              "incid": m["incidencies"], "hores": m["hores"]} for m in ms if m["incidencies"]],
                "moduls": [{"codi": m["codi"], "sigla": m["sigles"].split("_", 1)[-1], "hores": m["hores"]}
                           for m in ms],
                "docx": _enllac(prog_root, os.path.join(prog_root, DIR_FE, f"RRAA_CA_{cicle}_{sufix}.docx")),
            })
        res.append({"cicle": cicle, "cursos": cursos})
    return res


def _pccf(sync_root, centre):
    from report_pccf import compute_pccf_status
    pccf_dir = os.path.join(sync_root, "pccf")
    prog_root = os.path.join(sync_root, "programacions")
    res = []
    for cicle in CICLES_ALL:
        try:
            st = compute_pccf_status(cicle, get_familia(cicle), pccf_dir)
        except Exception as e:
            res.append({"cicle": cicle, "error": str(e)})
            continue
        if not st.get("dir_found"):
            continue
        pdf = os.path.join(pccf_dir, "1_esborrany", f"PCCF_{centre}_{cicle}.pdf")
        res.append({
            "cicle": cicle, "marques": st["total_places"],
            "fitxers": [{"fitxer": f, "n": len(ll)} for f, ll in st["placeholders"]][:20],
            "pdf": _enllac(prog_root, pdf), "pdf_t": _hora(_mtime(pdf)),
        })
    return res


def _evolucio(dir_historial, depts, total, avui):
    """Una instantània diària del % verificat (evolucio.jsonl) i les sèries per
    a les gràfiques (últims 90 dies)."""
    path = os.path.join(dir_historial, "evolucio.jsonl")
    punts = []
    try:
        with open(path, encoding="utf-8") as f:
            punts = [json.loads(l) for l in f if l.strip()]
    except (OSError, json.JSONDecodeError):
        punts = []
    actual = {"data": avui, "total": total, "depts": depts}
    if not punts or punts[-1].get("data") != avui:
        try:
            os.makedirs(dir_historial, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(actual, ensure_ascii=False) + "\n")
        except OSError:
            pass
        punts.append(actual)
    else:
        punts[-1] = actual
    punts = punts[-90:]
    series = {"Total": [p.get("total", 0) for p in punts]}
    for d in DEPARTAMENTS:
        series[d] = [p.get("depts", {}).get(d) for p in punts]
    return {"dates": [p["data"] for p in punts], "series": [
        {"nom": nom, "valors": v, "punts": _polyline(v), "ultim": next((x for x in reversed(v) if x is not None), None)}
        for nom, v in series.items() if any(x is not None for x in v)]}


def _polyline(valors, amplaria=220, alcaria=44):
    n = len(valors)
    if not n:
        return ""
    pas = amplaria / max(1, n - 1)
    return " ".join(f"{i * pas:.1f},{alcaria - (v or 0) * alcaria / 100:.1f}"
                    for i, v in enumerate(valors) if v is not None)


def _te_trigger(directori):
    """Hi ha un COMPILAR_ARA (o .md/.txt) a `directori`? El mateix criteri que
    pccf_sync_poller.find_pd_triggers (no s'importa: el poller importa este mòdul)."""
    try:
        return any(f.upper() in ("COMPILAR_ARA", "COMPILAR_ARA.MD", "COMPILAR_ARA.TXT")
                   for f in os.listdir(directori))
    except OSError:
        return False


def _triggers(prog_root):
    res = ["tots els cicles"] if _te_trigger(prog_root) else []
    return res + [c for c in CICLES_ALL if _te_trigger(os.path.join(prog_root, c))]


def dades(sync_root, centre, activitat=""):
    prog_root = os.path.join(sync_root, "programacions")
    ara = time.time()
    cfg = config()
    curs_acad = curs_academic()
    build_state = _llig_json(PD_BUILD_STATE_PATH)
    ko_state = _llig_json(KO_PATH)
    debounce = int(os.environ.get("PD_BUILD_DEBOUNCE", "600"))

    per_cicle = {}
    for cicle in CICLES_ALL:
        try:
            per_cicle[cicle], _ = _moduls_cicle(cicle, sync_root, prog_root, centre, ara, cfg,
                                                build_state, ko_state, debounce)
        except Exception as e:
            print(f"[panel] {cicle}: error calculant l'estat: {e}", flush=True)
            per_cicle[cicle] = []
    tots = [m for ms in per_cicle.values() for m in ms]
    arbre_dept = _arbre(per_cicle, True, prog_root, centre)

    historial = os.path.join(prog_root, DIR_PANEL, "historial")
    log_od = cua(LOG_ONEDRIVE, 4000, 2_000_000)
    limit = cfg.get("data_limit_pd")
    dies_limit = None
    if limit:
        try:
            dies_limit = (datetime.date.fromisoformat(limit) - datetime.date.today()).days
        except ValueError:
            limit = None
    try:
        disc = shutil.disk_usage(sync_root)
        disc = {"lliure_gb": round(disc.free / 1e9, 1), "pct": round(100 * disc.used / disc.total)}
    except OSError:
        disc = None
    from mailer import smtp_configured

    resum = _resum(tots)
    return {
        "generat": datetime.datetime.fromtimestamp(ara).strftime("%Y-%m-%d %H:%M:%S"),
        "generat_ts": int(ara * 1000),
        "centre": centre, "curs": curs_acad, "commit": commit(), "activitat": activitat,
        "interval": int(os.environ.get("POLLER_INTERVAL", "300")), "heartbeat": HEARTBEAT,
        "limit": limit, "dies_limit": dies_limit, "dies_sense_canvis": cfg.get("dies_sense_canvis", 14),
        "resum": resum,
        "depts": arbre_dept,
        "cicles": _arbre(per_cicle, False, prog_root, centre),
        "docents": _docents(tots),
        "vells": sorted([m for m in tots if m["vell"]], key=lambda m: -(m["dies"] or 0)),
        "fe": _fe(sync_root, prog_root, curs_acad, cfg),
        "pccf": _pccf(sync_root, centre),
        "triggers": _triggers(prog_root),
        "events": panel_events.llig(historial),
        "tipus_events": panel_events.TIPUS,
        "alertes": alertes_onedrive(log_od),
        "conflictes": fitxers_conflicte(sync_root),
        "log": cua(LOG_POLLER, 250),
        "log_onedrive": [l for l in log_od if "integrity" not in l][-120:],
        "evolucio": _evolucio(historial, {d["dept"]: d["resum"]["pct"] for d in arbre_dept},
                              resum["pct"], datetime.date.today().isoformat()),
        "salut": {"smtp": smtp_configured(), "disc": disc, "debounce": debounce,
                  "log_onedrive_t": _hora(_mtime(LOG_ONEDRIVE)), "log_poller_t": _hora(_mtime(LOG_POLLER))},
    }


# --- render i escriptura ----------------------------------------------------------

def render(d):
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(TEMPLATE)),
                             autoescape=True, trim_blocks=True, lstrip_blocks=True)
    return env.get_template(os.path.basename(TEMPLATE)).render(d=d)


def _empremta(d):
    """El que, si canvia, obliga a reescriure el panel (sense hores ni log)."""
    claus = ("depts", "fe", "pccf", "triggers", "events", "alertes", "conflictes", "activitat", "limit", "commit")
    return hashlib.sha1(json.dumps({k: d.get(k) for k in claus}, sort_keys=True,
                                   ensure_ascii=False, default=str).encode()).hexdigest()


def _empremta_fonts(sync_root):
    """Comprovació barata per a saber si cal recalcular: mtimes de les PD, els
    llibres, l'historial i el log d'onedrive."""
    prog_root = os.path.join(sync_root, "programacions")
    vals = []
    for c in CICLES_ALL + [OPTATIVES_DIRNAME]:
        d = os.path.join(prog_root, c)
        try:
            vals += [(f, _mtime(os.path.join(d, f))) for f in sorted(os.listdir(d))]
        except OSError:
            pass
    vals.append(("od", _mtime(LOG_ONEDRIVE)))
    vals.append(("pccf", max((_mtime(p) for p in glob.glob(os.path.join(sync_root, "pccf", "1_esborrany", "*.pdf"))), default=0)))
    vals.append(("build", _mtime(PD_BUILD_STATE_PATH)))
    vals.append(("config", _mtime(CONFIG_PATH)))  # canviar la configuració al servidor es veu de seguida
    vals.append(("conflictes", [f["fitxer"] for f in fitxers_conflicte(sync_root)]))
    return hashlib.sha1(repr(vals).encode()).hexdigest()


def actualitza(sync_root, centre, forcat=False, activitat=""):
    """Regenera el panel si cal (vore el docstring del mòdul). Mai llança
    excepció: el panel no ha de poder aturar el poller."""
    try:
        for log in (LOG_POLLER, LOG_ONEDRIVE):
            retalla_log(log)
        estat = _llig_json(ESTAT_PATH)
        ara = time.time()
        fonts = _empremta_fonts(sync_root)
        heartbeat = ara - estat.get("escrit", 0) >= HEARTBEAT
        pendent = "dades" in estat and estat["dades"] is None  # després d'`activitat()`
        if not (forcat or heartbeat or pendent or fonts != estat.get("fonts")):
            return False
        d = dades(sync_root, centre, activitat)
        emp = _empremta(d)
        _guarda_json(CACHE_PATH, d)
        if emp == estat.get("dades") and not heartbeat and not pendent:
            _guarda_json(ESTAT_PATH, {**estat, "fonts": fonts})
            return False
        escriu_atomic(os.path.join(sync_root, "programacions", DIR_PANEL, "panel.html"), render(d))
        _guarda_json(ESTAT_PATH, {"fonts": fonts, "dades": emp, "escrit": ara})
        return True
    except Exception as e:
        print(f"[panel] ERROR generant el panel: {e}", flush=True)
        return False


def _moduls_node(node):
    """Mòduls d'un node de l'arbre (curs, cicle, departament o docent)."""
    if "moduls" in node:
        return node["moduls"]
    return [m for fill in node.get("cursos", node.get("cicles", [])) for m in _moduls_node(fill)]


def _refresca_compilats(d):
    """Lleva la marca «per compilar» dels mòduls que el poller ha compilat
    després de calcular `d` (la seua empremta ja és a pd_build_state.json) i
    torna a comptar els pendents de cada resum. Sense llegir cap Excel."""
    build_state = _llig_json(PD_BUILD_STATE_PATH)

    def recorre(x):
        if isinstance(x, list):
            for y in x:
                recorre(y)
        elif isinstance(x, dict):
            if x.get("compila") and x.get("emp") and build_state.get(f"{x['cicle']}/{x['codi']}") == x["emp"]:
                x["compila"] = None
            for v in x.values():
                recorre(v)
            if "resum" in x and any(k in x for k in ("moduls", "cursos", "cicles")):
                x["resum"]["compilar"] = sum(1 for m in _moduls_node(x) if m["compila"])

    recorre(d)
    d["resum"]["compilar"] = sum(1 for c in d["cicles"] for m in _moduls_node(c) if m["compila"])


def activitat(sync_root, text):
    """Canvia l'activitat actual de la capçalera («compilant DAM…») sobre les
    dades de l'últim panel, i refresca només el que és barat: alertes i
    fitxers en conflicte d'OneDrive, disparadors, logs i els mòduls que ja
    s'han compilat en esta passada."""
    d = _llig_json(CACHE_PATH)
    if not d:
        return
    try:
        d["activitat"] = text
        d["generat"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        d["generat_ts"] = int(time.time() * 1000)
        d["log"] = cua(LOG_POLLER, 250)
        # El que és barat de calcular es refresca (la resta, a la pròxima `actualitza()`)
        log_od = cua(LOG_ONEDRIVE, 4000, 2_000_000)
        d["alertes"] = alertes_onedrive(log_od)
        d["log_onedrive"] = [l for l in log_od if "integrity" not in l][-120:]
        d["conflictes"] = fitxers_conflicte(sync_root)
        d["triggers"] = _triggers(os.path.join(sync_root, "programacions"))
        _refresca_compilats(d)
        escriu_atomic(os.path.join(sync_root, "programacions", DIR_PANEL, "panel.html"), render(d))
        # La pròxima `actualitza()` l'ha de reescriure (sense l'activitat)
        # encara que les dades no hagen canviat.
        _guarda_json(ESTAT_PATH, {**_llig_json(ESTAT_PATH), "dades": None})
    except Exception as e:
        print(f"[panel] ERROR actualitzant l'activitat: {e}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", required=True, help="PCCF_ROOT (al contenidor: /home/PCCF/pccf_sync)")
    ap.add_argument("--centre", default=os.environ.get("CENTRO_EDUCATIVO", "IESEPM"))
    ap.add_argument("--sortida", help="Escriu el panel ací en lloc de programacions/5_panel/panel.html")
    args = ap.parse_args()
    panel_events.configura(os.path.join(args.root, "programacions"))
    d = dades(args.root, args.centre)
    _guarda_json(CACHE_PATH, d)
    desti = args.sortida or os.path.join(args.root, "programacions", DIR_PANEL, "panel.html")
    escriu_atomic(desti, render(d))
    print(f"Panel escrit a {desti}")


if __name__ == "__main__":
    main()
