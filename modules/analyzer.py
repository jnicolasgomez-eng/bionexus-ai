"""Motor academico de reglas para BioNexus AI.

Este modulo no realiza diagnostico clinico. Usa reglas simples y
transparentes para generar interpretaciones simuladas con fines educativos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class KnowledgeItem:
    """Relaciona un biomarcador con una categoria biologica simulada."""

    name: str
    category: str
    pathway: str
    interpretation: str


KNOWLEDGE_BASE: Dict[str, KnowledgeItem] = {
    # Inflamacion e inmunidad
    "IL6": KnowledgeItem("IL6", "inflamacion", "Senalizacion inflamatoria JAK/STAT", "posible activacion inflamatoria"),
    "TNF": KnowledgeItem("TNF", "inflamacion", "Respuesta inflamatoria NF-kB", "posible activacion inflamatoria"),
    "CRP": KnowledgeItem("CRP", "inflamacion", "Respuesta de fase aguda", "posible estado inflamatorio sistemico"),
    "CXCL8": KnowledgeItem("CXCL8", "inflamacion", "Quimiotaxis y respuesta inmune", "posible reclutamiento inmune"),
    # Ciclo celular y proliferacion
    "TP53": KnowledgeItem("TP53", "ciclo celular", "Control de dano en ADN y apoptosis", "posible alteracion de control celular"),
    "MYC": KnowledgeItem("MYC", "ciclo celular", "Proliferacion celular", "posible aumento de senales proliferativas"),
    "MKI67": KnowledgeItem("MKI67", "ciclo celular", "Actividad proliferativa", "posible incremento de proliferacion celular"),
    "CDK1": KnowledgeItem("CDK1", "ciclo celular", "Regulacion del ciclo celular", "posible alteracion de ciclo celular"),
    "EGFR": KnowledgeItem("EGFR", "ciclo celular", "Senalizacion de crecimiento EGFR/MAPK", "posible activacion de senales de crecimiento"),
    # Metabolismo
    "LDHA": KnowledgeItem("LDHA", "metabolismo", "Glucolisis y metabolismo energetico", "posible reprogramacion metabolica"),
    "GLUT1": KnowledgeItem("GLUT1", "metabolismo", "Transporte de glucosa", "posible aumento de demanda energetica"),
    "LACTATO": KnowledgeItem("Lactato", "metabolismo", "Glucolisis anaerobia", "posible alteracion metabolica energetica"),
    "PIRUVATO": KnowledgeItem("Piruvato", "metabolismo", "Metabolismo central del carbono", "posible alteracion metabolica"),
    "GLUCOSA": KnowledgeItem("Glucosa", "metabolismo", "Homeostasis energetica", "posible desbalance energetico"),
    "ATP": KnowledgeItem("ATP", "metabolismo", "Estado energetico celular", "posible estres energetico"),
    # Reparacion y estres celular
    "BRCA1": KnowledgeItem("BRCA1", "reparacion ADN", "Reparacion por recombinacion homologa", "posible alteracion de reparacion de ADN"),
    "BRCA2": KnowledgeItem("BRCA2", "reparacion ADN", "Reparacion por recombinacion homologa", "posible alteracion de reparacion de ADN"),
    "HIF1A": KnowledgeItem("HIF1A", "estres celular", "Respuesta a hipoxia", "posible respuesta adaptativa a hipoxia"),
}


MOLECULAR_CLASSES = {
    "inflamacion": "Perfil inflamatorio/inmunologico simulado",
    "ciclo celular": "Perfil proliferativo simulado",
    "metabolismo": "Perfil metabolico-energetico simulado",
    "reparacion ADN": "Perfil de reparacion genomica simulado",
    "estres celular": "Perfil de estres celular simulado",
}


def parse_items(raw_text: str) -> List[str]:
    """Convierte texto separado por comas o saltos de linea en una lista limpia."""

    if not raw_text:
        return []

    normalized = raw_text.replace("\n", ",").replace(";", ",")
    items = [item.strip() for item in normalized.split(",")]
    return [item for item in items if item]


def normalize_marker(marker: str) -> str:
    """Estandariza nombres para compararlos con la base de conocimiento."""

    return marker.strip().upper().replace(" ", "")


def count_known_categories(markers: Iterable[str]) -> Dict[str, int]:
    """Cuenta cuantos biomarcadores reconocidos caen en cada categoria."""

    counts: Dict[str, int] = {}
    for marker in markers:
        item = KNOWLEDGE_BASE.get(normalize_marker(marker))
        if item:
            counts[item.category] = counts.get(item.category, 0) + 1
    return counts


def build_candidate_table(data: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Crea la tabla de biomarcadores candidatos a partir de los datos ingresados."""

    rows: List[Dict[str, str]] = []
    for data_type, markers in data.items():
        for marker in markers:
            item = KNOWLEDGE_BASE.get(normalize_marker(marker))
            if item:
                rows.append(
                    {
                        "Tipo de dato": data_type,
                        "Biomarcador candidato": item.name,
                        "Categoria": item.category,
                        "Ruta asociada": item.pathway,
                        "Interpretacion": item.interpretation,
                    }
                )
            else:
                rows.append(
                    {
                        "Tipo de dato": data_type,
                        "Biomarcador candidato": marker,
                        "Categoria": "no clasificado",
                        "Ruta asociada": "requiere anotacion externa",
                        "Interpretacion": "posible asociacion no validada en este prototipo",
                    }
                )
    return rows


