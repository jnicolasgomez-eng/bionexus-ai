from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.analyzer import analyze_case, parse_items, recommend_marker_panel
from modules.report import build_pdf


APP_DIR = Path(__file__).parent
EXAMPLE_PATH = APP_DIR / "data" / "example_case.json"


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

st.markdown(
    """
    <div class="hero">
        <h1>BioNexus AI</h1>
        <p>Plataforma academica para integracion multi-omica mediante inteligencia artificial.</p>
        <p><strong>Genomica | Transcriptomica | Proteomica | Metabolomica | Datos clinicos</strong></p>
    </div>
    <div class="warning">Uso educativo e investigativo. No constituye diagnostico medico.</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="guide-grid">
    """
    + guide_card(
        "Que vas a ingresar",
        "Datos simulados de una muestra o paciente: edad, sintomas, genes, proteinas, metabolitos y laboratorio.",
    )
    + guide_card(
        "Como escribirlos",
        "Separa cada dato con coma o salto de linea. Ejemplo: IL6, TNF, CRP.",
    )
    + guide_card(
        "Que entrega el sistema",
        "Panel recomendado, biomarcadores candidatos, rutas posiblemente alteradas, nivel de riesgo academico y reporte PDF.",
    )
    + """
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Formulario guiado de ingreso de datos</div>', unsafe_allow_html=True)

with st.form("case_form"):
    step_title(1, "Identificacion clinica simulada")
    st.markdown(
        '<div class="mini-note">Estos campos describen el contexto del caso. No escribas datos personales reales; usa informacion simulada para la actividad academica.</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([1, 1, 2])
    age = col_a.number_input("Edad simulada", min_value=0, max_value=120, value=int(source.get("age", 35)))
    sex = col_b.selectbox(
        "Sexo biologico reportado",
        ["Femenino", "Masculino", "Intersexual", "No informado"],
        index=["Femenino", "Masculino", "Intersexual", "No informado"].index(source.get("sex", "No informado"))
        if source.get("sex", "No informado") in ["Femenino", "Masculino", "Intersexual", "No informado"]
        else 3,
    )
    presumptive_diagnosis = col_c.text_input(
        "Diagnostico presuntivo o pregunta de investigacion",
        value=source.get("presumptive_diagnosis", ""),
        placeholder="Ejemplo: sindrome inflamatorio en estudio",
    )
    field_note("Ejemplo: proceso inflamatorio cronico en evaluacion, sospecha metabolica o muestra tumoral simulada.")

    symptoms = st.text_area(
        "Sintomas o hallazgos clinicos",
        value=join_items(source.get("symptoms", [])),
        placeholder="fatiga, fiebre, dolor articular",
    )
    field_note("Escribe sintomas separados por comas. Ejemplo: fatiga, fiebre, dolor articular.")

    step_title(2, "Resultados de laboratorio complementarios")
    lab_results = st.text_area(
        "Laboratorio clinico o experimental",
        value=join_items(source.get("lab_results", [])),
        placeholder="PCR elevada, VSG elevada, LDH elevada",
    )
    field_note("Ejemplo: PCR elevada, VSG elevada, LDH elevada. Estos datos ayudan a sugerir marcadores, pero no generan diagnostico.")

    preliminary_case = {
        "presumptive_diagnosis": presumptive_diagnosis,
        "symptoms": parse_items(symptoms),
        "lab_results": parse_items(lab_results),
    }
    marker_recommendations = recommend_marker_panel(preliminary_case)
    recommended_markers = marker_recommendations["recommended_markers"]

    step_title(3, "Panel sugerido por BioNexus AI")
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

    step_title(4, "Datos omicos simulados editables")
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
    "age": age,
    "sex": sex,
    "presumptive_diagnosis": presumptive_diagnosis,
    "symptoms": parse_items(symptoms),
    "genomic": parse_items(genomic),
    "transcriptomic": parse_items(transcriptomic),
    "proteomic": parse_items(proteomic),
    "metabolomic": parse_items(metabolomic),
    "lab_results": parse_items(lab_results),
}

if submitted or use_example:
    analysis = analyze_case(case)
    summary = analysis["summary"]

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

    tab_summary, tab_recommendations, tab_markers, tab_visuals, tab_report = st.tabs(
        ["Panorama del caso", "Panel recomendado", "Biomarcadores", "Visualizaciones", "Reporte descargable"]
    )

    with tab_summary:
        left, right = st.columns([1.1, .9])
        with left:
            st.markdown('<div class="small-title">Interpretacion general</div>', unsafe_allow_html=True)
            for item in analysis["interpretations"]:
                st.write(f"- {item}")
            st.markdown(
                '<div class="callout">Las interpretaciones se expresan como posibles asociaciones. Requieren validacion experimental, bioinformatica y revision profesional.</div>',
                unsafe_allow_html=True,
            )
        with right:
            st.markdown('<div class="small-title">Rutas posiblemente alteradas</div>', unsafe_allow_html=True)
            if pathway_df.empty:
                st.info("No se identificaron rutas suficientes con las reglas actuales.")
            else:
                st.dataframe(pathway_df, use_container_width=True, hide_index=True)

        st.markdown('<div class="small-title">Datos ingresados al prototipo</div>', unsafe_allow_html=True)
        input_df = pd.DataFrame(
            [
                {"Campo": "Edad simulada", "Valor": str(case["age"])},
                {"Campo": "Sexo biologico reportado", "Valor": case["sex"]},
                {"Campo": "Diagnostico presuntivo", "Valor": case["presumptive_diagnosis"] or "No informado"},
                {"Campo": "Sintomas o hallazgos", "Valor": ", ".join(case["symptoms"]) or "No informado"},
                {"Campo": "Laboratorio", "Valor": ", ".join(case["lab_results"]) or "No informado"},
            ]
        )
        st.dataframe(input_df, use_container_width=True, hide_index=True)

    with tab_recommendations:
        st.markdown('<div class="small-title">Marcadores sugeridos por BioNexus AI</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="callout">Este panel se genera con reglas academicas basadas en palabras clave del diagnostico presuntivo, sintomas y laboratorio. No equivale a una orden clinica ni a una guia diagnostica real.</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(recommendation_df, use_container_width=True, hide_index=True)

        profile_text = ", ".join(marker_recommendations["matched_profiles"])
        st.write(f"**Perfiles detectados:** {profile_text}")
        st.write(
            "La recomendacion busca orientar que marcadores podrian explorarse para discutir inflamacion, proliferacion, metabolismo, reparacion de ADN u otros procesos simulados."
        )

    with tab_markers:
        st.markdown('<div class="small-title">Tabla de biomarcadores candidatos</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="callout">Un biomarcador candidato no confirma enfermedad. En este prototipo indica una posible asociacion biologica para discusion academica.</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(candidates_df, use_container_width=True, hide_index=True)

        category_df = (
            candidates_df.groupby("Categoria", as_index=False)
            .size()
            .rename(columns={"size": "Numero de biomarcadores"})
            .sort_values("Numero de biomarcadores", ascending=False)
        )
        st.markdown('<div class="small-title">Distribucion por categoria biologica</div>', unsafe_allow_html=True)
        st.dataframe(category_df, use_container_width=True, hide_index=True)

    with tab_visuals:
        left, right = st.columns([.95, 1.05])
        with left:
            st.plotly_chart(bar_fig, use_container_width=True)
        with right:
            st.plotly_chart(
                build_network_figure(analysis["candidates"], analysis["altered_pathways"]),
                use_container_width=True,
            )

    with tab_report:
        st.markdown('<div class="small-title">Reporte final interpretativo</div>', unsafe_allow_html=True)
        st.write(
            f"El caso presenta una **{summary['molecular_class']}** con riesgo academico simulado "
            f"**{summary['risk']}** y confianza **{summary['confidence']}**."
        )
        st.write("Este resultado sugiere posibles asociaciones y biomarcadores candidatos que requieren validacion.")
        st.markdown("**Recomendaciones de analisis complementarios**")
        for recommendation in analysis["recommendations"]:
            st.write(f"- {recommendation}")
        st.markdown("**Limitaciones**")
        for limitation in analysis["limitations"]:
            st.write(f"- {limitation}")
        st.warning(
            "Advertencia etica y academica: no reemplaza al medico, bacteriologo, bioinformatico ni investigador."
        )

        pdf_bytes = build_pdf(case, analysis)
        st.download_button(
            "Descargar reporte PDF",
            data=pdf_bytes,
            file_name="reporte_bionexus_ai.pdf",
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
