# Instruccions d'us

## Afegir un nou cicle 

### 1. Crear el nou arxiu `rd-xxxx.json`

Pots fer servir alguna IA ([DeepSeek.com](https://www.deepseek.com/)) passant-li com a context el `json` d'un altre cicle i el `pdf` amb el currículum per a que emplene els valors del `json` però no alterar les claus. Inclús pots demanar que traduisca els valors al Valencià.

### 2. Afegir el nou cicle al `Makefile`

Agafar un fragment d'un altre cicle, fer una còpia i adaptar-lo al nou cicle, en este cas adaptem el Curs d'especialització d'IA I Big Data per a Grau bàsic d'Informàtica i Oficina:

Original (ceiabd):

```makefile
proyecto-ceiabd: files proyecto-base

	@echo " [ ${BLUE} Proyecto Curricular : CE IABD ${RESET}]"

	@echo " ${LIGHTBLUE} Poblando desde CEIABD ${RESET}"
	cp -r src_CEIABD/* temp/

	@echo " ${LIGHTBLUE} Libro de las Programaciones de CEIABD ${RESET}"
	./tools/json2excel.py CEIABD
	@echo " ${LIGHTBLUE} Excel Generado para CEIABD ${RESET}"

	@echo " ${LIGHTBLUE} Proyecto y Programaciones de CEIABD ${RESET}"
	./tools/json2pccf.py CEIABD

	@echo " ${LIGHTBLUE} Generando $(PDF_PATH)/PCCF_$(CENTRO_EDUCATIVO)_CEIABD.pdf ${RESET}"
	@cd temp/ && pandoc --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/PCCF_$(CENTRO_EDUCATIVO)_CEIABD.pdf ./PCCF_*.md
	@echo " ${LIGHTBLUE} PDF Generado para CEIABD ${RESET}"

	@# Me dejo aqui el --verbose por si quiero apuntar algo mas fino en los errores.
	@echo " ${LIGHTBLUE} Generando $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_CEIABD.pdf ${RESET}"
	@cd temp/ && pandoc  --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_CEIABD.pdf ./PD_*.md
	@echo " ${LIGHTBLUE} Programaciones Generadas para CEIABD ${RESET}"
	@echo " ${LIGHTBLUE} Ahora recorro los diferentes modulos ${RESET}"
	./tools/shell-progs-didacticas-standalone.sh CEIABD
	@echo " ${LIGHTBLUE} [ Proyecto CEIABD Completado ] ${RESET}"
```

Adaptació (fpbiio):

```makefile
proyecto-fpbiio: files proyecto-base

	@echo " [ ${BLUE} Proyecto Curricular : FPB IIO ${RESET}]"

	@echo " ${LIGHTBLUE} Poblando desde FPBIIO ${RESET}"
	cp -r src_FPBIIO/* temp/

	@echo " ${LIGHTBLUE} Libro de las Programaciones de FPBIIO ${RESET}"
	./tools/json2excel.py FPBIIO
	@echo " ${LIGHTBLUE} Excel Generado para FPBIIO ${RESET}"

	@echo " ${LIGHTBLUE} Proyecto y Programaciones de FPBIIO ${RESET}"
	./tools/json2pccf.py FPBIIO

	@echo " ${LIGHTBLUE} Generando $(PDF_PATH)/PCCF_$(CENTRO_EDUCATIVO)_FPBIIO.pdf ${RESET}"
	@cd temp/ && pandoc --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/PCCF_$(CENTRO_EDUCATIVO)_FPBIIO.pdf ./PCCF_*.md
	@echo " ${LIGHTBLUE} PDF Generado para FPBIIO ${RESET}"

	@# Me dejo aqui el --verbose por si quiero apuntar algo mas fino en los errores.
	@echo " ${LIGHTBLUE} Generando $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_FPBIIO.pdf ${RESET}"
	@cd temp/ && pandoc  --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_FPBIIO.pdf ./PD_*.md
	@echo " ${LIGHTBLUE} Programaciones Generadas para FPBIIO ${RESET}"
	@echo " ${LIGHTBLUE} Ahora recorro los diferentes modulos ${RESET}"
	./tools/shell-progs-didacticas-standalone.sh FPBIIO
	@echo " ${LIGHTBLUE} [ Proyecto FPBIIO Completado ] ${RESET}"
```

Afegir el nou projecte també a l'apartat `help:`:

```makefile
# Regla para mostrar ayuda
help:
	@echo "Uso: make [CENTRO_EDUCATIVO=nombre_del_centro] <target>"
	@echo ""
	@echo "Targets disponibles:"
	@echo "  proyecto-smx       Generar proyecto para SMX"
	@echo "  proyecto-asir      Generar proyecto para ASIR"
	@echo "  proyecto-daw       Generar proyecto para DAW"
	@echo "  proyecto-dam       Generar proyecto para DAM"
	@echo "  proyecto-ceiabd    Generar proyecto para CEIABD"
	@echo "  proyecto-fpbiio    Generar proyecto para FPBIIO"
	@echo "  clean              Limpiar archivos generados"
	@echo "  files              Crear estructura de directorios"
	@echo "  dependences        Instalar dependencias"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make proyecto-smx	# Usa 'SENIA' por defecto"
	@echo "  make CENTRO_EDUCATIVO=MICENTRO proyecto-asir"
	@echo "  make CENTRO_EDUCATIVO=IESEPM proyecto-dam"

```

### 3. Modificar el script `tools/json2excel.py`:

Este script genera un excel generic a partir de la informació de l'arxiu `rd-fpbiio.json` que hem generat al primer punt.

Hem de clonar les linees referents al CEIABD:

```python
elif sys.argv[1] == "CEIABD":

    with open('./boe/rd-ceiabd.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
```

I generar les noves per a FPBIIO:

```python
elif sys.argv[1] == "FPBIIO":

    with open('./boe/rd-fpbiio.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
```

### 4. Generar la plantilla de les PD's per als mòduls del nou cicle

A la carpeta `templates` hem de clonar l'arxiu `PCCF_PD_Plantilla_MODULO_CEIABD.md` i crear un per al nou cicle `PCCF_PD_Plantilla_MODULO_FPBIIO.md`

### 5. Modificar el script `tools/json2pccf.py`:

Este script genera les PD's per a cadascun del mòduls a partir de la informació de l'arxiu `rd-fpbiio.json` que hem generat al primer punt i de la plantilla `PCCF_PD_Plantilla_MODULO_FPBIIO.md` del punt anterior.

Hem de clonar les liníes referents al CEIABD:

```python
elif sys.argv[1] == "CEIABD":

    with open('./boe/rd-ceiabd.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
```

I generar les noves per a FPBIIO:

```python
elif sys.argv[1] == "FPBIIO":

    with open('./boe/rd-fpbiio.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
```

### 6. Crear estructura de carpeta per al nou cicle `src_FPBIIO`:

Podem clonar la carpeta d'un altre cicle, per exemple `src_CEIABD` i anomenar-la `src_FPBIIO`:

Dins de la carpeta trobarem la següent estructura:

| Ruta i/o fitxer                              | Descripció                                                   |
| -------------------------------------------- | ------------------------------------------------------------ |
| `imgs/FPBIIO_horario.png`                    | Este fitxer hauria de contindre la taula d'hores del cicle per a insertar-lo als documents |
| `PCCF_000_FPBIIO_Introduccion.md`            | Plantilla per a la portada del PCCF de FPBIIO.<br />Especificar nom del cicle, centre, curs, portada, etc. |
| `PCCF_006_MarcoNormativoEspecificoFPBIIO.md` | Marc normatiu específic del PCCF de FPBIIO                   |
| `PCCF_110_AdecuacionYArreglo_FPBIIO.md`      | Ponderació de les competencies profesionals i per a la ocupabilitat del cicle |
| `PCCF_150_OrganizacionDistribucion.md`       | En esta plantilla s'utilitza la imatge de `imgs/FPBIIO_horario.png` |
| `PD_000_FPBIIO_Introduccion.md`              | Plantilla per a la portada de les PD dels mòduls de FPBIIO.<br />Especificar nom del cicle, centre, curs, portada, etc. |

> A més d'estos fitxers, s'hauran d'afegir tots els que siguen específics d'este cicle. Els arxius comuns es troben a la ruta `src/`. La ordenació dels fitxers és per ordre alfabètic, per això és important la numeració que apareix darrere de les inicials `PCCF_` o `PD_`.

### 7. Llançar el projecte per primera vegada per a el nou cicle:

Llançar el make per al projecte del nou cicle:

```sh
./contenedor_lanza.sh "make CENTRO_EDUCATIVO=IESEPM proyecto-fpbiio"
```

### 8. Resultat final

Si el procés funciona correctament (i no es veu cap error pel mig) vorem al final:

```bash
========================================
  SESIÓN FINALIZADA
========================================
```

I tindrem 3 noves carpetes (o si ja existien s'afegiran a elles els nous arxius):

| Ruta                                    | Descripció                                                   |
| --------------------------------------- | ------------------------------------------------------------ |
| `PDFS/PDs_FPBIIO/`                      | Esta carpeta conté un PDF amb la PD de cadascún dels mòduls  |
| `PDFS/FPBIIO_libro_autogenerado.xlsx`   | Excel genèric generat a partir de la informació del rd-fpbiio.json i que posteriorment utilitzarà cada docent per a ajustar les ponderacions de cada RA i designar els CE o RA que van a FEE. |
| `PDFS/PCCF_IESEPM_FPBIIO.pdf`           | PCCF preeliminar del cicle corresponent en PDF               |
| `PDFS/Programaciones_IESEPM_FPBIIO.pdf` | PDF amb totes les PD's de tots els mòduls del cicle          |

### 9. Afegir el nou cicle a l'script `pccf_utils.py`

Al final de l'script, fem una còpia del que fa referència a CEIABD:

```python
# CEIABD
if hoja.startswith("Models d"): hoja = "MIA"
if hoja.startswith("Sistemes d"): hoja = "SAA"
if hoja.startswith("Programació d"): hoja = "PIA"
if hoja.startswith("Sistemes de"): hoja = "SBD"
if hoja.startswith("Big Data"): hoja = "BDA"
```

i ho adaptem a FPBIIO, podem mirar les pestanyes de l'excel que s'ha generat en `PDFS/FPBIIO_libro_autogenerado.xlsx` i canviar-ho per les sigles del mòdul:

```python
# FPBIIO
if hoja.startswith("Montatge i manteniment"): hoja = "MME"
if hoja.startswith("Operacions auxiliars"): hoja = "OA"
if hoja.startswith("Ofimàtica"): hoja = "OAD"
if hoja.startswith("Instal·lació i manteniment"): hoja = "IMXTD"
if hoja.startswith("Ciències aplicades I"): hoja = "CA1"
if hoja.startswith("Ciències aplicades II"): hoja = "CA2"
if hoja.startswith("Comunicació i societat I"): hoja = "CS1"
if hoja.startswith("Comunicació i societat II"): hoja = "CS2"
```

## Procediment per a generar correctament les PD's i PCCF de cada cicle

### 1. Revisar el contingut de l'excel

Copiar l'excel de `PDFS/FPBIIO_libro_autogenerado.xlsx` a `excel/FPBIIO_libro.xlsx` revisar el contingut per cadascun dels mòduls per part dels docents:

1. A la columna `C` s'indicarà el pes de cada RA en percentatge (tots junts hauran de sumar 100%)
2. *La columna `D` no tinc clar per a que s'utilitza*
3. A la columna `F` s'han d'indicar les hores destinades a cada CE (l'excel sumarà el total per a cada RA, o bé indicar directament el total de RA i no especificar res a les hores del CE)
4. A la columna `H` s'indicarà "si", "SI" o "X" si el CE és un requeriment per a la FEE
5. A la columna `I` S'indicarà les hores destinades de cada CE/RA a les FEE (en la fila 5 de la mateixa columna apareixerà el total d'hores enviades a DUAL)
6. A la columna `J` s'indicaran els continguts de cada RA
7. Reanomenar la pestanya que conté el mòdul, per les sigles del mateix tal i com s'ha indicat a l'script `pccf_utils.py`, este pas indicarà que el mòdul està revisat i ja pot formar part de les PD's i el PCCF.

### Generació de PD's:

La generació final de les PD's es basa en el contingut de la carpeta `src_CICLE` corresponent al cicle, tots els fitxers de dita carpeta (excepte els de les PCCF) es junten en una carpeta (temp) que després s'uniran en un únic document PDF per cada PD, i un altre que juntarà totes les PD's.

Si a la carpeta `src_MODUL` trobem el fitxer corresponent a la PD del mòdul s'utilitzarà per a la generació del PDF, sino s'utilitzarà el genèric de la carpeta `temp_CICLE`.

### Generació del PCCF:

La generació final del PCCF es basa en el contingut de les carpetes `src` i `src_CICLE` corresponent al cicle, tots els fitxers de dites carpetes (excepte els de les PD) es junten en una carpeta (temp) que després s'uniran en un únic document PDF.





