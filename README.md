# BioNexus AI

BioNexus AI es un prototipo academico de Streamlit para integrar datos multi-omicos y clinicos simulados. Su objetivo es apoyar una exposicion universitaria sobre genómica, transcriptomica, proteomica, metabolomica, biomarcadores candidatos y medicina de precision.

Importante: este prototipo no realiza diagnostico medico. Usa reglas simples con fines educativos e investigativos.

## Estructura del proyecto

```text
bionexus_ai/
  app.py
  requirements.txt
  README.md
  data/
    example_case.json
  modules/
    __init__.py
    analyzer.py
    report.py
```

## Como ejecutarlo

1. Abre una terminal dentro de la carpeta `bionexus_ai`.
2. Crea un entorno virtual, si quieres aislar las librerias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
pip install -r requirements.txt
```

4. Ejecuta la aplicacion:

```powershell
streamlit run app.py
```

5. Abre la direccion que muestre Streamlit, normalmente `http://localhost:8501`.

## Datos simulados de ejemplo

Puedes cargar el caso incluido en `data/example_case.json` desde la barra lateral de la aplicacion. Tambien puedes ingresar tus propios datos simulados separados por comas o por saltos de linea.

Ejemplo:

- Genes alterados: `TP53, BRCA1, EGFR`
- Genes sobreexpresados o subexpresados: `IL6, TNF, MKI67, HIF1A`
- Proteinas alteradas: `CRP, CXCL8, LDHA`
- Metabolitos alterados: `Lactato, Glucosa, ATP`
- Laboratorio: `PCR elevada, VSG elevada, LDH elevada`

## Como funciona el analisis

El modulo `modules/analyzer.py` contiene una base de conocimiento simulada que relaciona biomarcadores con categorias biologicas:

- Inflamacion e inmunidad.
- Ciclo celular y proliferacion.
- Metabolismo energetico.
- Reparacion de ADN.
- Estres celular.

La aplicacion cuenta biomarcadores candidatos, identifica rutas posiblemente alteradas, asigna una clasificacion molecular simulada y estima un riesgo academico bajo, moderado o alto. Estos resultados requieren validacion y no deben interpretarse como diagnostico.

## Recomendaciones para fases futuras

- Conectar bases de datos reales como ClinVar, OMIM, KEGG, Reactome, UniProt o Gene Ontology.
- Agregar carga de archivos CSV o Excel para datos omicos.
- Incorporar control de calidad, normalizacion y trazabilidad de muestras.
- Usar modelos de machine learning entrenados con cohortes reales y validacion estadistica.
- Separar perfiles de usuario para estudiantes, investigadores y docentes.
- Agregar comparacion contra cohortes sanas o grupos control.
- Incluir referencias bibliograficas automaticas para cada biomarcador.
- Crear un modo docente con explicaciones paso a paso de cada regla.

