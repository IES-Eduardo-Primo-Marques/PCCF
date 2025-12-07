\newpage
# Competèncias del Cicle `{{ ciclo }}`

## Competencias Professionals

| Código | Competencia | Peso (%) |
|--------|-------------|---------:|{% set total_prof = competencias_profesionales|length %}{% if total_prof > 0 %}{% set peso_prof = 100.0 / total_prof %}{% for code in competencias_profesionales %}
| {{ code }} | {{ cpps[code] if code in cpps else '' }} | {{ (peso_prof|round(2))|string|replace('.', ',') }}% |{% endfor %} {% else %} | - | No hay competencias profesionales definidas | 0% | {% endif %}
|<img width=100/>|<img width=500/>|<img width=100/>|

## Competencias per a la ocupabilitat

| Código | Competencia | Peso (%) |
|--------|-------------|---------:|{% set total_soc = competencias_sociales|length %}{% if total_soc > 0 %}{% set peso_soc = 100.0 / total_soc %}{% for code in competencias_sociales %}
| {{ code }} | {{ cpps[code] if code in cpps else '' }} | {{ (peso_soc|round(2))|string|replace('.', ',') }}% |{% endfor %} {% else %} | - | No hay competencias sociales definidas | 0% | {% endif %}
|<img width=100/>|<img width=500/>|<img width=100/>|