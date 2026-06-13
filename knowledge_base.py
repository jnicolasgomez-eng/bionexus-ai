"""Base de conocimiento curada para BioNexus AI.

Este modulo simula una capa RAG segura: recupera evidencia desde una
base local controlada, no desde internet abierto. En una fase clinica real,
estas entradas deberian sincronizarse con fuentes oficiales y versionadas.
"""

from __future__ import annotations

from typing import Dict, List


CURATED_KNOWLEDGE: List[Dict[str, str]] = [
    {
        "profile": "Inflamatorio",
        "keywords": "inflamacion fiebre pcr vsg il6 tnf crp cxcl8 dolor articular",
        "clinical_use": "Apoya la interpretacion de respuesta inflamatoria sistemica o local cuando se correlaciona con clinica y laboratorio.",
        "markers": "IL6, TNF, CRP, CXCL8",
        "limitations": "No diferencia por si solo inflamacion infecciosa, autoinmune, tumoral o traumatica.",
        "source": "WHO - Ethics and governance of AI for health",
        "source_url": "https://www.who.int/publications/i/item/9789240029200",
    },
    {
        "profile": "Infeccioso",
        "keywords": "infeccion sepsis cultivo antibiograma fiebre leucocitos procalcitonina lactato bacteria",
        "clinical_use": "Prioriza correlacion entre sintomas, muestra, cultivo, antibiograma y marcadores de respuesta inflamatoria.",
        "markers": "CRP, IL6, CXCL8, Lactato, procalcitonina si esta disponible",
        "limitations": "No reemplaza cultivo, identificacion microbiologica, antibiograma ni guias institucionales.",
        "source": "FDA - Clinical Decision Support Software guidance",
        "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
    },
    {
        "profile": "Metabolico",
        "keywords": "metabolico glucosa lactato atp piruvato hipoxia diabetes ldh ldha glut1",
        "clinical_use": "Apoya sospecha de alteracion metabolica o energetica mediante integracion de metabolitos y marcadores moleculares.",
        "markers": "Glucosa, Lactato, ATP, Piruvato, LDHA, GLUT1",
        "limitations": "Altamente dependiente de ayuno, transporte, procesamiento y estado clinico del paciente.",
        "source": "IMDRF - SaMD clinical evaluation",
        "source_url": "https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation",
    },
    {
        "profile": "Tumoral/proliferativo",
        "keywords": "tumor neoplasia cancer proliferacion tp53 egfr myc mki67 cdk1 biopsia masa",
        "clinical_use": "Orienta discusion molecular de proliferacion celular y vias de crecimiento en contexto de muestra validada.",
        "markers": "TP53, EGFR, MYC, MKI67, CDK1",
        "limitations": "No confirma malignidad sin histopatologia, correlacion clinica y validacion molecular.",
        "source": "IMDRF - SaMD clinical evaluation",
        "source_url": "https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation",
    },
    {
        "profile": "Molecular/genetico",
        "keywords": "genetico molecular brca brca1 brca2 tp53 mutacion hereditario familiar adn secuenciacion",
        "clinical_use": "Apoya priorizacion de biomarcadores genomicos y necesidad de validacion molecular o consejeria genetica.",
        "markers": "BRCA1, BRCA2, TP53",
        "limitations": "Requiere consentimiento, control de calidad, interpretacion de variantes y confirmacion por laboratorio validado.",
        "source": "FDA - Clinical Decision Support Software guidance",
        "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
    },
    {
        "profile": "Seguimiento terapeutico",
        "keywords": "seguimiento terapeutico tratamiento respuesta control evolucion antibiotico antimicrobiano tendencia",
        "clinical_use": "Apoya seguimiento de tendencia laboratorial y respuesta, sin seleccionar tratamientos ni dosis.",
        "markers": "CRP, LDHA, Lactato, IL6 segun contexto",
        "limitations": "Debe compararse contra basal, metodo equivalente y evolucion clinica.",
        "source": "WHO - Ethics and governance of AI for health",
        "source_url": "https://www.who.int/publications/i/item/9789240029200",
    },
]


def _case_text(case: Dict[str, object], analysis: Dict[str, object]) -> str:
    parts = [
        str(case.get("presumptive_diagnosis", "")),
        " ".join(case.get("symptoms", [])),
        " ".join(case.get("lab_results", [])),
        " ".join(case.get("genomic", [])),
        " ".join(case.get("transcriptomic", [])),
        " ".join(case.get("proteomic", [])),
        " ".join(case.get("metabolomic", [])),
        " ".join(row.get("Categoria", "") for row in analysis.get("candidates", [])),
    ]
    return " ".join(parts).lower()


def retrieve_curated_evidence(case: Dict[str, object], analysis: Dict[str, object], limit: int = 4) -> List[Dict[str, str]]:
    """Recupera entradas relevantes de la base curada."""

    text = _case_text(case, analysis)
    scored = []
    for entry in CURATED_KNOWLEDGE:
        score = sum(1 for keyword in entry["keywords"].split() if keyword in text)
        if score:
            scored.append({**entry, "score": str(score)})

    if not scored:
        scored = [{**CURATED_KNOWLEDGE[0], "score": "0"}]

    return sorted(scored, key=lambda item: int(item["score"]), reverse=True)[:limit]


def build_ai_interpretive_summary(
    case: Dict[str, object], analysis: Dict[str, object], evidence_rows: List[Dict[str, str]]
) -> List[str]:
    """Construye una sintesis tipo IA, limitada a evidencia curada."""

    summary = analysis["summary"]
    profiles = ", ".join(row["profile"] for row in evidence_rows)
    alert = summary.get("alert", "No informado")

    return [
        f"Perfil documental recuperado: {profiles}.",
        f"Clasificacion molecular simulada: {summary.get('molecular_class')}; nivel de alerta: {alert}.",
        "La interpretacion se basa en coincidencia entre sintomas, resultados de laboratorio, datos omicos y perfiles de conocimiento curados.",
        "La salida debe ser revisada y liberada por bacteriologo/laboratorista clinico responsable antes de uso asistencial.",
    ]

