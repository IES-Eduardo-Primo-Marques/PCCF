#!/usr/bin/make -f

# Version 0.4 - Refactorizada con reglas patrón
# Probando si esto funciona.
# A ver ahora

# Colors
BLUE= \e[1;34m
LIGHTBLUE= \e[94m
LIGHTGREEN= \e[92m
LIGHTYELLOW= \e[93m
RESET= \e[0m

# Variables configurables
CENTRO_EDUCATIVO ?= SENIA

# Templates 
TEMPLATE_TEX_PD="../rsrc/templates/eisvogel.latex"
PANDOC_OPTIONS="-V fontsize=12pt -V mainfont="../rsrc/sorts-mill-goudy/OFLGoudyStM.otf" -V toc-title="Índex" --pdf-engine=xelatex"

# PDFS
PDF_PATH:=$(shell readlink -f PDFS)

# Lista de ciclos disponibles
CICLOS = smx asir daw dam ceiabd fpbiio

# RULES

todo:
	@echo " [ ${BLUE} * Cosas por hacer ${RESET}]"
	@rgrep "TODO" . | grep -v ".git" | grep -v "./temp/"

dependences:
	@echo " [${BLUE} * Dependencias necesarias para PANDOC ${RESET}] "
	sudo apt update ; sudo apt install --yes make pandoc texlive-extra-utils texlive-lang-spanish texlive-latex-extra texlive-fonts-extra libreoffice poppler-utils
	@echo " [${BLUE} * Dependencias necesarias para PYTHON ${RESET}] "
	sudo apt update ; sudo apt install --yes make python3-jinja2 python3-box python3-numpy python-openpyxl-doc python-pandas-doc python3-pandas

clean:
	@echo " [${BLUE} * Step : Clean ${RESET}] "
	@echo "${LIGHTBLUE} -- PDFS ${RESET}"
	rm -f PDFS/*.pdf PDFS/*.odt
	rm -rf temp/

files:
	@echo " [${BLUE} * Creando Espacio ${RESET}] "
	@echo "${LIGHTBLUE} * Carpeta [ PDFS ]${RESET}"
	mkdir -p PDFS
	@echo "${LIGHTBLUE} * Carpeta [ temp/ ]${RESET}"
	mkdir -p temp
	@echo "${LIGHTBLUE} * Limpiando [ temp/ ]${RESET}"
	rm -rf temp/*

proyecto-base: files
	@echo " [${BLUE} * Poblando el Proyecto Base ${RESET}"
	cp -r src/* temp/

# Regla patrón para todos los ciclos
proyecto-%: files proyecto-base
	@$(eval CICLO=$(subst proyecto-,,$@))
	@$(eval CICLO_UPPER=$(shell echo $(CICLO) | tr '[:lower:]' '[:upper:]'))
	
	@echo " [ ${BLUE} Proyecto Curricular : $(CICLO_UPPER) ${RESET}]"
	@echo " ${LIGHTBLUE} Poblando desde $(CICLO_UPPER) ${RESET}"
	
	# Copiar archivos específicos del ciclo
	cp -r src_$(CICLO_UPPER)/* temp/
	
	@echo " ${LIGHTBLUE} Libro de las Programaciones de $(CICLO_UPPER) ${RESET}"
	./tools/json2excel.py $(CICLO_UPPER)
	@echo " ${LIGHTBLUE} Excel Generado para $(CICLO_UPPER) ${RESET}"
	
	@echo " ${LIGHTBLUE} Fuentes de las Programaciones de $(CICLO_UPPER) ${RESET}"
	./tools/json2pccf.py $(CICLO_UPPER)
	
	@echo " ${LIGHTBLUE} Proyecto de $(CICLO_UPPER) ${RESET}"
	@cd temp/ && pandoc --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/PCCF_$(CENTRO_EDUCATIVO)_$(CICLO_UPPER).pdf ./PCCF_*.md
	@echo " ${LIGHTBLUE} PDF Generado para $(CICLO_UPPER) ${RESET}"
	
	@echo " ${LIGHTBLUE} Generando $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_$(CICLO_UPPER).pdf ${RESET}"
	@cd temp/ && pandoc --template $(TEMPLATE_TEX_PD) $(PANDOC_OPTIONS) -o $(PDF_PATH)/Programaciones_$(CENTRO_EDUCATIVO)_$(CICLO_UPPER).pdf ./PD_*.md
	@echo " ${LIGHTBLUE} Programaciones Generadas para $(CICLO_UPPER) ${RESET}"
	
	@echo " ${LIGHTBLUE} Ahora recorro los diferentes módulos ${RESET}"
	./tools/shell-progs-didacticas-standalone.sh $(CICLO_UPPER)
	
	@echo " ${LIGHTBLUE} [ Proyecto $(CICLO_UPPER) Completado ] ${RESET}"

# Target para generar todos los ciclos
todos: $(addprefix proyecto-,$(CICLOS))
	@echo " ${LIGHTGREEN} [ Todos los proyectos generados ] ${RESET}"

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
	@echo "  todos              Generar todos los proyectos"
	@echo "  clean              Limpiar archivos generados"
	@echo "  files              Crear estructura de directorios"
	@echo "  dependences        Instalar dependencias"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make proyecto-smx                 # Usa 'SENIA' por defecto"
	@echo "  make proyecto-asir                # Genera solo ASIR"
	@echo "  make todos                        # Genera todos los ciclos"
	@echo "  make CENTRO_EDUCATIVO=MIESCUELA proyecto-dam"
	@echo "  make CENTRO_EDUCATIVO=IESEPM todos"