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


RECOMMENDATION_RULES = [
    {
        "profile": "Inflamacion / respuesta inmune",
        "keywords": [
            "inflam",
            "fiebre",
            "dolor articular",
            "artralgia",
            "fatiga",
            "pcr",
            "vsg",
            "leucocitos",
            "infeccion",
        ],
        "markers": {
            "genomic": ["TNF"],
            "transcriptomic": ["IL6", "TNF", "CXCL8"],
            "proteomic": ["CRP", "CXCL8"],
            "metabolomic": ["Lactato"],
        },
        "reason": "El contexto contiene terminos asociados con inflamacion o respuesta inmune; estos marcadores permiten explorar senalizacion inflamatoria y fase aguda de forma simulada.",
        "sample": "Suero, plasma o sangre total segun prueba.",
        "technique": "ELISA, inmunoensayo, qPCR o panel molecular segun marcador.",
        "limitations": "La inflamacion no define etiologia por si sola; requiere correlacion clinica y microbiologica.",
        "false_results": "Falsos positivos por inflamacion no infecciosa; falsos negativos en fases tempranas o muestras inadecuadas.",
        "validator": "Bacteriologo/laboratorista clinico y medico tratante.",
    },
    {
        "profile": "Infeccioso",
        "keywords": [
            "infeccion",
            "sepsis",
            "fiebre",
            "cultivo",
            "bacteria",
            "viral",
            "pus",
            "leucocitos",
            "procalcitonina",
            "antibiograma",
        ],
        "markers": {
            "genomic": ["TNF"],
            "transcriptomic": ["IL6", "CXCL8"],
            "proteomic": ["CRP"],
            "metabolomic": ["Lactato"],
        },
        "reason": "El contexto sugiere proceso infeccioso o respuesta sistemica; se priorizan marcadores inflamatorios y metabolicos de apoyo, no confirmatorios.",
        "sample": "Sangre, suero, plasma, orina, hisopado o muestra del foco sospechoso.",
        "technique": "Cultivo, antibiograma, PCR/qPCR, inmunoensayo o panel sindromico segun disponibilidad.",
        "limitations": "Los biomarcadores no reemplazan cultivo, identificacion microbiologica ni antibiograma.",
        "false_results": "Falsos positivos por inflamacion esteril; falsos negativos por antibiotico previo, baja carga microbiana o mala toma de muestra.",
        "validator": "Bacteriologo, microbiologo clinico y medico tratante.",
    },
    {
        "profile": "Proliferacion / ciclo celular",
        "keywords": [
            "tumor",
            "neoplas",
            "cancer",
            "prolifer",
            "masa",
            "biopsia",
            "perdida de peso",
            "ldh",
        ],
        "markers": {
            "genomic": ["TP53", "EGFR", "MYC"],
            "transcriptomic": ["MKI67", "CDK1", "MYC"],
            "proteomic": ["EGFR", "MKI67"],
            "metabolomic": ["Lactato", "Glucosa"],
        },
        "reason": "El contexto sugiere una pregunta academica relacionada con crecimiento celular; estos marcadores ayudan a explorar ciclo celular, senales proliferativas y metabolismo asociado.",
        "sample": "Tejido, sangre o muestra molecular segun sospecha y protocolo.",
        "technique": "Inmunohistoquimica, qPCR, secuenciacion, citometria o panel molecular.",
        "limitations": "No confirma malignidad sin histopatologia, correlacion clinica e interpretacion especializada.",
        "false_results": "Sobreexpresion no especifica, heterogeneidad tumoral o baja calidad de muestra pueden alterar la interpretacion.",
        "validator": "Patologia, genetica molecular, bacteriologo molecular y medico especialista.",
    },
    {
        "profile": "Metabolismo energetico",
        "keywords": [
            "metabol",
            "glucosa",
            "diabetes",
            "lactato",
            "hipoxia",
            "energia",
            "atp",
            "obesidad",
        ],
        "markers": {
            "genomic": ["GLUT1", "LDHA"],
            "transcriptomic": ["HIF1A", "LDHA", "GLUT1"],
            "proteomic": ["LDHA"],
            "metabolomic": ["Glucosa", "Lactato", "ATP", "Piruvato"],
        },
        "reason": "El contexto apunta a metabolismo o demanda energetica; este panel permite discutir glucolisis, transporte de glucosa y estres energetico.",
        "sample": "Suero, plasma o sangre total segun analito.",
        "technique": "Quimica clinica, espectrometria, inmunoensayo o metabolomica.",
        "limitations": "Los metabolitos son sensibles a ayuno, transporte, tiempo de procesamiento y estado clinico.",
        "false_results": "Hemolisis, retraso preanalitico, ejercicio o mala conservacion pueden modificar resultados.",
        "validator": "Bacteriologo/laboratorista clinico, quimico clinico y medico tratante.",
    },
    {
        "profile": "Reparacion de ADN / riesgo genomico",
        "keywords": [
            "genet",
            "heredit",
            "familiar",
            "mutacion",
            "brca",
            "adn",
            "molecular",
        ],
        "markers": {
            "genomic": ["BRCA1", "BRCA2", "TP53"],
            "transcriptomic": ["TP53"],
            "proteomic": [],
            "metabolomic": [],
        },
        "reason": "El contexto contiene elementos de pregunta genomica o antecedente familiar; estos marcadores sirven para ilustrar reparacion de ADN y control de dano genomico.",
        "sample": "Sangre total, saliva o tejido segun estudio molecular.",
        "technique": "Secuenciacion, qPCR, MLPA o panel genetico validado.",
        "limitations": "Requiere consentimiento, consejeria genetica e interpretacion por variantes clasificadas.",
        "false_results": "Variantes de significado incierto, contaminacion o cobertura insuficiente pueden limitar conclusiones.",
        "validator": "Genetista, bioinformatico clinico y bacteriologo molecular.",
    },
    {
        "profile": "Autoinmune",
        "keywords": [
            "autoinmune",
            "ana",
            "lupus",
            "artritis",
            "rash",
            "dolor articular",
            "anticuerpos",
            "inflamacion cronica",
        ],
        "markers": {
            "genomic": ["TNF"],
            "transcriptomic": ["IL6", "TNF"],
            "proteomic": ["CRP"],
            "metabolomic": [],
        },
        "reason": "El contexto sugiere inflamacion persistente o autoinmunidad; se recomienda correlacionar marcadores inflamatorios con autoanticuerpos y clinica.",
        "sample": "Suero o plasma.",
        "technique": "Inmunoensayo, inmunofluorescencia, ELISA o panel autoinmune.",
        "limitations": "Marcadores inflamatorios son inespecificos y no sustituyen criterios clinicos de enfermedad autoinmune.",
        "false_results": "Autoanticuerpos pueden aparecer en poblacion sana; inmunosupresion puede disminuir senales.",
        "validator": "Bacteriologo/laboratorista clinico, inmunologo y medico tratante.",
    },
    {
        "profile": "Seguimiento terapeutico",
        "keywords": [
            "seguimiento",
            "tratamiento",
            "respuesta",
            "terapeutico",
            "control",
            "evolucion",
            "antibiotico",
            "antimicrobiano",
        ],
        "markers": {
            "genomic": [],
            "transcriptomic": ["IL6"],
            "proteomic": ["CRP", "LDHA"],
            "metabolomic": ["Lactato"],
        },
        "reason": "El contexto indica seguimiento; se priorizan marcadores de tendencia para comparar contra resultados previos y respuesta clinica.",
        "sample": "Misma matriz usada en el resultado basal para comparabilidad.",
        "technique": "Metodo equivalente al basal, idealmente en el mismo laboratorio o plataforma validada.",
        "limitations": "No interpretar cambios aislados sin tendencia temporal, clinica y tratamiento recibido.",
        "false_results": "Cambios por preanalitica, variabilidad biologica o diferencia metodologica.",
        "validator": "Bacteriologo/laboratorista clinico y medico tratante.",
    },
]


