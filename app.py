from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.analyzer import analyze_case, parse_items, recommend_marker_panel
from modules.knowledge_base import build_ai_interpretive_summary, retrieve_curated_evidence
from modules.report import build_pdf


APP_DIR = Path(__file__).parent
EXAMPLE_PATH = APP_DIR / "data" / "example_case.json"
LAB_NAME = "BioNexus AI"
REPORT_TZ = ZoneInfo("America/Bogota")


st.set_page_config(
    page_title="BioNexus AI",
    page_icon="🧬",
    layout="wide",
)


def load_example_case() -> dict:
    """Lee el caso de ejemplo para llenar rapidamente el formulario."""

    with EXAMPLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def join_items(items: list[str]) -> str:
    """Convierte listas del ejemplo en texto editable para Streamlit."""

    return ", ".join(items)


def current_report_datetime() -> str:
    """Fecha y hora de expedicion del informe en hora de Colombia."""

    return datetime.now(REPORT_TZ).strftime("%Y-%m-%d %H:%M:%S")


def render_styles() -> None:
    """Estilos visuales: salud digital, biotecnologia e IA."""

    st.markdown(
        """
        <style>
        :root {
            --bio-teal: #0f766e;
            --bio-cyan: #0891b2;
            --bio-indigo: #4f46e5;
            --bio-gold: #d97706;
            --bio-ink: #0f172a;
            --bio-muted: #64748b;
            --bio-soft: #ecfeff;
            --bio-line: #cbd5e1;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(20, 184, 166, 0.13), transparent 28rem),
                linear-gradient(180deg, #f8fafc 0%, #eef9fb 100%);
            color: var(--bio-ink);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            border: 1px solid rgba(15, 118, 110, 0.18);
            background:
                linear-gradient(135deg, rgba(15, 118, 110, 0.96), rgba(8, 145, 178, 0.9)),
                repeating-linear-gradient(90deg, rgba(255,255,255,.12) 0 1px, transparent 1px 42px);
            color: white;
            padding: 2.15rem;
            border-radius: 18px;
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.14);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .hero::after {
            content: "AI";
            position: absolute;
            right: 2rem;
            bottom: -1.2rem;
            color: rgba(255,255,255,.12);
            font-size: 7rem;
            font-weight: 900;
        }
        .hero h1 {
            font-size: 3rem;
            margin: 0;
            letter-spacing: 0;
        }
        .hero p {
            font-size: 1.08rem;
            margin: .4rem 0 0 0;
        }
        .warning {
            background: #fff7ed;
            border: 1px solid #fed7aa;
            color: #9a3412;
            padding: .85rem 1rem;
            border-radius: 10px;
            margin: .75rem 0 1.25rem 0;
            font-weight: 600;
        }
        .guide-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .85rem;
            margin: 1rem 0 1.25rem 0;
        }
        .guide-card {
            background: rgba(255,255,255,.9);
            border: 1px solid var(--bio-line);
            border-left: 5px solid var(--bio-teal);
            border-radius: 12px;
            padding: 1rem;
            min-height: 124px;
        }
        .guide-card strong {
            color: #155e75;
            display: block;
            margin-bottom: .35rem;
        }
        .guide-card span {
            color: var(--bio-muted);
            font-size: .92rem;
            line-height: 1.35rem;
        }
        .step-title {
            color: #0f172a;
            font-weight: 850;
            font-size: 1.08rem;
            margin: 1.2rem 0 .25rem 0;
            padding: .65rem .85rem;
            border: 1px solid #dbeafe;
            border-left: 6px solid var(--bio-cyan);
            border-radius: 10px;
            background: rgba(255,255,255,.78);
        }
        .field-note {
            color: #475569;
            font-size: .86rem;
            margin: -.35rem 0 .65rem 0;
        }
        .mini-note {
            background: #f8fafc;
            border: 1px dashed #94a3b8;
            border-radius: 10px;
            padding: .8rem .9rem;
            color: #334155;
            font-size: .92rem;
            margin: .35rem 0 .95rem 0;
        }
        .metric-card {
            background: rgba(255,255,255,.88);
            border: 1px solid var(--bio-line);
            border-radius: 12px;
            padding: 1rem;
            min-height: 112px;
        }
        .metric-label {
            color: var(--bio-muted);
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .04em;
        }
        .metric-value {
            color: var(--bio-ink);
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: .25rem;
        }
        .executive-card {
            background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(248,250,252,.96));
            border: 1px solid var(--bio-line);
            border-radius: 14px;
            padding: 1.15rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
            margin: .8rem 0 1rem 0;
        }
        .executive-card h3 {
            color: #0f172a;
            margin: 0 0 .45rem 0;
            font-size: 1.18rem;
        }
        .executive-card p {
            color: #334155;
            line-height: 1.5rem;
            margin: .2rem 0;
        }
        .status-pill {
            display: inline-block;
            border-radius: 999px;
            padding: .3rem .7rem;
            font-size: .82rem;
            font-weight: 800;
            margin: .25rem .35rem .25rem 0;
            border: 1px solid rgba(15,23,42,.08);
        }
        .pill-low {
            background: #ecfdf5;
            color: #047857;
        }
        .pill-mid {
            background: #fffbeb;
            color: #b45309;
        }
        .pill-high {
            background: #fef2f2;
            color: #b91c1c;
        }
        .pill-blue {
            background: #eff6ff;
            color: #1d4ed8;
        }
        .callout {
            background: #f8fafc;
            border: 1px solid #dbeafe;
            border-left: 5px solid var(--bio-indigo);
            border-radius: 12px;
            padding: .9rem 1rem;
            color: #334155;
            margin: .7rem 0;
        }
        .small-title {
            color: #155e75;
            font-weight: 800;
            margin: .35rem 0 .25rem 0;
        }
        .support-badge {
            background: #ecfeff;
            border: 1px solid #67e8f9;
            color: #155e75;
            border-radius: 999px;
            display: inline-block;
            font-weight: 800;
            padding: .28rem .7rem;
            margin-bottom: .6rem;
        }
        .section-title {
            color: #155e75;
            font-weight: 800;
            font-size: 1.25rem;
            margin: 1rem 0 .4rem 0;
        }
        .report-box {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--bio-line);
            border-radius: 12px;
            padding: 1rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--bio-line);
            border-radius: 10px;
            overflow: hidden;
        }
        @media (max-width: 900px) {
            .guide-grid {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: 2.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def guide_card(title: str, text: str) -> str:
    """Devuelve una tarjeta HTML de guia para explicar el flujo."""

    return f'<div class="guide-card"><strong>{title}</strong><span>{text}</span></div>'


def step_title(number: int, title: str) -> None:
    """Muestra un titulo numerado dentro del formulario."""

    st.markdown(f'<div class="step-title">{number}. {title}</div>', unsafe_allow_html=True)


def field_note(text: str) -> None:
    """Muestra una nota breve debajo de campos amplios."""

    st.markdown(f'<div class="field-note">{text}</div>', unsafe_allow_html=True)


def pill_class(value: str) -> str:
    """Asigna color visual para niveles bajo, medio/moderado y alto."""

    normalized = value.lower()
    if "alto" in normalized:
        return "pill-high"
    if "medio" in normalized or "moderado" in normalized:
        return "pill-mid"
    if "bajo" in normalized:
        return "pill-low"
    return "pill-blue"


def executive_summary(summary: dict, analysis: dict) -> None:
    """Muestra una lectura ejecutiva del caso para exposicion."""

    risk = summary["risk"]
    confidence = summary["confidence"]
    molecular_class = summary["molecular_class"]
    candidate_count = len(analysis["candidates"])
    pathway_count = len(analysis["altered_pathways"])

    st.markdown(
        f"""
        <div class="executive-card">
            <h3>Resumen ejecutivo del caso simulado</h3>
            <p>
                BioNexus AI integro los datos clinicos y multi-omicos ingresados.
                El caso se clasifica como <strong>{molecular_class}</strong>, con
                <strong>{candidate_count}</strong> biomarcador(es) candidato(s) y
                <strong>{pathway_count}</strong> ruta(s) o proceso(s) posiblemente alterado(s).
            </p>
            <span class="status-pill {pill_class(risk)}">Riesgo academico: {risk}</span>
            <span class="status-pill {pill_class(confidence)}">Confianza: {confidence}</span>
            <span class="status-pill pill-blue">Resultado simulado</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fallback_treatment_orientation(analysis: dict) -> list[str]:
    """Genera orientacion academica si el motor de analisis aun no la trae."""

    categories = {
        row.get("Categoria", "").lower()
        for row in analysis.get("candidates", [])
        if row.get("Categoria") and row.get("Categoria") != "no clasificado"
    }
    suggestions = []

    if "inflamacion" in categories:
        suggestions.append(
            "Correlacionar hallazgos inflamatorios con PCR, VSG, hemograma, cultivo u otros estudios segun criterio profesional."
        )
    if "ciclo celular" in categories:
        suggestions.append(
            "Considerar revision interdisciplinaria y validacion molecular si el caso simula proliferacion celular o proceso tumoral."
        )
    if "metabolismo" in categories:
        suggestions.append(
            "Explorar seguimiento metabolico con glucosa, lactato, perfil energetico u otras pruebas complementarias segun el contexto."
        )
    if "reparacion adn" in categories:
        suggestions.append(
            "Plantear validacion genomica y consejeria genetica en un escenario real antes de decisiones preventivas o terapeuticas."
        )
    if "estres celular" in categories:
        suggestions.append(
            "Correlacionar posible estres celular o hipoxia con datos clinicos, imagenologicos y de laboratorio."
        )
    if not suggestions:
        suggestions.append(
            "Ampliar datos clinicos, laboratorio y biomarcadores antes de proponer una orientacion terapeutica academica."
        )

    suggestions.append(
        "Orientacion no prescriptiva: BioNexus AI no formula tratamientos, dosis ni conductas clinicas; organiza hipotesis para revision profesional."
    )
    return suggestions


def clinical_support_notice() -> None:
    st.markdown(
        """
        <div class="callout">
        <span class="support-badge">Apoyo interpretativo supervisado</span><br>
        BioNexus AI organiza datos clinicos, preanaliticos, laboratoriales y multi-omicos para apoyar
        la interpretacion del bacteriologo/laboratorista clinico. El informe debe ser revisado,
        validado y liberado por el profesional responsable y correlacionado con el medico tratante.
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_network_figure(candidates: list[dict], pathways: list[dict]) -> go.Figure:
    """Dibuja una red sencilla entre biomarcadores candidatos y rutas."""

    nodes = []
    edges = []

    for row in candidates:
        marker = row["Biomarcador candidato"]
        pathway = row["Ruta asociada"]
        if pathway == "requiere anotacion externa":
            continue
        nodes.extend([marker, pathway])
        edges.append((marker, pathway))

    unique_nodes = list(dict.fromkeys(nodes))[:18]
    if not unique_nodes:
        fig = go.Figure()
        fig.add_annotation(text="No hay biomarcadores suficientes para construir la red.", showarrow=False)
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
        return fig

    marker_nodes = [node for node in unique_nodes if any(node == row["Biomarcador candidato"] for row in candidates)]
    pathway_nodes = [node for node in unique_nodes if node not in marker_nodes]

    positions = {}
    for index, node in enumerate(marker_nodes):
        positions[node] = (0.15, 1 - (index + 1) / (len(marker_nodes) + 1))
    for index, node in enumerate(pathway_nodes):
        positions[node] = (0.85, 1 - (index + 1) / (len(pathway_nodes) + 1))

    edge_x, edge_y = [], []
    for start, end in edges:
        if start in positions and end in positions:
            x0, y0 = positions[start]
            x1, y1 = positions[end]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1.4, color="#94a3b8"),
            hoverinfo="none",
        )
    )

    for group_name, group_nodes, color in [
        ("Biomarcadores", marker_nodes, "#0f766e"),
        ("Rutas", pathway_nodes, "#7c3aed"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=[positions[node][0] for node in group_nodes],
                y=[positions[node][1] for node in group_nodes],
                mode="markers+text",
                marker=dict(size=22, color=color, line=dict(color="white", width=2)),
                text=group_nodes,
                textposition="middle right" if group_name == "Biomarcadores" else "middle left",
                name=group_name,
            )
        )

    fig.update_layout(
        height=430,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        legend=dict(orientation="h", y=1.04, x=0),
    )
    return fig


render_styles()

example = load_example_case()

with st.sidebar:
    st.header("Panel de trabajo")
    use_example = st.toggle("Cargar caso de ejemplo", value=True)
    st.caption("Usa el caso de ejemplo o escribe tus propios datos simulados.")
    st.divider()
    st.markdown("**Flujo sugerido**")
    st.write("1. Completa datos clinicos.")
    st.write("2. Revisa el panel recomendado.")
    st.write("3. Edita marcadores si lo necesitas.")
    st.write("4. Analiza y descarga el reporte.")
    st.divider()
    st.info("Prototipo academico. No reemplaza criterio clinico ni profesional.")

source = example if use_example else {}
report_datetime = current_report_datetime()

st.markdown(
    """
    <div class="hero">
        <h1>BioNexus AI</h1>
        <p>Informe academico de apoyo diagnostico y terapeutico basado en integracion multi-omica.</p>
        <p><strong>Genomica | Transcriptomica | Proteomica | Metabolomica | Datos clinicos</strong></p>
    </div>
    <div class="warning">Herramienta de apoyo interpretativo laboratorial. Requiere validacion y liberacion por bacteriologo/laboratorista clinico responsable.</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="guide-grid">
    """
    + guide_card(
        "Que vas a ingresar",
        "Datos administrativos, muestra, fase preanalitica, sintomas, laboratorio y marcadores omicos.",
    )
    + guide_card(
        "Como escribirlos",
        "Separa cada dato con coma o salto de linea. Ejemplo: IL6, TNF, CRP.",
    )
    + guide_card(
        "Que entrega el sistema",
        "Panel recomendado, alertas, hipotesis diagnostica, orientacion supervisada y reporte PDF.",
    )
    + """
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Formulario guiado de ingreso de datos</div>', unsafe_allow_html=True)
clinical_support_notice()

with st.form("case_form"):
    step_title(1, "Datos administrativos del informe")
    st.markdown(
        '<div class="mini-note">Usa datos simulados o anonimizados. Este encabezado permite que el informe se vea mas cercano a un reporte academico de laboratorio.</div>',
        unsafe_allow_html=True,
    )
    patient_name = st.text_input(
        "Nombre del paciente",
        value=source.get("patient_name", "Paciente simulado"),
        placeholder="Ejemplo: Paciente simulado 01",
    )

    age = st.number_input("Edad del paciente", min_value=0, max_value=120, value=int(source.get("age", 35)))

    patient_gender = st.selectbox(
        "Genero del paciente",
        ["Femenino", "Masculino", "No binario", "Otro", "No informado"],
        index=["Femenino", "Masculino", "No binario", "Otro", "No informado"].index(
            source.get("patient_gender", source.get("sex", "No informado"))
        )
        if source.get("patient_gender", source.get("sex", "No informado"))
        in ["Femenino", "Masculino", "No binario", "Otro", "No informado"]
        else 4,
    )

    patient_id = st.text_input(
        "ID del paciente o muestra",
        value=source.get("patient_id", "BNX-0001"),
        placeholder="Ejemplo: BNX-0001",
    )

    st.text_input("Fecha y hora automatica de expedicion", value=report_datetime, disabled=True)
    field_note("La fecha y hora se generan automaticamente al cargar o actualizar la app.")

    lab_name = st.text_input("Nombre del laboratorio", value=LAB_NAME)

    bacteriologist_name = st.text_input(
        "Nombre del bacteriologo a cargo",
        value=source.get("bacteriologist_name", ""),
        placeholder="Nombre del profesional",
    )

    step_title(2, "Datos de muestra y fase preanalitica")
    sample_a, sample_b = st.columns(2)
    sample_type = sample_a.selectbox(
        "Tipo de muestra",
        ["Sangre", "Suero", "Plasma", "Tejido", "Orina", "Hisopado", "Otro"],
    )
    sample_quality = sample_b.selectbox(
        "Calidad de muestra",
        ["Adecuada", "Hemolizada", "Lipemica", "Insuficiente"],
    )
    sample_c, sample_d = st.columns(2)
    collection_date = sample_c.date_input("Fecha de toma de muestra")
    reception_date = sample_d.date_input("Fecha de recepcion")
    method_used = st.selectbox(
        "Metodo usado",
        ["PCR", "qPCR", "ELISA", "Secuenciacion", "Espectrometria", "Inmunoensayo", "Otro"],
    )
    preanalytical_observations = st.text_area(
        "Observaciones preanaliticas",
        placeholder="Ejemplo: muestra recibida en cadena de frio, volumen adecuado, leve hemolisis",
    )

    step_title(3, "Resultados del laboratorio")
    lab_results = st.text_area(
        "Resultados del laboratorio",
        value=join_items(source.get("lab_results", [])),
        placeholder="PCR elevada, VSG elevada, LDH elevada",
    )
    lab_a, lab_b, lab_c = st.columns([1.2, 1, 1])
    reference_values = lab_a.text_input(
        "Valores de referencia",
        placeholder="Ejemplo: PCR < 5 mg/L; lactato 0.5-2.2 mmol/L",
    )
    units = lab_b.text_input("Unidades", placeholder="mg/L, mmol/L, copias/mL")
    result_status = lab_c.selectbox("Resultado", ["Normal", "Anormal", "Critico"])
    field_note("Estos datos permiten reglas por rango, metodo, estado del resultado y calidad de muestra.")

    step_title(4, "Sintomas del paciente")
    symptoms = st.text_area(
        "Sintomas del paciente",
        value=join_items(source.get("symptoms", [])),
        placeholder="fatiga, fiebre, dolor articular",
    )
    field_note("Escribe sintomas separados por comas. Ejemplo: fatiga, fiebre, dolor articular.")

    with st.expander("Contexto adicional opcional para orientar el panel"):
        col_b, col_c = st.columns([1, 2])
        sex = col_b.selectbox(
            "Sexo biologico reportado",
            ["Femenino", "Masculino", "Intersexual", "No informado"],
            index=["Femenino", "Masculino", "Intersexual", "No informado"].index(
                source.get("sex", patient_gender if patient_gender in ["Femenino", "Masculino"] else "No informado")
            )
            if source.get("sex", patient_gender if patient_gender in ["Femenino", "Masculino"] else "No informado")
            in ["Femenino", "Masculino", "Intersexual", "No informado"]
            else 3,
        )
        presumptive_diagnosis = col_c.text_input(
            "Diagnostico presuntivo o pregunta de investigacion",
            value=source.get("presumptive_diagnosis", ""),
            placeholder="Ejemplo: sindrome inflamatorio en estudio",
        )
        field_note("Este contexto ayuda a recomendar marcadores, pero no se interpreta como diagnostico definitivo.")

    preliminary_case = {
        "presumptive_diagnosis": presumptive_diagnosis,
        "symptoms": parse_items(symptoms),
        "lab_results": parse_items(lab_results),
    }
    marker_recommendations = recommend_marker_panel(preliminary_case)
    recommended_markers = marker_recommendations["recommended_markers"]

    step_title(5, "Panel sugerido por BioNexus AI")
    st.markdown(
        '<div class="mini-note">Segun el contexto clinico simulado, la app recomienda marcadores candidatos y explica por que pueden ser utiles para una exploracion academica. Puedes aceptar el panel o editarlo.</div>',
        unsafe_allow_html=True,
    )
    recommendation_df = pd.DataFrame(marker_recommendations["recommendation_rows"])
    st.dataframe(recommendation_df, use_container_width=True, hide_index=True)
    use_recommended_panel = st.checkbox(
        "Usar automaticamente este panel recomendado como punto de partida",
        value=True,
    )

    genomic_default = recommended_markers["genomic"] if use_recommended_panel else source.get("genomic", [])
    transcriptomic_default = (
        recommended_markers["transcriptomic"] if use_recommended_panel else source.get("transcriptomic", [])
    )
    proteomic_default = recommended_markers["proteomic"] if use_recommended_panel else source.get("proteomic", [])
    metabolomic_default = (
        recommended_markers["metabolomic"] if use_recommended_panel else source.get("metabolomic", [])
    )

    step_title(6, "Datos omicos editables")
    st.markdown(
        '<div class="mini-note">Estos campos se llenan con la recomendacion automatica. El bacteriologo, bioinformatico o estudiante puede modificar, agregar o retirar marcadores antes de analizar.</div>',
        unsafe_allow_html=True,
    )
    col_1, col_2 = st.columns(2)
    genomic = col_1.text_area(
        "Genomica - variantes, mutaciones o genes alterados",
        value=join_items(genomic_default),
        placeholder="TP53, BRCA1, EGFR",
    )
    col_1.caption("Ejemplo: TP53, BRCA1, EGFR. Representa genes con variantes o alteraciones simuladas.")
    transcriptomic = col_2.text_area(
        "Transcriptomica - genes sobreexpresados o subexpresados",
        value=join_items(transcriptomic_default),
        placeholder="IL6, TNF, MKI67",
    )
    col_2.caption("Ejemplo: IL6, TNF, MKI67. Representa cambios en expresion genica.")

    col_3, col_4 = st.columns(2)
    proteomic = col_3.text_area(
        "Proteomica - proteinas aumentadas o disminuidas",
        value=join_items(proteomic_default),
        placeholder="CRP, CXCL8, LDHA",
    )
    col_3.caption("Ejemplo: CRP, CXCL8, LDHA. Representa proteinas alteradas en la muestra.")
    metabolomic = col_4.text_area(
        "Metabolomica - metabolitos alterados",
        value=join_items(metabolomic_default),
        placeholder="Lactato, Glucosa, ATP",
    )
    col_4.caption("Ejemplo: Lactato, Glucosa, ATP. Representa metabolitos energeticos o de interes.")

    submitted = st.form_submit_button("Analizar caso simulado y generar reporte", type="primary")


case = {
    "patient_name": patient_name,
    "patient_gender": patient_gender,
    "patient_id": patient_id,
    "report_datetime": report_datetime,
    "lab_name": lab_name,
    "bacteriologist_name": bacteriologist_name,
    "sample_type": sample_type,
    "collection_date": str(collection_date),
    "reception_date": str(reception_date),
    "sample_quality": sample_quality,
    "method_used": method_used,
    "reference_values": reference_values,
    "units": units,
    "result_status": result_status,
    "preanalytical_observations": preanalytical_observations,
    "age": age,
    "sex": sex,
    "presumptive_diagnosis": presumptive_diagnosis,
    "symptoms": parse_items(symptoms),
    "genomic": parse_items(genomic),
    "transcriptomic": parse_items(transcriptomic),
    "proteomic": parse_items(proteomic),
    "metabolomic": parse_items(metabolomic),
    "lab_results": parse_items(lab_results),
    "recommendation_rows": marker_recommendations["recommendation_rows"],
}

if submitted or use_example:
    analysis = analyze_case(case)
    if not analysis.get("treatment_orientation"):
        analysis["treatment_orientation"] = fallback_treatment_orientation(analysis)
    evidence_rows = retrieve_curated_evidence(case, analysis)
    ai_summary = build_ai_interpretive_summary(case, analysis, evidence_rows)
    case["evidence_rows"] = evidence_rows
    case["ai_summary"] = ai_summary
    summary = analysis["summary"]

    counts_df = pd.DataFrame(
        {
            "Tipo de dato": list(analysis["omics_counts"].keys()),
            "Alteraciones": list(analysis["omics_counts"].values()),
        }
    )
    bar_fig = go.Figure(
        data=[
            go.Bar(
                x=counts_df["Tipo de dato"],
                y=counts_df["Alteraciones"],
                marker_color=["#0f766e", "#0891b2", "#7c3aed", "#f59e0b"],
            )
        ]
    )
    bar_fig.update_layout(
        title="Numero de alteraciones por tipo de dato",
        height=380,
        margin=dict(l=20, r=20, t=60, b=20),
        yaxis_title="Cantidad",
        xaxis_title="",
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
    )

    candidates_df = pd.DataFrame(analysis["candidates"])
    pathway_df = pd.DataFrame(analysis["altered_pathways"])

    st.markdown('<div class="section-title">Informe BioNexus AI</div>', unsafe_allow_html=True)

    st.markdown('<div class="small-title">Nombre del paciente</div>', unsafe_allow_html=True)
    st.write(case["patient_name"] or "No informado")

    st.markdown('<div class="small-title">Edad del paciente</div>', unsafe_allow_html=True)
    st.write(f"{case['age']} anos")

    st.markdown('<div class="small-title">Genero del paciente</div>', unsafe_allow_html=True)
    st.write(case["patient_gender"] or "No informado")

    st.markdown('<div class="small-title">ID del paciente o muestra</div>', unsafe_allow_html=True)
    st.write(case["patient_id"] or "No informado")

    st.markdown('<div class="small-title">Fecha y hora automatica de expedicion</div>', unsafe_allow_html=True)
    st.write(case["report_datetime"])

    st.markdown('<div class="small-title">Nombre del laboratorio</div>', unsafe_allow_html=True)
    st.write(case["lab_name"] or LAB_NAME)

    st.markdown('<div class="small-title">Nombre del bacteriologo a cargo</div>', unsafe_allow_html=True)
    st.write(case["bacteriologist_name"] or "No informado")

    st.markdown('<div class="small-title">Tipo de muestra</div>', unsafe_allow_html=True)
    st.write(case["sample_type"])

    st.markdown('<div class="small-title">Fecha de toma de muestra</div>', unsafe_allow_html=True)
    st.write(case["collection_date"])

    st.markdown('<div class="small-title">Fecha de recepcion</div>', unsafe_allow_html=True)
    st.write(case["reception_date"])

    st.markdown('<div class="small-title">Calidad de muestra</div>', unsafe_allow_html=True)
    st.write(case["sample_quality"])

    st.markdown('<div class="small-title">Metodo usado</div>', unsafe_allow_html=True)
    st.write(case["method_used"])

    st.markdown('<div class="small-title">Sintomas del paciente</div>', unsafe_allow_html=True)
    st.write(", ".join(case["symptoms"]) or "No informado")

    st.markdown('<div class="small-title">Resultados del laboratorio</div>', unsafe_allow_html=True)
    st.write(", ".join(case["lab_results"]) or "No informado")

    st.markdown('<div class="small-title">Valores de referencia</div>', unsafe_allow_html=True)
    st.write(case["reference_values"] or "No informado")

    st.markdown('<div class="small-title">Unidades</div>', unsafe_allow_html=True)
    st.write(case["units"] or "No informado")

    st.markdown('<div class="small-title">Resultado normal/anormal/critico</div>', unsafe_allow_html=True)
    st.write(case["result_status"])

    st.markdown('<div class="small-title">Observaciones preanaliticas</div>', unsafe_allow_html=True)
    st.write(case["preanalytical_observations"] or "Sin observaciones")

    st.markdown('<div class="section-title">Panel sugerido por BioNexus AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="callout">Este panel se genera con reglas academicas basadas en sintomas, diagnostico presuntivo y resultados de laboratorio. No equivale a una orden clinica ni a una guia terapeutica real.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(recommendation_df, width="stretch", hide_index=True)
    profile_text = ", ".join(marker_recommendations["matched_profiles"])
    st.write(f"**Perfiles detectados:** {profile_text}")

    st.markdown('<div class="section-title">IA con base de conocimiento curada</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="callout">Esta capa simula un motor RAG clinico seguro: recupera evidencia desde una base curada y versionable, no desde internet abierto. En una fase real, estas fuentes se sincronizarian con repositorios oficiales y guias institucionales.</div>',
        unsafe_allow_html=True,
    )
    for item in ai_summary:
        st.write(f"- {item}")
    evidence_df = pd.DataFrame(evidence_rows)
    st.dataframe(
        evidence_df[["profile", "clinical_use", "markers", "limitations", "source", "source_url"]],
        width="stretch",
        hide_index=True,
    )

    st.markdown('<div class="section-title">Datos omicos editables</div>', unsafe_allow_html=True)
    omics_df = pd.DataFrame(
        [
            {"Tipo de dato": "Genomica", "Marcadores ingresados": ", ".join(case["genomic"]) or "No informado"},
            {
                "Tipo de dato": "Transcriptomica",
                "Marcadores ingresados": ", ".join(case["transcriptomic"]) or "No informado",
            },
            {"Tipo de dato": "Proteomica", "Marcadores ingresados": ", ".join(case["proteomic"]) or "No informado"},
            {
                "Tipo de dato": "Metabolomica",
                "Marcadores ingresados": ", ".join(case["metabolomic"]) or "No informado",
            },
        ]
    )
    st.dataframe(omics_df, width="stretch", hide_index=True)

    st.markdown('<div class="section-title">Resultados del analisis academico</div>', unsafe_allow_html=True)
    executive_summary(summary, analysis)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Riesgo academico", summary["risk"])
    with m2:
        metric_card("Nivel de confianza", summary["confidence"])
    with m3:
        metric_card("Biomarcadores", str(len(analysis["candidates"])))
    with m4:
        metric_card("Clasificacion", summary["molecular_class"])

    st.markdown('<div class="small-title">Nivel de alerta</div>', unsafe_allow_html=True)
    st.write(summary.get("alert", "No informado"))

    st.markdown('<div class="small-title">Interpretacion general</div>', unsafe_allow_html=True)
    for item in analysis["interpretations"]:
        st.write(f"- {item}")
    st.markdown(
        '<div class="callout">Las interpretaciones se expresan como posibles asociaciones. Requieren validacion experimental, bioinformatica y revision profesional.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="small-title">Hipotesis diagnostica</div>', unsafe_allow_html=True)
    for item in analysis.get("diagnostic_hypothesis", []):
        st.write(f"- {item}")

    st.markdown('<div class="small-title">Rutas posiblemente alteradas</div>', unsafe_allow_html=True)
    if pathway_df.empty:
        st.info("No se identificaron rutas suficientes con las reglas actuales.")
    else:
        st.dataframe(pathway_df, width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Tabla de biomarcadores candidatos</div>', unsafe_allow_html=True)
    st.dataframe(candidates_df, width="stretch", hide_index=True)

    category_df = (
        candidates_df.groupby("Categoria", as_index=False)
        .size()
        .rename(columns={"size": "Numero de biomarcadores"})
        .sort_values("Numero de biomarcadores", ascending=False)
    )
    st.markdown('<div class="small-title">Distribucion por categoria biologica</div>', unsafe_allow_html=True)
    st.dataframe(category_df, width="stretch", hide_index=True)

    left, right = st.columns([.95, 1.05])
    with left:
        st.plotly_chart(bar_fig, width="stretch")
    with right:
        st.plotly_chart(
            build_network_figure(analysis["candidates"], analysis["altered_pathways"]),
            width="stretch",
        )

    st.markdown('<div class="section-title">Posible orientacion terapeutica academica</div>', unsafe_allow_html=True)
    for item in analysis.get("treatment_orientation", []):
        st.write(f"- {item}")
    st.warning(
        "Esta orientacion no prescribe tratamientos, dosis ni conductas clinicas. Debe ser revisada por profesionales competentes."
    )

    st.markdown('<div class="section-title">Recomendaciones de seguimiento</div>', unsafe_allow_html=True)
    for recommendation in analysis["recommendations"]:
        st.write(f"- {recommendation}")
    st.write("- Programar revision del caso con el equipo academico o profesional responsable.")
    st.write("- Documentar cambios en sintomas, resultados de laboratorio y nuevos datos omicos antes de repetir el analisis.")

    st.markdown('<div class="section-title">Boton para descargar el informe completo en PDF</div>', unsafe_allow_html=True)
    pdf_bytes = build_pdf(case, analysis)
    st.download_button(
        "Descargar informe completo",
        data=pdf_bytes,
        file_name="informe_bionexus_ai.pdf",
        mime="application/pdf",
        type="primary",
    )

    with st.expander("Guion breve para explicar este resultado en una exposicion"):
        st.write(
            "BioNexus AI integra datos clinicos y multi-omicos simulados para proponer biomarcadores candidatos. "
            "El sistema usa reglas transparentes, no modelos clinicos reales, por lo que sus resultados se deben "
            "leer como posibles asociaciones academicas. La clasificacion molecular y el nivel de riesgo son "
            "orientativos y requieren validacion profesional."
        )
