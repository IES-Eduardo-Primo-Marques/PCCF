#!/usr/bin/env python3
"""Historial d'esdeveniments del poller de PCCF per al panel (5_panel).

Cada esdeveniment és una línia JSON a
programacions/5_panel/historial/events_AAAA-MM.jsonl, dins de la carpeta
sincronitzada: així sobreviu als redesplegaments (temp/ es perd) i el panel
el pot mostrar. Sense `configura()` (p. ex. el poller de memòries, que també
usa el mailer) `registra()` no fa res.

Tipus d'esdeveniment (`TIPUS`): vore el diccionari, el panel en mostra
l'etiqueta.
"""

import datetime
import glob
import json
import os

TIPUS = {
    "pd_modificada": "PD modificada",
    "pd_esborrada": "PD esborrada",
    "compilar_ara": "COMPILAR_ARA",
    "compilacio_ok": "Compilació correcta",
    "compilacio_ko": "Compilació fallida",
    "pccf_ok": "PCCF compilat",
    "pccf_ko": "PCCF fallit",
    "correu": "Correu enviat",
    "error": "Error",
    "arrencada": "Arrencada del poller",
}

_dir = None
_comptador = 0  # esdeveniments registrats des de l'últim `reinicia_comptador()`


def configura(prog_root):
    """Activa el registre a {prog_root}/5_panel/historial."""
    global _dir
    from pccf_utils import DIR_PANEL
    _dir = os.path.join(prog_root, DIR_PANEL, "historial")


def directori():
    return _dir


def registra(tipus, cicle=None, codi=None, detall=""):
    """Afig un esdeveniment al fitxer del mes. Mai llança excepció: el
    historial no ha de poder aturar el poller."""
    global _comptador
    if not _dir:
        return
    ara = datetime.datetime.now()
    event = {"t": ara.strftime("%Y-%m-%d %H:%M:%S"), "tipus": tipus}
    if cicle:
        event["cicle"] = cicle
    if codi:
        event["codi"] = str(codi)
    if detall:
        event["detall"] = str(detall)[:500]
    try:
        os.makedirs(_dir, exist_ok=True)
        with open(os.path.join(_dir, f"events_{ara:%Y-%m}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        _comptador += 1
    except OSError as e:
        print(f"[pccf-poller] AVÍS: no s'ha pogut registrar l'esdeveniment {tipus}: {e}", flush=True)


def comptador():
    return _comptador


def reinicia_comptador():
    global _comptador
    _comptador = 0


def llig(directori_historial, maxim=400):
    """Els `maxim` esdeveniments més recents (dels dos últims fitxers de mes),
    del més nou al més antic."""
    events = []
    for path in sorted(glob.glob(os.path.join(directori_historial, "events_*.jsonl")))[-2:]:
        try:
            with open(path, encoding="utf-8") as f:
                for linia in f:
                    try:
                        events.append(json.loads(linia))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    return list(reversed(events[-maxim:]))
