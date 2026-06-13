from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.analyzer import analyze_case, parse_items, recommend_marker_panel
from modules.report import build_pdf


APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "bionexus_logo.png"
LOGO_FALLBACK_PATHS = [
    ASSETS_DIR / "bionexus_logo.png",
    ASSETS_DIR / "bionexus_logo_small.png",
    APP_DIR / "bionexus_logo.png",
    APP_DIR / "bionexus_logo_small.png",
]
DB_PATH = APP_DIR / "bionexus_patients.db"
LAB_NAME = "BioNexus AI"
REPORT_TZ = ZoneInfo("America/Bogota")
APP_VERSION = "BioNexus AI Lab Support v0.4"


CURATED_KNOWLEDGE = [
    {
        "profile": "Inflamatorio",
        "keywords": "inflamacion fiebre pcr vsg il6 tnf crp cxcl8 dolor articular",
        "clinical_use": "Apoya la interpretacion de respuesta inflamatoria sistemica o local.",
        "markers": "IL6, TNF, CRP, CXCL8",
        "limitations": "No diferencia etiologia infecciosa, autoinmune, tumoral o traumatica por si solo.",
        "source": "WHO - Ethics and governance of AI for health",
        "source_url": "https://www.who.int/publications/i/item/9789240029200",
    },
    {
        "profile": "Infeccioso",
        "keywords": "infeccion sepsis cultivo antibiograma fiebre leucocitos procalcitonina lactato bacteria",
        "clinical_use": "Prioriza correlacion entre sintomas, muestra, cultivo, antibiograma y marcadores inflamatorios.",
        "markers": "CRP, IL6, CXCL8, Lactato, procalcitonina si esta disponible",
        "limitations": "No reemplaza cultivo, identificacion microbiologica, antibiograma ni guias institucionales.",
        "source": "FDA - Clinical Decision Support Software guidance",
        "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
    },
    {
        "profile": "Metabolico",
        "keywords": "metabolico glucosa lactato atp piruvato hipoxia diabetes ldh ldha glut1",
        "clinical_use": "Apoya sospecha de alteracion metabolica o energetica.",
        "markers": "Glucosa, Lactato, ATP, Piruvato, LDHA, GLUT1",
        "limitations": "Depende de ayuno, transporte, procesamiento y estado clinico.",
        "source": "IMDRF - SaMD clinical evaluation",
        "source_url": "https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation",
    },
    {
        "profile": "Tumoral/proliferativo",
        "keywords": "tumor neoplasia cancer proliferacion tp53 egfr myc mki67 cdk1 biopsia masa",
        "clinical_use": "Orienta discusion molecular de proliferacion celular y vias de crecimiento.",
        "markers": "TP53, EGFR, MYC, MKI67, CDK1",
        "limitations": "No confirma malignidad sin histopatologia, correlacion clinica y validacion molecular.",
        "source": "IMDRF - SaMD clinical evaluation",
        "source_url": "https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation",
    },
    {
        "profile": "Molecular/genetico",
        "keywords": "genetico molecular brca brca1 brca2 tp53 mutacion hereditario familiar adn secuenciacion",
        "clinical_use": "Apoya priorizacion de biomarcadores genomicos y validacion molecular.",
        "markers": "BRCA1, BRCA2, TP53",
        "limitations": "Requiere consentimiento, control de calidad, interpretacion de variantes y confirmacion.",
        "source": "FDA - Clinical Decision Support Software guidance",
        "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software",
    },
]


st.set_page_config(page_title="BioNexus AI", page_icon="BN", layout="wide")


def now_report_datetime() -> str:
    return datetime.now(REPORT_TZ).strftime("%Y-%m-%d %H:%M:%S")


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def save_patient_record(patient_id: str, payload: dict) -> None:
    timestamp = now_report_datetime()
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute("SELECT created_at FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT OR REPLACE INTO patients (patient_id, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (patient_id, json.dumps(payload, ensure_ascii=False), created_at, timestamp),
        )