def parse_items(raw_text: str) -> List[str]:
    """Convierte texto separado por comas o saltos de linea en una lista limpia."""

    if not raw_text:
        return []

    normalized = raw_text.replace("\n", ",").replace(";", ",")
    items = [item.strip() for item in normalized.split(",")]
    return [item for item in items if item]


def unique_items(items: Iterable[str]) -> List[str]:
    """Elimina duplicados conservando el orden original."""

    clean_items = []
    seen = set()
    for item in items:
        normalized = normalize_marker(item)
        if item and normalized not in seen:
            clean_items.append(item)
            seen.add(normalized)
    return clean_items


def recommend_marker_panel(case: Dict[str, object]) -> Dict[str, object]:
    """Recomienda marcadores simulados segun contexto clinico basico.

    Las recomendaciones son academicas: no indican que el marcador deba
    solicitarse en un paciente real ni reemplazan criterio profesional.
    """

    text_parts = [
        str(case.get("presumptive_diagnosis", "")),
        " ".join(case.get("symptoms", [])),
        " ".join(case.get("lab_results", [])),
    ]
    searchable_text = " ".join(text_parts).lower()

    matched_rules = []
    recommended = {
        "genomic": [],
        "transcriptomic": [],
        "proteomic": [],
        "metabolomic": [],
    }

    for rule in RECOMMENDATION_RULES:
        score = sum(1 for keyword in rule["keywords"] if keyword in searchable_text)
        if score > 0:
            matched_rules.append({**rule, "score": score})
            for data_type, markers in rule["markers"].items():
                recommended[data_type].extend(markers)

    if not matched_rules:
        matched_rules.append(
            {
                "profile": "Panel exploratorio general",
                "score": 1,
                "reason": "No se detecto un perfil dominante; se propone un panel balanceado para mostrar integracion multi-omica en el prototipo.",
                "markers": {
                    "genomic": ["TP53", "EGFR"],
                    "transcriptomic": ["IL6", "MKI67"],
                    "proteomic": ["CRP", "LDHA"],
                    "metabolomic": ["Glucosa", "Lactato"],
                },
            }
        )
        for data_type, markers in matched_rules[0]["markers"].items():
            recommended[data_type].extend(markers)

    recommended = {data_type: unique_items(markers) for data_type, markers in recommended.items()}

    rows = []
    labels = {
        "genomic": "Genomica",
        "transcriptomic": "Transcriptomica",
        "proteomic": "Proteomica",
        "metabolomic": "Metabolomica",
    }
    for rule in sorted(matched_rules, key=lambda item: item["score"], reverse=True):
        priority = "Alta" if rule["score"] >= 2 else "Media"
        for data_type, markers in rule["markers"].items():
            for marker in markers:
                item = KNOWLEDGE_BASE.get(normalize_marker(marker))
                rows.append(
                    {
                        "Perfil sugerido": rule["profile"],
                        "Tipo de dato": labels[data_type],
                        "Marcador recomendado": item.name if item else marker,
                        "Prioridad": priority,
                        "Por que se recomienda": rule["reason"],
                        "Tipo de muestra recomendada": rule.get("sample", "Segun prueba y protocolo."),
                        "Tecnica sugerida": rule.get("technique", "Metodo validado por el laboratorio."),
                        "Limitaciones": rule.get("limitations", "Requiere correlacion clinica y validacion profesional."),
                        "Posibles falsos positivos/falsos negativos": rule.get(
                            "false_results", "Dependen de la muestra, metodo y contexto clinico."
                        ),
                        "Profesional que debe validar": rule.get(
                            "validator", "Bacteriologo/laboratorista clinico y medico tratante."
                        ),
                    }
                )

    return {
        "recommended_markers": recommended,
        "recommendation_rows": rows,
        "matched_profiles": [rule["profile"] for rule in matched_rules],
    }


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


