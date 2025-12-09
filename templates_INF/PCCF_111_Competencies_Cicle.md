## Competències del cicle `{{ ciclo }}`

### Competencias Professionals

| Codi | Competència | Pes (%) |
|--------|-------------|---------:|{% set total_prof = competencias_profesionales|length %}{% if total_prof > 0 %}{% set peso_prof = 100.0 / total_prof %}{% for code in competencias_profesionales %}
| {{ code }} | {{ cpps[code] if code in cpps else '' }} | {{ (peso_prof|round(2))|string|replace('.', ',') }}% |{% endfor %} {% else %} | - | No hi ha competències professionals definides | 0% | {% endif %}

### Competencias per a la ocupabilitat

| Codi | Competència | Pes (%) |
|--------|-------------|---------:|{% set total_soc = competencias_sociales|length %}{% if total_soc > 0 %}{% set peso_soc = 100.0 / total_soc %}{% for code in competencias_sociales %}
| {{ code }} | {{ cpps[code] if code in cpps else '' }} | {{ (peso_soc|round(2))|string|replace('.', ',') }}% |{% endfor %} {% else %} | - | No hi ha competències per a la ocupabilitat definides | 0% | {% endif %}