def confidence_level(candidate_count: int, pathway_count: int) -> str:
    """Asigna confianza academica segun cantidad de evidencia simulada."""

    if candidate_count >= 7 and pathway_count >= 3:
        return "Alto"
    if candidate_count >= 3 and pathway_count >= 2:
        return "Medio"
    return "Bajo"


def risk_level(candidate_count: int, pathway_count: int, lab_alerts: int) -> str:
    """Clasifica riesgo simulado. No representa riesgo clinico real."""

    score = candidate_count + pathway_count * 2 + lab_alerts
    if score >= 10:
        return "Alto"
    if score >= 5:
        return "Moderado"
    return "Bajo"


def analyze_case(case: Dict[str, object]) -> Dict[str, object]:
    """Integra los datos y devuelve un reporte estructurado."""

    omics_data = {
        "Genomico": case.get("genomic", []),
        "Transcriptomico": case.get("transcriptomic", []),
        "Proteomico": case.get("proteomic", []),
        "Metabolomico": case.get("metabolomic", []),
    }

    all_markers = [marker for markers in omics_data.values() for marker in markers]
    candidates = build_candidate_table(omics_data)
    known_candidates = [row for row in candidates if row["Categoria"] != "no clasificado"]
    category_counts = count_known_categories(all_markers)

    altered_pathways = []
    for category, count in sorted(category_counts.items(), key=lambda item: item[1], reverse=True):
        label = MOLECULAR_CLASSES.get(category, "Perfil molecular simulado")
        altered_pathways.append(
            {
                "Categoria": category,
                "Ruta o proceso": label,
                "Evidencia": f"{count} biomarcador(es) candidato(s)",
            }
        )

    interpretations = []
    if category_counts.get("inflamacion", 0) >= 2:
        interpretations.append("posible activacion inflamatoria por convergencia de biomarcadores inmunes")
    if category_counts.get("ciclo celular", 0) >= 2:
        interpretations.append("posible alteracion de ciclo celular o senalizacion proliferativa")
    if category_counts.get("metabolismo", 0) >= 2:
        interpretations.append("posible alteracion metabolica energetica")
    if category_counts.get("reparacion ADN", 0) >= 1:
        interpretations.append("posible asociacion con mecanismos de reparacion de ADN")
    if not interpretations:
        interpretations.append("evidencia limitada; requiere validacion con bases de datos y revision experta")

    lab_alerts = len(case.get("lab_results", []))
    pathway_count = len(altered_pathways)
    known_count = len(known_candidates)
    confidence = confidence_level(known_count, pathway_count)
    risk = risk_level(known_count, pathway_count, lab_alerts)

    dominant_category = max(category_counts, key=category_counts.get) if category_counts else None
    molecular_class = (
        MOLECULAR_CLASSES.get(dominant_category, "Perfil molecular simulado no concluyente")
        if dominant_category
        else "Perfil molecular simulado no concluyente"
    )

    recommendations = [
        "Validar biomarcadores candidatos con literatura cientifica y bases de datos especializadas.",
        "Repetir o complementar el analisis con control de calidad de muestras y metadatos.",
        "Comparar resultados con cohortes o controles apropiados para investigacion.",
        "Consultar a profesionales de salud, bioinformatica o investigacion antes de tomar decisiones.",
    ]

    return {
        "summary": {
            "age": case.get("age"),
            "sex": case.get("sex"),
            "presumptive_diagnosis": case.get("presumptive_diagnosis"),
            "symptoms": case.get("symptoms", []),
            "risk": risk,
            "confidence": confidence,
            "molecular_class": molecular_class,
        },
        "omics_counts": {data_type: len(markers) for data_type, markers in omics_data.items()},
        "candidates": candidates,
        "altered_pathways": altered_pathways,
        "interpretations": interpretations,
        "recommendations": recommendations,
        "limitations": [
            "El analisis es simulado y basado en reglas simples.",
            "No usa secuenciacion real, validacion estadistica ni anotacion clinica certificada.",
            "No constituye diagnostico medico ni reemplaza criterio profesional.",
        ],
    }