def treatment_orientation(category_counts: Dict[str, int]) -> List[str]:
    """Sugiere lineas academicas de discusion terapeutica no prescriptiva."""

    suggestions = []
    if category_counts.get("inflamacion", 0) >= 2:
        suggestions.append(
            "Discutir evaluacion clinica de foco inflamatorio/infeccioso, correlacion con PCR/VSG y pertinencia de estudios inmunologicos o microbiologicos complementarios."
        )
    if category_counts.get("ciclo celular", 0) >= 2:
        suggestions.append(
            "Considerar discusion interdisciplinaria con patologia, oncologia o genetica molecular si el contexto academico simula proliferacion celular; no iniciar decisiones terapeuticas sin confirmacion diagnostica."
        )
    if category_counts.get("metabolismo", 0) >= 2:
        suggestions.append(
            "Explorar control metabolico, estado energetico celular y pruebas complementarias como glucosa, lactato, perfil metabolico o estudios funcionales segun criterio profesional."
        )
    if category_counts.get("reparacion ADN", 0) >= 1:
        suggestions.append(
            "Plantear consejeria genetica o validacion molecular confirmatoria en un escenario real antes de cualquier decision preventiva o terapeutica."
        )
    if category_counts.get("estres celular", 0) >= 1:
        suggestions.append(
            "Correlacionar posible hipoxia o estres celular con hallazgos clinicos, imagenologicos o de laboratorio antes de proponer intervenciones."
        )
    if not suggestions:
        suggestions.append(
            "No se propone una linea terapeutica especifica; se recomienda ampliar datos, validar biomarcadores y revisar el caso con profesionales competentes."
        )
    suggestions.append(
        "Orientacion no prescriptiva: BioNexus AI no selecciona antibioticos, dosis ni conductas clinicas. Para antimicrobianos se requiere foco infeccioso, cultivo/antibiograma cuando aplique, alergias, funcion renal/hepatica, guias institucionales y validacion medica."
    )
    return suggestions


