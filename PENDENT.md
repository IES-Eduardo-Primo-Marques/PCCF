# Feina pendent

Notes per a continuar en un altre ordinador. Quan una tasca s'acabe, s'esborra d'ací; quan no en quede cap, s'esborra el fitxer i la línia que l'enllaça des de `CLAUDE.md`.

## 2026-10-19 · Panel de control `programacions/5_panel/panel.html` — FET, SENSE COMMIT

Vore `AGENTS.md` → «Panel de control». Provat en local amb un arbre de prova (DAM, SMX, EI) i `pccf_sync_poller.py --once`; no s'ha provat al contenidor.

1. Commit + push quan l'usuari ho diga, i tornar a desplegar l'stack (canvien `docker-entrypoint.sh`, amb els logs a `temp/logs/`, i `docker-compose.portainer.yml`, amb el bind mount de `panel_config.json`).
2. Comprovar a `docker logs pccf` que arranca bé i que apareix «panel actualitzat»; que `5_panel/panel.html` arriba a OneDrive i s'obri amb doble clic; i que no es torna a pujar a cada passada (només amb canvis o cada 30 min).
0. **Abans de desplegar**, crear al servidor `/docker/pccf/panel_config.json` (copiar `panel_config.example.json` del repo). Si no existix, Docker en crea un directori: el panel funciona igual però sense configuració.
3. Posar a eixe fitxer `data_limit_pd` quan hi haja data límit de les PD, i revisar `objectiu_fe` (SMX/DAM 200/380 el 2026-27 i 200/300 el 2027-28, segons la proposta de FE). No cal redesplegar.

## 2026-10-16 · RA/CE (0020 d'EI/IS/ISSEMI i FPBIIO) i Projecte intermodular dividit — FETS, AMB COMMIT I PUSH

Els canvis ja són a `main` (commit i push del 2026-10-16). Falta posar-los en producció i fer els passos següents.

### Què s'ha canviat