def load_patient_record(patient_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT payload FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    return json.loads(row[0]) if row else None


def list_patient_records() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT patient_id, payload, created_at, updated_at FROM patients ORDER BY updated_at DESC").fetchall()
    data = []
    for patient_id, payload, created_at, updated_at in rows:
        item = json.loads(payload)
        data.append(
            {
                "ID": patient_id,
                "Paciente": item.get("patient_name", "No informado"),
                "Estado": item.get("workflow_status", "Ingreso inicial"),
                "Creado": created_at,
                "Actualizado": updated_at,
            }
        )
    return pd.DataFrame(data)


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bn-navy: #061622;
            --bn-teal: #12c7bd;
            --bn-blue: #0284c7;
            --bn-green: #0f766e;
            --bn-soft: #e8fbff;
            --bn-line: #b7e4ea;
            --bn-ink: #0f172a;
        }
        .stApp {
            background:
                linear-gradient(180deg, #eefcff 0%, #f8fafc 46%, #ecfeff 100%);
            color: var(--bn-ink);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }
        .bn-hero {
            background: linear-gradient(135deg, #04111f 0%, #0f766e 52%, #0891b2 100%);
            color: white;
            border-radius: 18px;
            padding: 1.4rem 1.5rem;
            display: flex;
            gap: 1.1rem;
            align-items: center;
            box-shadow: 0 18px 45px rgba(15, 23, 42, .18);
            margin-bottom: 1rem;
        }
        .bn-hero img {
            width: 96px;
            height: 96px;
            object-fit: cover;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,.25);
        }
        .bn-hero h1 {
            margin: 0;
            font-size: 2.25rem;
            letter-spacing: 0;
            color: #ffffff;
        }
        .bn-hero p {
            margin: .25rem 0 0 0;
            color: #ddfeff;
        }
        .hero-subtitle {
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 850;
            margin: .25rem 0 .35rem 0;
        }
        .hero-muted {
            color: #cffafe;
            line-height: 1.45rem;
        }
        .hero-version {
            color: #a7f3d0;
            font-weight: 750;
            margin-top: .25rem;
        }
        .omic-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin: .8rem 0 1.5rem 0;
        }
        .omic-card {
            background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
            border: 1px solid #99f6e4;
            border-top: 5px solid #0891b2;
            border-radius: 16px;
            padding: 1rem;
            min-height: 155px;
            box-shadow: 0 12px 26px rgba(15, 23, 42, .08);
        }
        .omic-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0f766e;
            color: white;
            font-weight: 900;
            margin-bottom: .65rem;
        }
        .omic-card strong {
            color: #0f172a;
            display: block;
            font-size: 1.03rem;
            margin-bottom: .4rem;
        }
        .omic-card span {
            color: #334155;
            line-height: 1.4rem;
            font-size: .95rem;
        }
        .chat-card {
            background: rgba(255,255,255,.94);
            border: 1px solid var(--bn-line);
            border-radius: 14px;
            padding: 1rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, .08);
            margin: .6rem 0 1rem 0;
        }
        .ai-bubble {
            background: #ecfeff;
            border: 1px solid #67e8f9;
            border-left: 6px solid #0891b2;
            padding: 1rem;
            border-radius: 14px;
            margin: .75rem 0;
        }
        .user-bubble {
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-left: 6px solid #0f766e;
            padding: 1rem;
            border-radius: 14px;
            margin: .75rem 0;
        }
        .section-title {
            color: #155e75;
            font-weight: 900;
            font-size: 1.22rem;
            margin: 1.1rem 0 .45rem 0;
        }
        .small-title {
            color: #0f766e;
            font-weight: 850;
            margin: .45rem 0 .25rem 0;
        }
        .warning-box {
            background: #fffbeb;
            border: 1px solid #f59e0b;
            border-left: 7px solid #b45309;
            border-radius: 12px;
            color: #451a03;
            padding: .85rem 1rem;
            margin: .75rem 0;
            font-weight: 800;
        }
        .warning-box strong,
        .warning-box span,
        .warning-box p {
            color: #451a03;
        }
        @media (max-width: 900px) {
            .omic-grid {
                grid-template-columns: 1fr;
            }
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--bn-line);
            border-radius: 10px;
            overflow: hidden;
        }
        div[data-testid="stChatMessage"] {
            background: #ffffff;
            border: 1px solid #a7f3d0;
            border-radius: 16px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, .08);
            margin: .8rem 0;
        }
        div[data-testid="stChatMessage"] *,
        div[data-testid="stChatMessageContent"] *,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li {
            color: #0f172a;
        }
        div[data-testid="stChatMessage"] strong {
            color: #0f766e;
        }
        div[data-testid="stTabs"] button {
            font-weight: 850;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    logo_html = '<div class="omic-icon">BN</div>'
    logo_file = next((path for path in LOGO_FALLBACK_PATHS if path.exists()), None)
    if logo_file:
        import base64

        encoded = base64.b64encode(logo_file.read_bytes()).decode("utf-8")
        logo_html = f'<img src="data:image/png;base64,{encoded}" alt="BioNexus IA logo">'

    st.markdown(
        f"""
        <div class="bn-hero">
            {logo_html}
            <div>
                <h1>BioNexus IA</h1>
                <div class="hero-subtitle">Ayuda en diagnostico, tratamiento y seguimiento de pacientes</div>
                <div class="hero-muted">
                    Plataforma de apoyo interpretativo para laboratorio clinico con IA, seguimiento por ID
                    y analisis multi-omico supervisado por bacteriologo/laboratorista clinico.
                </div>
                <div class="hero-muted">
                    Integra datos clinicos, preanaliticos, laboratorio, genomica, transcriptomica,
                    proteomica, metabolomica, biomarcadores moleculares y evidencia curada.
                </div>
                <div class="hero-version">{APP_VERSION}</div>
            </div>
        </div>
        <div class="warning-box">
            Herramienta de apoyo interpretativo. La liberacion diagnostica debe realizarla el bacteriologo/laboratorista clinico responsable y correlacionarse con el medico tratante.
        </div>
        """,
        unsafe_allow_html=True,
    )


def retrieve_curated_evidence(case: dict, analysis: dict, limit: int = 4) -> list[dict]:
    text_parts = [
        str(case.get("presumptive_diagnosis", "")),
        " ".join(case.get("symptoms", [])),
        " ".join(case.get("lab_results", [])),
        " ".join(case.get("genomic", [])),
        " ".join(case.get("transcriptomic", [])),
        " ".join(case.get("proteomic", [])),
        " ".join(case.get("metabolomic", [])),
        " ".join(row.get("Categoria", "") for row in analysis.get("candidates", [])),
    ]
    text = " ".join(text_parts).lower()
    scored = []
    for entry in CURATED_KNOWLEDGE:
        score = sum(1 for keyword in entry["keywords"].split() if keyword in text)
        if score:
            scored.append({**entry, "score": str(score)})
    if not scored:
        scored = [{**CURATED_KNOWLEDGE[0], "score": "0"}]
    return sorted(scored, key=lambda item: int(item["score"]), reverse=True)[:limit]


def clinical_flags(case: dict) -> list[dict]:
    """Detecta senales clinicas simples para hacer la respuesta menos generica."""
    text = " ".join(
        [
            str(case.get("presumptive_diagnosis", "")),
            " ".join(case.get("symptoms", [])),
            " ".join(case.get("lab_results", [])),
        ]
    ).lower()
    flags = []

    def has_any(words: list[str]) -> bool:
        return any(word in text for word in words)

    if has_any(["perdida de conciencia", "pérdida de conciencia", "desmayo", "convulsion", "convulsión", "confusion", "confusión", "agitacion", "agitación"]):
        flags.append(
            {
                "area": "Neurologica/urgencia",
                "priority": "Alta",
                "reason": "hay sintomas que pueden requerir revision prioritaria y correlacion clinica inmediata.",
            }
        )
    if has_any(["respiratorio", "respiratoria", "tos", "disnea", "dificultad respiratoria", "saturacion", "saturación"]):
        flags.append(
            {
                "area": "Respiratoria/infecciosa",
                "priority": "Moderada a alta",
                "reason": "los sintomas respiratorios justifican pruebas inflamatorias, infecciosas y de oxigenacion segun contexto.",
            }
        )
    if has_any(["fiebre", "escalofrio", "escalofrío", "sudoracion", "sudoración", "nocturna"]):
        flags.append(
            {
                "area": "Inflamatoria/infecciosa",
                "priority": "Moderada",
                "reason": "la fiebre o sudoracion orienta a documentar inflamacion y buscar foco infeccioso.",
            }
        )
    if has_any(["palido", "pálido", "palidez", "cansancio", "fatiga"]):
        flags.append(
            {
                "area": "Hematologica/metabolica",
                "priority": "Moderada",
                "reason": "fatiga o palidez hacen pertinente evaluar hemograma, hierro y metabolismo basico.",
            }
        )
    if has_any(["prurito", "picazon", "picazón", "alergia", "roncha"]):
        flags.append(
            {
                "area": "Alergica/inmunologica",
                "priority": "Baja a moderada",
                "reason": "el prurito puede requerir correlacion con eosinofilos, IgE, perfil hepatico o causas dermatologicas.",
            }
        )
    if has_any(["glucosa", "lactato", "diabetes", "hipoglucemia", "hiperglucemia", "metabolico", "metabólico"]):
        flags.append(
            {
                "area": "Metabolica",
                "priority": "Segun resultado",
                "reason": "los datos metabolicos deben interpretarse con unidades, rangos y tendencia.",
            }
        )
    return flags


def extra_clinical_flags(case: dict) -> list[dict]:
    """Complementa reglas para sintomas frecuentes escritos en lenguaje natural."""
    text = " ".join(
        [
            str(case.get("presumptive_diagnosis", "")),
            " ".join(case.get("symptoms", [])),
            " ".join(case.get("lab_results", [])),
        ]
    ).lower()
    flags = []

    def has_any(words: list[str]) -> bool:
        return any(word in text for word in words)

    if has_any(["mareo", "mareos", "vision borrosa", "cefalea", "cefaleas", "dolor de cabeza"]):
        flags.append(
            {
                "area": "Neurologica/metabolica",
                "priority": "Moderada",
                "reason": "mareo, cefalea o vision borrosa requieren correlacion con glucosa, hemograma y electrolitos.",
            }
        )
    if has_any(["mialgia", "mialgias", "dolor muscular", "dolores musculares"]):
        flags.append(
            {
                "area": "Inflamatoria/muscular",
                "priority": "Baja a moderada",
                "reason": "las mialgias pueden acompanar infeccion, inflamacion o alteracion muscular y deben correlacionarse con laboratorio.",
            }
        )
    return flags


def build_ai_summary(case: dict, analysis: dict, evidence_rows: list[dict]) -> list[str]:
    profiles = ", ".join(row["profile"] for row in evidence_rows)
    summary = analysis["summary"]
    patient_name = case.get("patient_name") or "el paciente"
    symptoms = ", ".join(case.get("symptoms", [])) or "no se registraron sintomas especificos"
    flags = clinical_flags(case) + extra_clinical_flags(case)
    lines = [
        f"Recibi el caso de {patient_name} con ID {case.get('patient_id', 'no informado')}. Sintomas registrados: {symptoms}.",
        f"Con los datos actuales, los perfiles mas relacionados son: {profiles}.",
        f"Nivel operativo inicial: {summary.get('alert', 'No informado')}.",
    ]
    if flags:
        for flag in flags[:4]:
            lines.append(f"Senal {flag['area']}: prioridad {flag['priority']}; {flag['reason']}")
    else:
        lines.append("No detecto una senal clinica dominante; sugiero iniciar con pruebas basicas y ajustar segun resultados.")
    lines.extend(
        [
            "Primero recomiendo examenes de laboratorio dirigidos. Despues, con resultados y calidad de muestra, puedo apoyar la interpretacion profesional.",
            "El bacteriologo responsable debe validar preanalitica, metodo, rangos, unidades y consistencia clinica antes de liberar.",
        ]
    )
    return lines


def recommended_lab_tests(case: dict, marker_recommendations: dict, evidence_rows: list[dict]) -> pd.DataFrame:
    profiles = {row["profile"] for row in evidence_rows}
    lab_text = " ".join(case.get("symptoms", []) + case.get("lab_results", [])).lower()
    rows = []
    seen_tests = set()

    def add(test: str, sample: str, method: str, reason: str, validator: str = "Bacteriologo/laboratorista clinico"):
        if test in seen_tests:
            return
        seen_tests.add(test)
        rows.append(
            {
                "Examen sugerido": test,
                "Tipo de muestra": sample,
                "Metodo sugerido": method,
                "Justificacion": reason,
                "Validacion": validator,
            }
        )

    if "Inflamatorio" in profiles or "fiebre" in lab_text or "dolor" in lab_text:
        add("PCR cuantitativa", "Suero o plasma", "Inmunoensayo/ELISA", "Evalua magnitud de respuesta inflamatoria.")
        add("VSG", "Sangre total", "Metodo hematologico", "Apoya seguimiento de inflamacion persistente.")
        add("Hemograma con diferencial", "Sangre total", "Hematologia automatizada", "Permite correlacionar leucocitosis, neutrofilia o linfocitosis.")
    if "Infeccioso" in profiles or "infeccion" in lab_text or "sepsis" in lab_text:
        add("Cultivo segun foco", "Muestra del foco sospechoso", "Cultivo microbiologico", "Busca agente etiologico y permite antibiograma.")
        add("Antibiograma si hay aislamiento", "Aislado bacteriano", "CLSI/EUCAST institucional", "Orienta sensibilidad/resistencia; no reemplaza prescripcion medica.")
        add("Procalcitonina", "Suero o plasma", "Inmunoensayo", "Puede apoyar sospecha bacteriana sistemica segun contexto.")
    if "Metabolico" in profiles or "lactato" in lab_text or "glucosa" in lab_text:
        add("Glucosa", "Suero o plasma", "Quimica clinica", "Apoya evaluacion metabolica inicial.")
        add("Lactato", "Sangre total/plasma", "Quimica clinica o gasometria", "Puede alertar hipoperfusion o alteracion metabolica.")
    if "Tumoral/proliferativo" in profiles:
        add("LDH", "Suero", "Quimica clinica", "Marcador inespecifico de dano tisular o alta actividad celular.")
        add("Panel molecular dirigido", "Tejido/sangre segun indicacion", "qPCR/secuenciacion", "Explora biomarcadores de proliferacion con validacion especializada.")
    if "Molecular/genetico" in profiles:
        add("Panel genetico validado", "Sangre/saliva/tejido", "Secuenciacion/qPCR", "Prioriza genes candidatos y requiere consentimiento/validacion.")

    for flag in clinical_flags(case) + extra_clinical_flags(case):
        if flag["area"] == "Neurologica/urgencia":
            add("Glucosa inmediata", "Sangre capilar/suero", "Quimica clinica o glucometria validada", "Ayuda a descartar alteracion glucemica en sintomas neurologicos.")
            add("Electrolitos", "Suero o plasma", "Quimica clinica", "Sodio, potasio y cloro pueden explicar compromiso neurologico o debilidad.")
            add("Gasometria y lactato", "Sangre arterial o venosa", "Gasometria", "Apoya evaluacion de oxigenacion, perfusion y estado acido-base.")
        if flag["area"] == "Neurologica/metabolica":
            add("Glucosa", "Suero o plasma", "Quimica clinica", "Correlaciona mareo, vision borrosa o cefalea con alteraciones glucemicas.")
            add("Electrolitos", "Suero o plasma", "Quimica clinica", "Apoya correlacion de sintomas neurologicos inespecificos con balance hidroelectrolitico.")
            add("Hemograma con diferencial", "Sangre total", "Hematologia automatizada", "Evalua anemia, infeccion o inflamacion asociada a fatiga, mareo o cefalea.")
        if flag["area"] == "Respiratoria/infecciosa":
            add("Saturacion de oxigeno y gases si aplica", "Dato clinico/sangre", "Oximetria/gasometria", "Correlaciona sintomas respiratorios con oxigenacion.")
            add("Panel respiratorio molecular segun disponibilidad", "Hisopado nasofaringeo", "PCR/qPCR", "Busca agentes respiratorios cuando el contexto lo justifique.")
        if flag["area"] == "Inflamatoria/muscular":
            add("CK total", "Suero", "Quimica clinica", "Apoya evaluacion de compromiso muscular cuando predominan mialgias.")
            add("Perfil renal", "Suero/plasma", "Quimica clinica", "Permite vigilar funcion renal si hay mialgias intensas, deshidratacion o sospecha sistemica.")
        if flag["area"] == "Hematologica/metabolica":
            add("Ferritina y perfil de hierro", "Suero", "Quimica clinica/inmunoensayo", "Apoya evaluacion de fatiga, palidez o posible anemia/inflamacion.")
            add("Perfil metabolico basico", "Suero o plasma", "Quimica clinica", "Evalua glucosa, funcion renal y electrolitos para correlacion inicial.")
        if flag["area"] == "Alergica/inmunologica":
            add("Eosinofilos absolutos", "Sangre total", "Hemograma con diferencial", "Apoya correlacion con alergia, parasitosis o respuesta inmunologica.")
            add("IgE total si aplica", "Suero", "Inmunoensayo", "Puede orientar componente alergico; requiere interpretacion clinica.")
            add("Perfil hepatico", "Suero", "Quimica clinica", "Ayuda a correlacionar prurito con causas hepatobiliares si el contexto lo sugiere.")

    if not rows:
        add("Hemograma, PCR y panel metabolico basico", "Sangre/suero", "Metodos validados", "Panel inicial para orientar interpretacion laboratorial.")

    return pd.DataFrame(rows)


def fallback_treatment_orientation(analysis: dict) -> list[str]:
    categories = {row.get("Categoria", "").lower() for row in analysis.get("candidates", [])}
    suggestions = []
    if "inflamacion" in categories:
        suggestions.append("Correlacionar con PCR, VSG, hemograma, cultivos o pruebas inmunologicas segun sospecha.")
    if "metabolismo" in categories:
        suggestions.append("Revisar glucosa, lactato, estado metabolico y tendencia de resultados.")
    if "ciclo celular" in categories:
        suggestions.append("Considerar validacion por patologia/genetica molecular si hay sospecha proliferativa.")
    suggestions.append("No seleccionar antibiotico, dosis ni duracion sin cultivo/antibiograma, guias institucionales y medico tratante.")
    return suggestions


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="chat-card">
            <div class="small-title">{label}</div>
            <strong>{value}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_bar_figure(analysis: dict) -> go.Figure:
    counts_df = pd.DataFrame(
        {
            "Tipo de dato": list(analysis["omics_counts"].keys()),
            "Alteraciones": list(analysis["omics_counts"].values()),
        }
    )
    fig = go.Figure(
        data=[
            go.Bar(
                x=counts_df["Tipo de dato"],
                y=counts_df["Alteraciones"],
                marker_color=["#0f766e", "#0891b2", "#12c7bd", "#22c55e"],
            )
        ]
    )
    fig.update_layout(
        title="Alteraciones por tipo de dato",
        height=340,
        margin=dict(l=20, r=20, t=55, b=20),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
    )
    return fig


def base_case_from_intake(intake: dict) -> dict:
    return {
        "patient_name": intake["patient_name"],
        "patient_gender": intake["patient_gender"],
        "patient_id": intake["patient_id"],
        "report_datetime": intake["report_datetime"],
        "lab_name": LAB_NAME,
        "bacteriologist_name": intake.get("bacteriologist_name", ""),
        "age": intake["age"],
        "sex": intake["patient_gender"] if intake["patient_gender"] in ["Femenino", "Masculino"] else "No informado",
        "presumptive_diagnosis": intake.get("presumptive_diagnosis", ""),
        "symptoms": parse_items(intake.get("symptoms", "")),
        "lab_results": parse_items(intake.get("lab_results", "")),
        "sample_type": intake.get("sample_type", "Sangre"),
        "collection_date": intake.get("collection_date", ""),
        "reception_date": intake.get("reception_date", ""),
        "sample_quality": intake.get("sample_quality", "Adecuada"),
        "method_used": intake.get("method_used", "Inmunoensayo"),
        "reference_values": intake.get("reference_values", ""),
        "units": intake.get("units", ""),
        "result_status": intake.get("result_status", "Normal"),
        "preanalytical_observations": intake.get("preanalytical_observations", ""),
        "genomic": parse_items(intake.get("genomic", "")),
        "transcriptomic": parse_items(intake.get("transcriptomic", "")),
        "proteomic": parse_items(intake.get("proteomic", "")),
        "metabolomic": parse_items(intake.get("metabolomic", "")),
    }


def enrich_case(case: dict) -> tuple[dict, dict, pd.DataFrame, list[dict], list[str]]:
    marker_recommendations = recommend_marker_panel(case)
    recommended = marker_recommendations["recommended_markers"]
    case.setdefault("genomic", recommended.get("genomic", []))
    case.setdefault("transcriptomic", recommended.get("transcriptomic", []))
    case.setdefault("proteomic", recommended.get("proteomic", []))
    case.setdefault("metabolomic", recommended.get("metabolomic", []))
    case["recommendation_rows"] = marker_recommendations["recommendation_rows"]
    analysis = analyze_case(case)
    if not analysis.get("treatment_orientation"):
        analysis["treatment_orientation"] = fallback_treatment_orientation(analysis)
    evidence_rows = retrieve_curated_evidence(case, analysis)
    ai_summary = build_ai_summary(case, analysis, evidence_rows)
    exams_df = recommended_lab_tests(case, marker_recommendations, evidence_rows)
    case["evidence_rows"] = evidence_rows
    case["ai_summary"] = ai_summary
    case["recommended_exams"] = exams_df.to_dict("records")
    return analysis, marker_recommendations, exams_df, evidence_rows, ai_summary


def build_report_pdf(case: dict, analysis: dict, report_type: str) -> bytes:
    """Genera PDF y evita que la app se rompa si el modulo de reportes esta desactualizado."""
    try:
        return build_pdf(case, analysis, report_type=report_type)
    except TypeError:
        return build_pdf(case, analysis)


def show_ai_response(case: dict, analysis: dict, exams_df: pd.DataFrame, evidence_rows: list[dict], ai_summary: list[str]) -> None:
    with st.chat_message("user"):
        st.markdown(
            f"""
            **Ingreso enviado a BioNexus IA**

            Paciente: **{case.get('patient_name', 'No informado')}**  
            ID: **{case.get('patient_id', 'No informado')}**  
            Sintomatologia: {', '.join(case.get('symptoms', [])) or 'No informada'}  
            Pregunta clinico-laboratorial: {case.get('presumptive_diagnosis') or 'No informada'}
            """
        )

    with st.chat_message("assistant"):
        st.markdown("**BioNexus IA responde**")
        for line in ai_summary:
            st.write(f"- {line}")

    st.markdown('<div class="section-title">Examenes de laboratorio relevantes y justificacion</div>', unsafe_allow_html=True)
    st.dataframe(exams_df, width="stretch", hide_index=True)
    st.markdown('<div class="section-title">Evidencia curada recuperada</div>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(evidence_rows)[["profile", "clinical_use", "markers", "limitations", "source", "source_url"]],
        width="stretch",
        hide_index=True,
    )
    st.info(
        f"Se guardo el ingreso con ID: {case['patient_id']}. Para seguimiento, abre la pestana "
        "'Seguimiento / datos guardados', escribe ese ID y carga los resultados del laboratorio."
    )

    st.markdown('<div class="section-title">Descarga preliminar</div>', unsafe_allow_html=True)
    patient_pdf = build_report_pdf(case, analysis, report_type="patient")
    technical_pdf = build_report_pdf(case, analysis, report_type="technical")
    p1, p2 = st.columns(2)
    with p1:
        st.download_button(
            "PDF preliminar para paciente",
            data=patient_pdf,
            file_name=f"plan_preliminar_paciente_{case['patient_id']}.pdf",
            mime="application/pdf",
            type="primary",
        )
    with p2:
        st.download_button(
            "PDF preliminar tecnico",
            data=technical_pdf,
            file_name=f"plan_preliminar_tecnico_{case['patient_id']}.pdf",
            mime="application/pdf",
        )


def show_interpretation(case: dict) -> None:
    analysis, marker_recommendations, exams_df, evidence_rows, ai_summary = enrich_case(case)
    summary = analysis["summary"]
    st.markdown('<div class="section-title">Interpretacion profesional para liberacion</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Alerta", summary.get("alert", "No informado"))
    with c2:
        metric_card("Confianza", summary.get("confidence", "No informado"))
    with c3:
        metric_card("Clasificacion", summary.get("molecular_class", "No informado"))

    st.markdown('<div class="small-title">Interpretacion laboratorial</div>', unsafe_allow_html=True)
    for item in analysis["interpretations"]:
        st.write(f"- {item}")
    st.markdown('<div class="small-title">Hipotesis diagnostica</div>', unsafe_allow_html=True)
    for item in analysis.get("diagnostic_hypothesis", []):
        st.write(f"- {item}")
    st.markdown('<div class="small-title">Orientacion terapeutica supervisada</div>', unsafe_allow_html=True)
    for item in analysis.get("treatment_orientation", []):
        st.write(f"- {item}")
    st.warning("No prescribe antibiotico, dosis ni duracion. Validar con cultivo/antibiograma, guias institucionales y medico tratante.")

    st.markdown('<div class="section-title">Biomarcadores candidatos</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(analysis["candidates"]), width="stretch", hide_index=True)
    st.plotly_chart(build_bar_figure(analysis), width="stretch")

    st.markdown('<div class="section-title">Descarga de informes</div>', unsafe_allow_html=True)
    patient_pdf = build_report_pdf(case, analysis, report_type="patient")
    technical_pdf = build_report_pdf(case, analysis, report_type="technical")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Informe de laboratorio del paciente",
            data=patient_pdf,
            file_name=f"informe_paciente_{case['patient_id']}.pdf",
            mime="application/pdf",
            type="primary",
        )
    with d2:
        st.download_button(
            "Informe tecnico con justificaciones y bases",
            data=technical_pdf,
            file_name=f"informe_tecnico_bionexus_{case['patient_id']}.pdf",
            mime="application/pdf",
        )


def chat_intake_view() -> None:
    st.markdown('<div class="section-title">Que integra BioNexus IA</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="omic-grid">
            <div class="omic-card">
                <div class="omic-icon">DNA</div>
                <strong>Genomica</strong>
                <span>Evalua genes, variantes, mutaciones y biomarcadores moleculares relevantes para priorizacion diagnostica.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">RNA</div>
                <strong>Transcriptomica</strong>
                <span>Integra genes sobreexpresados o subexpresados para reconocer rutas biologicas activas.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">PRO</div>
                <strong>Proteomica</strong>
                <span>Relaciona proteinas aumentadas o disminuidas con inflamacion, proliferacion y seguimiento.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">MET</div>
                <strong>Metabolomica</strong>
                <span>Analiza metabolitos como lactato, glucosa o ATP para orientar alteraciones energeticas.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Mini ingreso del paciente</div>', unsafe_allow_html=True)
    with st.form("chat_intake_form"):
        patient_name = st.text_input("Nombre del paciente", placeholder="Ejemplo: Paciente simulado 01")
        age = st.number_input("Edad", min_value=0, max_value=120, value=35)
        patient_gender = st.selectbox("Genero/Sexo", ["Femenino", "Masculino", "No binario", "Otro", "No informado"])
        patient_id = st.text_input("ID del paciente o muestra", placeholder="Ejemplo: BNX-0001")
        report_datetime = st.text_input("Fecha automatica", value=now_report_datetime(), disabled=True)
        symptoms = st.text_area("Sintomatologia", placeholder="fiebre, fatiga, dolor articular")
        presumptive_diagnosis = st.text_input("Sospecha o pregunta clinico-laboratorial", placeholder="Ejemplo: sospecha de proceso infeccioso")
        bacteriologist_name = st.text_input("Bacteriologo a cargo", placeholder="Nombre del profesional")
        submitted = st.form_submit_button("Enviar a BioNexus AI", type="primary")

    if submitted:
        if not patient_id.strip():
            st.error("Debes ingresar un ID para guardar y recuperar el caso.")
            return
        intake = {
            "workflow_status": "Pendiente por traer resultados de laboratorio",
            "patient_name": patient_name,
            "age": age,
            "patient_gender": patient_gender,
            "patient_id": patient_id.strip(),
            "report_datetime": report_datetime,
            "symptoms": symptoms,
            "presumptive_diagnosis": presumptive_diagnosis,
            "bacteriologist_name": bacteriologist_name,
        }
        case = base_case_from_intake(intake)
        analysis, marker_recommendations, exams_df, evidence_rows, ai_summary = enrich_case(case)
        intake["recommended_exams"] = exams_df.to_dict("records")
        intake["recommendation_rows"] = marker_recommendations["recommendation_rows"]
        save_patient_record(patient_id.strip(), intake)

        show_ai_response(case, analysis, exams_df, evidence_rows, ai_summary)


def follow_up_view() -> None:
    st.markdown('<div class="section-title">Seguimiento / datos guardados</div>', unsafe_allow_html=True)
    st.info("Para continuar un caso guardado, escribe el mismo ID del paciente o muestra. Ejemplo: si guardaste ID 01, busca 01.")
    saved_df = list_patient_records()
    if not saved_df.empty:
        st.dataframe(saved_df, width="stretch", hide_index=True)
    else:
        st.info("Aun no hay pacientes guardados en esta instancia.")

    patient_id = st.text_input("Buscar por ID del paciente o muestra")
    if not patient_id:
        return
    record = load_patient_record(patient_id.strip())
    if not record:
        st.error("No encontre un caso con ese ID.")
        return

    with st.chat_message("assistant"):
        st.markdown(
            f"""
            **Caso encontrado**

            Paciente: **{record.get('patient_name', 'No informado')}**  
            ID: **{patient_id.strip()}**  
            Sintomatologia inicial: {record.get('symptoms', 'No informado')}

            Ahora puedes cargar los resultados del laboratorio y BioNexus IA continuara la interpretacion profesional.
            """
        )
    if record.get("recommended_exams"):
        st.markdown('<div class="small-title">Examenes sugeridos previamente</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(record["recommended_exams"]), width="stretch", hide_index=True)

    with st.form("follow_up_results"):
        sample_type = st.selectbox("Tipo de muestra", ["Sangre", "Suero", "Plasma", "Tejido", "Orina", "Hisopado", "Otro"])
        sample_quality = st.selectbox("Calidad de muestra", ["Adecuada", "Hemolizada", "Lipemica", "Insuficiente"])
        c1, c2 = st.columns(2)
        collection_date = c1.date_input("Fecha de toma de muestra")
        reception_date = c2.date_input("Fecha de recepcion")
        method_used = st.selectbox("Metodo usado", ["PCR", "qPCR", "ELISA", "Secuenciacion", "Espectrometria", "Inmunoensayo", "Otro"])
        lab_results = st.text_area("Resultados del laboratorio", placeholder="PCR 48 mg/L, VSG 60 mm/h, lactato 3.1 mmol/L")
        c3, c4, c5 = st.columns([1.4, 1, 1])
        reference_values = c3.text_input("Valores de referencia", placeholder="PCR < 5 mg/L")
        units = c4.text_input("Unidades", placeholder="mg/L")
        result_status = c5.selectbox("Resultado", ["Normal", "Anormal", "Critico"])
        workflow_status = st.selectbox(
            "Estado del caso",
            [
                "Resultados cargados: pendiente liberacion",
                "Seguimiento activo",
                "Caso resuelto / seguimiento cerrado",
                "Requiere revision prioritaria",
            ],
        )
        preanalytical_observations = st.text_area("Observaciones preanaliticas")
        st.markdown('<div class="small-title">Datos omicos si estan disponibles</div>', unsafe_allow_html=True)
        genomic = st.text_area("Genomica", value=", ".join(record.get("genomic", [])))
        transcriptomic = st.text_area("Transcriptomica", value=", ".join(record.get("transcriptomic", [])))
        proteomic = st.text_area("Proteomica", value=", ".join(record.get("proteomic", [])))
        metabolomic = st.text_area("Metabolomica", value=", ".join(record.get("metabolomic", [])))
        submitted = st.form_submit_button("Continuar interpretacion con BioNexus AI", type="primary")

    if submitted:
        intake = {**record}
        intake.update(
            {
                "workflow_status": workflow_status,
                "sample_type": sample_type,
                "sample_quality": sample_quality,
                "collection_date": str(collection_date),
                "reception_date": str(reception_date),
                "method_used": method_used,
                "lab_results": lab_results,
                "reference_values": reference_values,
                "units": units,
                "result_status": result_status,
                "preanalytical_observations": preanalytical_observations,
                "genomic": genomic,
                "transcriptomic": transcriptomic,
                "proteomic": proteomic,
                "metabolomic": metabolomic,
                "report_datetime": now_report_datetime(),
            }
        )
        case = base_case_from_intake(intake)
        save_patient_record(patient_id.strip(), intake)
        show_interpretation(case)


def dashboard_view() -> None:
    st.markdown('<div class="section-title">Resumen de pacientes</div>', unsafe_allow_html=True)
    saved_df = list_patient_records()
    if saved_df.empty:
        st.info("Aun no hay pacientes guardados. Cuando ingreses pacientes, apareceran aqui.")
        return

    pending = saved_df[saved_df["Estado"].str.contains("Ingreso inicial|pendiente|Pendiente", case=False, na=False)]
    loaded = saved_df[saved_df["Estado"].str.contains("Resultados cargados|Seguimiento activo", case=False, na=False)]
    resolved = saved_df[saved_df["Estado"].str.contains("resuelto|cerrado", case=False, na=False)]
    priority = saved_df[saved_df["Estado"].str.contains("prioritaria|Critico|critico", case=False, na=False)]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total de pacientes", str(len(saved_df)))
    with c2:
        metric_card("Faltan resultados", str(len(pending)))
    with c3:
        metric_card("En seguimiento", str(len(loaded)))
    with c4:
        metric_card("Resueltos", str(len(resolved)))

    if not priority.empty:
        st.warning("Hay casos marcados para revision prioritaria.")
        st.dataframe(priority, width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Pacientes que faltan por traer resultados de laboratorio</div>', unsafe_allow_html=True)
    st.dataframe(pending if not pending.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Pacientes en seguimiento o con resultados cargados</div>', unsafe_allow_html=True)
    st.dataframe(loaded if not loaded.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Casos resueltos o cerrados</div>', unsafe_allow_html=True)
    st.dataframe(resolved if not resolved.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)


def safety_view() -> None:
    st.markdown('<div class="section-title">Seguridad, trazabilidad y siguiente fase</div>', unsafe_allow_html=True)
    st.write("- Esta version guarda datos en SQLite local de la app. En Streamlit Cloud puede ser persistencia temporal.")
    st.write("- Para uso real se necesita login, roles, cifrado, auditoria y base de datos segura.")
    st.write("- Debe existir estado del informe: borrador, revisado, liberado.")
    st.write("- La IA debe usar fuentes curadas, versionadas y trazables, no internet abierto sin filtro.")
    st.write("- Para antimicrobianos: no formula antibiotico ni dosis; exige cultivo/antibiograma, guias institucionales y validacion medica.")


init_db()
render_styles()
hero()

intake_tab, follow_tab, dashboard_tab, safety_tab = st.tabs(
    ["Ingreso del paciente", "Seguimiento por ID", "Resumen de pacientes", "Validacion y seguridad"]
)
with intake_tab:
    chat_intake_view()
with follow_tab:
    follow_up_view()
with dashboard_tab:
    dashboard_view()
with safety_tab:
    safety_view()