def alert_level(case: Dict[str, object], risk: str) -> str:
    """Asigna alerta operacional para priorizacion del informe."""

    quality = str(case.get("sample_quality", "")).lower()
    status = str(case.get("result_status", "")).lower()
    lab_text = " ".join(case.get("lab_results", [])).lower()

    if "critico" in status or "crítico" in status or "sepsis" in lab_text or "lactato elevado" in lab_text:
        return "Critico: contactar profesional responsable"
    if quality in {"hemolizada", "lipemica", "lipémica", "insuficiente"}:
        return "Alto: requiere revision prioritaria por calidad de muestra"
    if risk == "Alto":
        return "Alto: requiere revision prioritaria"
    if risk == "Moderado":
        return "Moderado: requiere correlacion clinica"
    return "Bajo: seguimiento rutinario"


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
    alert = alert_level(case, risk)

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
            "alert": alert,
        },
        "omics_counts": {data_type: len(markers) for data_type, markers in omics_data.items()},
        "candidates": candidates,
        "altered_pathways": altered_pathways,
        "interpretations": interpretations,
        "diagnostic_hypothesis": [
            f"Hipotesis compatible con {molecular_class.lower()} segun biomarcadores candidatos y datos ingresados.",
            "Debe correlacionarse con historia clinica, examen fisico, criterios diagnosticos y pruebas confirmatorias.",
        ],
        "treatment_orientation": treatment_orientation(category_counts),
        "recommendations": recommendations,
        "limitations": [
            "El analisis es simulado y basado en reglas simples.",
            "No usa secuenciacion real, validacion estadistica ni anotacion clinica certificada.",
            "No constituye diagnostico medico ni reemplaza criterio profesional.",
        ],
    }