- **Primers auxilis (0020)** a `boe_SCO/rd-{ei,is,issemi}.json`: ara porten els RA i CE del BOE, els mateixos que APD. Els d'abans eren inventats («situació d'emergència amb xiquets i xiquetes…») i no apareixen ni al RD 1394/2007 (EI) ni al RD 1074/2012 (IS, BOE-A-2012-10866). Ho va detectar la professora de Primers auxilis.
- **Projecte intermodular de grau superior dividit en dos mòduls** (Decret 95/2026, DOGV 10391, annex IV, que reescriu l'annex II del Decret 114/2025): DAM `0492p` 35 h + `0492` 100 h; EI `0019p` 35 h + `0019` 100 h; IS i ISSEMI `0345p` 34 h + `0345` 100 h. Abans era un sol mòdul de 2n de 135/134 h. La part de 1r té els mateixos RA/CE, nom acabat en « - 1r curs» i fulla `PI1` (`pccf_utils.PART_1R`, `get_hoja_label()`). Els regex de noms de PD accepten `\d+p`. Vore `AGENTS.md` → RA i CE del Projecte intermodular.
- **FPBIIO** (`boe_INF/rd-fpbiio.json`):
  - Hores: les de `HEAD`, que són les del Decret 95/2026 (annex VI, que modifica l'annex III-A del Decret 117/2025): 3029 266, 3031 332, 3030 266, 3016 266. A l'altre ordinador s'havien tornat per error a les de la versió original del Decret 117/2025 (299/299/200/332); corregit el 2026-10-16.
  - Noms: «Comunicació i Ciències Socials I/II» i «Ciències aplicades I/II». Les fulles es continuen dient CS1/CS2/CA1/CA2 (`HOJA_LABELS`).
  - `"dualitza": false` a IPO1, IPO2 i 3161–3164. Només dualitzen els mòduls professionals.
  - **Àmbits 3161–3164 sense RA.** El cap d'estudis del matí (professor de Ciències Aplicades) va fer notar que la normativa no en té, i té raó. El RD 498/2024 (art. 6.1) va suprimir els antics mòduls, i el seu currículum és l'annex V del RD 217/2022 (RD 498/2024, art. 6.2.c-d; Decret 117/2025, art. 3.3). Ara porten claus `CE1`…`CE8` i criteris `1.1`… La traducció al valencià és pròpia (no n'hi ha versió oficial) i **convé que la revisen els docents dels àmbits**.
  - `pccf/src_INF_FPBIIO/PCCF_006_MarcoNormativoEspecificoFPBIIO.md`: marc normatiu refet. Abans era una còpia del de DAM.
- **Codi**:
  - `tools/pccf_utils.py`: `es_ambit()`, `es_fila_ra()`, `_CE_LLETRA_RE` (accepta `1.1)`), `PART_1R` i `get_hoja_label()` per a la part de 1r.
  - `excel_estils.py`, `json2excel.py` (capçaleres COMPETÈNCIA ESPECÍFICA / % CE / % CRIT.), `json2pccf.py`, `compila_pd_cicle.py` i `compila_pd_dept.py` (regex `\d+p`).
  - `templates/_base_pd.md`: textos `{% if ambit %}`. Les PD que no són àmbits ixen idèntiques byte a byte.
- **Nou** `tools/regenera_llibre.py`, documentat a `AGENTS.md` → Excel workflow. Regenera un `libro_*.xlsx` des del JSON i hi conserva el que han omplit els docents. Amb `--pd` també actualitza les PD: taula de RA, hores, secció de FE i nom del fitxer. Una fulla nova (com `PI1`) ix buida.
- **Proves:** a Docker (altre ordinador) amb llibres i PD «de producció» generats des de `HEAD` i omplits amb dades. A este ordinador, amb venv: DAM conserva les 15 fulles, crea `PI1` buida, la PD del 0492 passa de 135 a 100 h, i `json2pccf.py --generate-only` crea la PD del `0492p` amb 35 h.

### Passos pendents

- **Fet el 2026-10-16:** desplegat a Portainer i `regenera_llibre.py --pd --aplica` a EI, IS, ISSEMI (`--regenera PA`), DAM, APD i SMX. Totes les fulles conservades; `PI1` nova i buida; PD del PI a 100 h, del 0020 amb la taula de RA nova, d'Anglés 68 → 67 (EI, DAM, SMX) i SMX 0222 133 → 134. APD perd 5 fulles buides (Hoja1-5). Còpies a `/home/PCCF/temp/backups_llibres/*_20261016-19*` (es perden en tornar a desplegar). IS i APD es van haver de tornar a regenerar: algú els tenia oberts a Excel Online, OneDrive va apartar la nostra versió com a safeBackup i va baixar la del núvol; regenerar de nou des d'eixa versió (i esborrar el safeBackup) conserva el que hi havia escrit el docent. Verificat: els 6 llibres al núvol, `PA` d'EI/IS/APD amb els 4 RA del BOE. Queda FPBIIO (punt 5).
2. **Avisar ja els docents del Projecte intermodular de 2n de DAM, EI, IS i ISSEMI**: el mòdul és de 100 h, no de 135/134. La fulla `PI` conserva el que havien posat; si les hores sumen 135, l'Excel donarà la incidència «el mòdul té 100 h» i les hauran de redistribuir.
4. Crear la PD de la part de 1r del PI (no sobreescriu cap PD ni llibre existent):

   ```
   make PCCF_ROOT=/home/PCCF/pccf_sync CENTRO_EDUCATIVO=IESEPM generar-plantilles-pccf-DAM generar-plantilles-pccf-EI generar-plantilles-pccf-IS generar-plantilles-pccf-ISSEMI
   ```
   Ha de crear `PD_{CICLE}_{0492p|0019p|0345p}_…-1rcurs_BORRADOR.md`. Cal assignar-li docent com a les altres PD.
5. **FPBIIO: esperar la decisió del departament** sobre com es reparteixen entre I i II les competències específiques i els criteris de cada àmbit. L'annex V no ho separa i ara I i II porten el conjunt sencer. Quan hi haja resposta, cal ajustar 3161/3162 i 3163/3164 al JSON i, en producció:

   ```
   python3 tools/regenera_llibre.py FPBIIO INF --root /home/PCCF/pccf_sync --regenera CA1 CA2 CS1 CS2 --pd
   ```
6. Comunicar-ho:
   - **A la professora de Primers auxilis:** el 0020 d'EI i IS ja té els mateixos RA i CE que APD.
   - **Al cap d'estudis**, la font normativa: RD 498/2024 (art. 6.1 i 6.2.d) i Decret 117/2025 (DOGV núm. 10172, art. 3.3), que remeten a l'annex V del RD 217/2022.
   - **Als docents del PI**, la font de les hores: Decret 95/2026 (DOGV núm. 10391, 25.06.2026), annex IV.
