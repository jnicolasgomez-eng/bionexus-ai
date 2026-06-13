# BioNexus AI Clinical Support - Ruta IA/RAG

## Objetivo

Convertir BioNexus AI en una herramienta de apoyo interpretativo de laboratorio con IA supervisada, evidencia trazable y liberacion por bacteriologo/laboratorista clinico.

## Enfoque seguro

No se recomienda que la app consulte internet abierto para generar conductas clinicas. La arquitectura recomendada es RAG con fuentes curadas:

1. Repositorio local de conocimiento validado.
2. Actualizacion programada desde fuentes oficiales.
3. Versionado de fuentes y fecha de actualizacion.
4. Recuperacion de evidencia relevante.
5. Respuesta generada con citas y limitaciones.
6. Revision y liberacion por profesional responsable.

## Fuentes candidatas

- Guias institucionales.
- CLSI/EUCAST para microbiologia y antibiogramas.
- LOINC para pruebas de laboratorio.
- SNOMED CT para hallazgos.
- CIE-10/ICD-10 para diagnosticos.
- HL7/FHIR para interoperabilidad.
- PubMed y guias clinicas oficiales curadas.
- ClinVar, OMIM, UniProt, KEGG y Reactome para biomarcadores.

## Regla de seguridad para antimicrobianos

La app no debe formular antibiotico, dosis ni duracion de tratamiento automaticamente. Puede apoyar con:

- Interpretacion de cultivo y antibiograma.
- Identificacion de resistencia.
- Recomendacion de revisar guia institucional.
- Alertas por resultado critico.
- Validacion obligatoria por bacteriologo/microbiologo y medico tratante.

