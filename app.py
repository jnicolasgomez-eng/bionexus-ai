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
MODULE_PASSWORDS = {
    "ingreso": "ingreso123",
    "seguimiento": "seguimiento123",
    "resumen": "resumen123",
    "laboratorio": "laboratorio123",
    "seguridad": "seguridad123",
}
HOSPITAL_AREAS = [
    "Urgencias",
    "Hospitalizacion",
    "Consulta externa",
    "UCI",
    "Pediatria",
    "Ginecologia/obstetricia",
    "Medicina interna",
    "Cirugia",
    "Oncologia",
    "Infectologia",
    "Salud mental",
    "Laboratorio clinico",
    "Otro",
]
REFERENCE_CATALOG_VERSION = "BioNexus Reference Catalog v0.1 - prototipo validable"
REFERENCE_CATALOG_SOURCE = "Catálogo curado interno del prototipo; validar contra manual del laboratorio, método, equipo, edad, sexo y población."
REFERENCE_RANGES = {
    "Hemoglobina": {"loinc": "718-7", "unit": "g/dL", "low": 12.0, "high": 16.0, "specimen": "Sangre total"},
    "Leucocitos": {"loinc": "6690-2", "unit": "10^3/uL", "low": 4.0, "high": 11.0, "specimen": "Sangre total"},
    "Neutrofilos absolutos": {"loinc": "751-8", "unit": "10^3/uL", "low": 1.5, "high": 7.5, "specimen": "Sangre total"},
    "Plaquetas": {"loinc": "777-3", "unit": "10^3/uL", "low": 150.0, "high": 450.0, "specimen": "Sangre total"},
    "PCR cuantitativa": {"loinc": "1988-5", "unit": "mg/L", "low": 0.0, "high": 5.0, "specimen": "Suero/plasma"},
    "VSG": {"loinc": "30341-2", "unit": "mm/h", "low": 0.0, "high": 20.0, "specimen": "Sangre total"},
    "Procalcitonina": {"loinc": "33959-8", "unit": "ng/mL", "low": 0.0, "high": 0.5, "specimen": "Suero/plasma"},
    "Glucosa": {"loinc": "2345-7", "unit": "mg/dL", "low": 70.0, "high": 100.0, "specimen": "Suero/plasma"},
    "Lactato": {"loinc": "2524-7", "unit": "mmol/L", "low": 0.5, "high": 2.2, "specimen": "Sangre/plasma"},
    "Creatinina": {"loinc": "2160-0", "unit": "mg/dL", "low": 0.6, "high": 1.3, "specimen": "Suero/plasma"},
    "Urea": {"loinc": "3094-0", "unit": "mg/dL", "low": 15.0, "high": 40.0, "specimen": "Suero/plasma"},
    "Sodio": {"loinc": "2951-2", "unit": "mmol/L", "low": 135.0, "high": 145.0, "specimen": "Suero/plasma"},
    "Potasio": {"loinc": "2823-3", "unit": "mmol/L", "low": 3.5, "high": 5.1, "specimen": "Suero/plasma"},
    "AST": {"loinc": "1920-8", "unit": "U/L", "low": 0.0, "high": 40.0, "specimen": "Suero/plasma"},
    "ALT": {"loinc": "1742-6", "unit": "U/L", "low": 0.0, "high": 41.0, "specimen": "Suero/plasma"},
    "Bilirrubina total": {"loinc": "1975-2", "unit": "mg/dL", "low": 0.2, "high": 1.2, "specimen": "Suero/plasma"},
    "Ferritina": {"loinc": "2276-4", "unit": "ng/mL", "low": 30.0, "high": 300.0, "specimen": "Suero"},
    "CK total": {"loinc": "2157-6", "unit": "U/L", "low": 30.0, "high": 200.0, "specimen": "Suero"},
    "LDH": {"loinc": "14804-9", "unit": "U/L", "low": 140.0, "high": 280.0, "specimen": "Suero"},
    "TSH": {"loinc": "3016-3", "unit": "uIU/mL", "low": 0.4, "high": 4.0, "specimen": "Suero"},
}


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
                "Area": item.get("hospital_area", "No informado"),
                "Estado": item.get("workflow_status", "Ingreso inicial"),
                "Resultado": item.get("result_status", "Pendiente"),
                "Creado": created_at,
                "Actualizado": updated_at,
            }
        )
    return pd.DataFrame(data)


def require_module_password(module_key: str, title: str) -> bool:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    expected = MODULE_PASSWORDS[module_key]
    typed = st.text_input(f"Contraseña para {title}", type="password", key=f"pass_{module_key}")
    if typed == expected:
        st.success("Acceso autorizado.")
        return True
    if typed:
        st.error("Contraseña incorrecta.")
    else:
        st.info("Ingresa la contraseña del módulo para continuar.")
    return False


def evaluate_reference_flag(test_name: str, value: float | None) -> str:
    if value is None or test_name not in REFERENCE_RANGES:
        return ""
    reference = REFERENCE_RANGES[test_name]
    if value < reference["low"]:
        return "L"
    if value > reference["high"]:
        return "H"
    return ""


def reference_range_text(test_name: str) -> str:
    reference = REFERENCE_RANGES.get(test_name)
    if not reference:
        return "Rango no configurado"
    return f'{reference["low"]} - {reference["high"]} {reference["unit"]}'


def build_structured_result(test_name: str, value: float | None) -> dict:
    reference = REFERENCE_RANGES.get(test_name, {})
    return {
        "Prueba": test_name,
        "LOINC": reference.get("loinc", "N/D"),
        "Valor": "" if value is None else value,
        "Unidades": reference.get("unit", ""),
        "Rango de referencia": reference_range_text(test_name),
        "Bandera": evaluate_reference_flag(test_name, value),
        "Muestra": reference.get("specimen", "N/D"),
        "Catalogo": REFERENCE_CATALOG_VERSION,
    }


def structured_results_summary(results: list[dict]) -> list[str]:
    items = []
    for row in results:
        flag = f" {row['Bandera']}" if row.get("Bandera") else ""
        items.append(f"{row['Prueba']} {row['Valor']} {row['Unidades']}{flag}".strip())
    return items


def reference_catalog_dataframe() -> pd.DataFrame:
    rows = []
    for test_name, reference in REFERENCE_RANGES.items():
        rows.append(
            {
                "Prueba": test_name,
                "LOINC": reference["loinc"],
                "Muestra": reference["specimen"],
                "Unidad": reference["unit"],
                "Bajo": reference["low"],
                "Alto": reference["high"],
                "Version": REFERENCE_CATALOG_VERSION,
            }
        )
    return pd.DataFrame(rows)


def consent_form_text() -> str:
    return f"""
BIO NEXUS IA - CONSENTIMIENTO INFORMADO PARA APOYO INTERPRETATIVO DE LABORATORIO

Paciente: ______________________________________
ID paciente/muestra: ___________________________
Fecha: ________________________________________

Declaro que he sido informado(a) de que BioNexus IA es una herramienta de apoyo
interpretativo para laboratorio clinico, seguimiento de resultados y priorizacion
de pruebas. La liberacion diagnostica debe realizarla el profesional responsable.

Autorizo el uso de mis datos clinicos y resultados de laboratorio para analisis
interpretativo dentro del flujo institucional, con manejo confidencial y trazable.

Entiendo que:
- Los resultados deben correlacionarse con criterio clinico y profesional.
- Los rangos de referencia dependen del laboratorio, metodo, equipo, edad, sexo y poblacion.
- El sistema no reemplaza al medico ni al bacteriologo/laboratorista responsable.
- Para antimicrobianos se requiere cultivo/antibiograma, guias institucionales y validacion medica.

Firma del paciente/acudiente: ______________________________
Documento: ________________________________________________
Firma del profesional que informa: _________________________

Catalogo usado: {REFERENCE_CATALOG_VERSION}
Fuente del catalogo: {REFERENCE_CATALOG_SOURCE}
"""


def standards_traceability_text() -> str:
    return f"""
BIO NEXUS IA - TRAZABILIDAD E INTEROPERABILIDAD

Catalogo de referencias:
- Version: {REFERENCE_CATALOG_VERSION}
- Fuente: {REFERENCE_CATALOG_SOURCE}
- Regla de bandera: L si el valor esta por debajo del limite bajo; H si esta por encima del limite alto; vacio si esta dentro del rango.

Estandares previstos:
- HL7/FHIR: Observation y DiagnosticReport para resultados y reportes.
- LOINC: codificacion de pruebas de laboratorio.
- SNOMED CT: hallazgos clinicos, sintomas, procedimientos y conceptos clinicos.
- CIE-10/ICD-10: codificacion diagnostica institucional.
- Unidades estandarizadas: registro obligatorio de unidad por prueba.
- Consentimiento informado: requerido para tratamiento de datos y apoyo interpretativo.

Controles necesarios para uso real:
- Login institucional y roles.
- Cifrado de datos.
- Auditoria de ingreso, consulta, edicion, descarga y liberacion.
- Estados del informe: borrador, revisado, liberado, corregido y anulado.
- Fuentes curadas, versionadas y trazables.
"""


def parse_numeric_series(raw: str) -> list[float]:
    values = []
    for token in raw.replace(";", ",").replace("\n", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def linear_regression(x_values: list[float], y_values: list[float]) -> dict:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0}
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    ss_x = sum((x - x_mean) ** 2 for x in x_values)
    if ss_x == 0:
        return {"slope": 0.0, "intercept": y_mean, "r2": 0.0}
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / ss_x
    intercept = y_mean - slope * x_mean
    predicted = [slope * x + intercept for x in x_values]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(y_values, predicted))
    ss_tot = sum((y - y_mean) ** 2 for y in y_values)
    r2 = 1 - (ss_res / ss_tot) if ss_tot else 1.0
    return {"slope": slope, "intercept": intercept, "r2": r2}


def build_calibration_figure(x_values: list[float], y_values: list[float], model: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_values, y=y_values, mode="markers", name="Calibradores", marker=dict(size=10, color="#0891b2")))
    if x_values:
        x_line = [min(x_values), max(x_values)]
        y_line = [model["slope"] * x + model["intercept"] for x in x_line]
        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", name="Ajuste lineal", line=dict(color="#0f766e", width=3)))
    fig.update_layout(
        title="Curva de calibracion",
        xaxis_title="Concentracion del calibrador",
        yaxis_title="Senal / absorbancia / respuesta",
        height=420,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def build_westgard_findings(values: list[float], target_mean: float, sd: float) -> list[dict]:
    if not values or sd <= 0:
        return [{"Regla": "Sin datos", "Resultado": "No evaluable", "Accion": "Ingresar valores de control y DE valida."}]
    z_scores = [(value - target_mean) / sd for value in values]
    findings = []

    if any(abs(z) > 2 for z in z_scores):
        findings.append({"Regla": "1-2s", "Resultado": "Alerta", "Accion": "Revisar tendencia, reactivo, calibracion y siguiente control."})
    if any(abs(z) > 3 for z in z_scores):
        findings.append({"Regla": "1-3s", "Resultado": "Rechazar corrida", "Accion": "No liberar resultados; investigar error aleatorio o sistematico."})
    for first, second in zip(z_scores, z_scores[1:]):
        if first > 2 and second > 2:
            findings.append({"Regla": "2-2s", "Resultado": "Rechazar corrida", "Accion": "Sospecha de error sistematico por dos controles consecutivos altos."})
            break
        if first < -2 and second < -2:
            findings.append({"Regla": "2-2s", "Resultado": "Rechazar corrida", "Accion": "Sospecha de error sistematico por dos controles consecutivos bajos."})
            break
        if abs(first - second) > 4:
            findings.append({"Regla": "R-4s", "Resultado": "Rechazar corrida", "Accion": "Sospecha de error aleatorio; repetir control y revisar procedimiento."})
            break
    for start in range(0, max(len(z_scores) - 3, 0)):
        window = z_scores[start : start + 4]
        if all(z > 1 for z in window) or all(z < -1 for z in window):
            findings.append({"Regla": "4-1s", "Resultado": "Alerta/Rechazo segun politica", "Accion": "Investigar desplazamiento sistematico."})
            break
    for start in range(0, max(len(z_scores) - 9, 0)):
        window = z_scores[start : start + 10]
        if all(z > 0 for z in window) or all(z < 0 for z in window):
            findings.append({"Regla": "10x", "Resultado": "Alerta/Rechazo segun politica", "Accion": "Investigar sesgo sostenido."})
            break

    return findings or [{"Regla": "Westgard multirregla", "Resultado": "Aceptable", "Accion": "Sin violaciones detectadas en este prototipo."}]


def build_levey_jennings_figure(values: list[float], target_mean: float, sd: float) -> go.Figure:
    runs = list(range(1, len(values) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=runs, y=values, mode="lines+markers", name="Control", line=dict(color="#0891b2", width=3)))
    line_specs = [
        (target_mean, "Media", "#0f766e", "solid"),
        (target_mean + sd, "+1 DE", "#22c55e", "dot"),
        (target_mean - sd, "-1 DE", "#22c55e", "dot"),
        (target_mean + 2 * sd, "+2 DE", "#f59e0b", "dash"),
        (target_mean - 2 * sd, "-2 DE", "#f59e0b", "dash"),
        (target_mean + 3 * sd, "+3 DE", "#ef4444", "dash"),
        (target_mean - 3 * sd, "-3 DE", "#ef4444", "dash"),
    ]
    for y_value, name, color, dash in line_specs:
        fig.add_hline(y=y_value, line_color=color, line_dash=dash, annotation_text=name)
    fig.update_layout(
        title="Grafica Levey-Jennings / Westgard",
        xaxis_title="Corrida de control",
        yaxis_title="Valor del control",
        height=450,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def qc_text_report(data: dict) -> str:
    return "\n".join(
        [
            "BIO NEXUS IA - REPORTE TECNICO DE CONTROL DE CALIDAD",
            f"Prueba: {data.get('test_name')}",
            f"Metodo/equipo: {data.get('method')} / {data.get('instrument')}",
            f"Lote reactivo: {data.get('reagent_lot')}",
            f"Lote calibrador: {data.get('calibrator_lot')}",
            f"Lote control: {data.get('control_lot')}",
            f"R2 calibracion: {data.get('r2')}",
            f"CV precision: {data.get('cv')}",
            f"Decision QC: {data.get('decision')}",
            "",
            "Este reporte es un apoyo documental. La aceptacion/rechazo debe seguir el procedimiento operativo estandar del laboratorio.",
        ]
    )


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
    hospital_area = str(case.get("hospital_area", "")).lower()
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

    if "urgencias" in hospital_area or "uci" in hospital_area:
        add("Hemograma con diferencial", "Sangre total", "Hematologia automatizada", "Tamizaje inicial de anemia, infeccion, inflamacion o compromiso sistemico.")
        add("Gases y lactato", "Sangre arterial o venosa", "Gasometria", "Apoya decisiones de prioridad por perfusion, oxigenacion y estado acido-base.")
        add("Electrolitos y funcion renal", "Suero o plasma", "Quimica clinica", "Permite vigilar alteraciones hidroelectroliticas y compromiso renal.")
    if "pediatria" in hospital_area:
        add("Hemograma con diferencial", "Sangre total", "Hematologia automatizada", "Permite correlacionar fiebre, anemia, infeccion o inflamacion en edad pediatrica.")
        add("PCR cuantitativa", "Suero o plasma", "Inmunoensayo/ELISA", "Apoya seguimiento de respuesta inflamatoria segun contexto pediatrico.")
    if "ginecologia" in hospital_area or "obstetricia" in hospital_area:
        add("Hemograma", "Sangre total", "Hematologia automatizada", "Evalua anemia, infeccion o sangrado segun contexto gineco-obstetrico.")
        add("Uroanalisis y urocultivo si aplica", "Orina", "Quimica/microscopia/cultivo", "Apoya evaluacion de sintomas urinarios o infeccion asociada.")
    if "cirugia" in hospital_area:
        add("Hemograma", "Sangre total", "Hematologia automatizada", "Evalua anemia, leucocitosis o respuesta inflamatoria perioperatoria.")
        add("TP, TPT e INR si aplica", "Plasma citratado", "Coagulometria", "Apoya valoracion hemostatica antes o despues de procedimiento.")
    if "oncologia" in hospital_area:
        add("Hemograma con diferencial", "Sangre total", "Hematologia automatizada", "Vigila citopenias, infeccion o seguimiento terapeutico.")
        add("LDH", "Suero", "Quimica clinica", "Marcador inespecifico de dano tisular o actividad celular; requiere correlacion.")
    if "infectologia" in hospital_area:
        add("Cultivo segun foco", "Muestra del foco sospechoso", "Cultivo microbiologico", "Busca agente etiologico para interpretacion y posible antibiograma.")
        add("Antibiograma si hay aislamiento", "Aislado bacteriano", "CLSI/EUCAST institucional", "Orienta sensibilidad/resistencia con validacion profesional.")

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
        "hospital_area": intake.get("hospital_area", "No informado"),
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
            Area hospitalaria: **{case.get('hospital_area', 'No informado')}**  
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

    if case.get("structured_lab_results"):
        st.markdown('<div class="section-title">Resultados cuantitativos interpretados</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(case["structured_lab_results"]), width="stretch", hide_index=True)

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
                <div class="omic-icon">HOS</div>
                <strong>Apoyo hospitalario</strong>
                <span>Funciona para urgencias, UCI, hospitalizacion, consulta externa, pediatria, cirugia, oncologia e infectologia.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">LAB</div>
                <strong>Laboratorio clinico</strong>
                <span>Sugiere examenes puntuales, tipo de muestra, metodo y justificacion segun sintomas y area hospitalaria.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">MIC</div>
                <strong>Microbiologia</strong>
                <span>Prioriza cultivo, antibiograma y marcadores infecciosos cuando el caso lo requiere.</span>
            </div>
            <div class="omic-card">
                <div class="omic-icon">MOL</div>
                <strong>Molecular opcional</strong>
                <span>Permite agregar genomica, transcriptomica, proteomica o metabolomica solo si el paciente tiene esos datos.</span>
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
        hospital_area = st.selectbox("Area hospitalaria", HOSPITAL_AREAS)
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
            "hospital_area": hospital_area,
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
            Area hospitalaria: **{record.get('hospital_area', 'No informado')}**  
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
        suggested_tests = [row.get("Examen sugerido") for row in record.get("recommended_exams", []) if row.get("Examen sugerido")]
        test_options = list(dict.fromkeys(suggested_tests + list(REFERENCE_RANGES.keys())))
        performed_tests = st.multiselect(
            "Pruebas realizadas",
            test_options,
            default=suggested_tests[: min(len(suggested_tests), 4)],
            help="Selecciona las pruebas enviadas o realizadas. Si estan en el catalogo, la app completa unidad, rango y bandera H/L.",
        )
        structured_values = {}
        if performed_tests:
            st.markdown('<div class="small-title">Valores numericos</div>', unsafe_allow_html=True)
            for idx, test_name in enumerate(performed_tests):
                reference = REFERENCE_RANGES.get(test_name)
                cols = st.columns([1.4, 1, 1.1, 0.8])
                cols[0].write(f"**{test_name}**")
                if reference:
                    value = cols[1].number_input("Valor", key=f"lab_value_{idx}_{test_name}", value=None, step=0.1, format="%.3f")
                    cols[2].write(f'{reference["unit"]} | Ref: {reference["low"]} - {reference["high"]}')
                    cols[3].write("Pendiente" if value is None else (evaluate_reference_flag(test_name, value) or "Normal"))
                    structured_values[test_name] = value
                else:
                    cols[1].write("Sin rango")
                    cols[2].write("Usar resultado textual")
                    cols[3].write("")
        lab_results = st.text_area("Resultados textuales adicionales", placeholder="Ejemplo: cultivo negativo, observaciones del equipo, comentario morfologico")
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
        with st.expander("Datos moleculares u omicos opcionales"):
            st.caption("Usa esta seccion solo si el caso tiene resultados genomicos, transcriptomicos, proteomicos o metabolomicos.")
            genomic = st.text_area("Genomica opcional", value=", ".join(record.get("genomic", [])))
            transcriptomic = st.text_area("Transcriptomica opcional", value=", ".join(record.get("transcriptomic", [])))
            proteomic = st.text_area("Proteomica opcional", value=", ".join(record.get("proteomic", [])))
            metabolomic = st.text_area("Metabolomica opcional", value=", ".join(record.get("metabolomic", [])))
        submitted = st.form_submit_button("Actualizar informacion y continuar interpretacion", type="primary")

    if submitted:
        structured_lab_results = [
            build_structured_result(test_name, structured_values.get(test_name))
            for test_name in performed_tests
            if test_name in REFERENCE_RANGES and structured_values.get(test_name) is not None
        ]
        intake = {**record}
        intake.update(
            {
                "workflow_status": workflow_status,
                "sample_type": sample_type,
                "sample_quality": sample_quality,
                "collection_date": str(collection_date),
                "reception_date": str(reception_date),
                "method_used": method_used,
                "lab_results": ", ".join(structured_results_summary(structured_lab_results) + parse_items(lab_results)),
                "structured_lab_results": structured_lab_results,
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
        st.success(f"Informacion actualizada para el ID {patient_id.strip()} a las {intake['report_datetime']}.")
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

    st.markdown('<div class="section-title">Analitica visual de pacientes</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    status_counts = saved_df["Estado"].value_counts().reset_index()
    status_counts.columns = ["Estado", "Pacientes"]
    area_counts = saved_df["Area"].fillna("No informado").value_counts().reset_index()
    area_counts.columns = ["Area", "Pacientes"]
    result_counts = saved_df["Resultado"].fillna("Pendiente").value_counts().reset_index()
    result_counts.columns = ["Resultado", "Pacientes"]

    with g1:
        fig_status = go.Figure(
            data=[
                go.Bar(
                    x=status_counts["Estado"],
                    y=status_counts["Pacientes"],
                    marker_color="#0891b2",
                )
            ]
        )
        fig_status.update_layout(
            title="Pacientes por estado del caso",
            height=360,
            xaxis_title="Estado",
            yaxis_title="Pacientes",
            margin=dict(l=20, r=20, t=55, b=90),
        )
        st.plotly_chart(fig_status, width="stretch")
    with g2:
        fig_result = go.Figure(
            data=[
                go.Pie(
                    labels=result_counts["Resultado"],
                    values=result_counts["Pacientes"],
                    hole=0.42,
                    marker_colors=["#12c7bd", "#0f766e", "#f59e0b", "#ef4444"],
                )
            ]
        )
        fig_result.update_layout(title="Distribucion por resultado", height=360, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(fig_result, width="stretch")

    fig_area = go.Figure(
        data=[
            go.Bar(
                x=area_counts["Pacientes"],
                y=area_counts["Area"],
                orientation="h",
                marker_color="#0f766e",
            )
        ]
    )
    fig_area.update_layout(
        title="Pacientes por area hospitalaria",
        height=380,
        xaxis_title="Pacientes",
        yaxis_title="Area",
        margin=dict(l=20, r=20, t=55, b=30),
    )
    st.plotly_chart(fig_area, width="stretch")

    st.markdown('<div class="small-title">Pacientes que faltan por traer resultados de laboratorio</div>', unsafe_allow_html=True)
    st.dataframe(pending if not pending.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Pacientes en seguimiento o con resultados cargados</div>', unsafe_allow_html=True)
    st.dataframe(loaded if not loaded.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)

    st.markdown('<div class="small-title">Casos resueltos o cerrados</div>', unsafe_allow_html=True)
    st.dataframe(resolved if not resolved.empty else pd.DataFrame(columns=saved_df.columns), width="stretch", hide_index=True)


def laboratory_qc_view() -> None:
    st.markdown('<div class="section-title">Laboratorio y control de calidad</div>', unsafe_allow_html=True)
    st.info(
        "Modulo tecnico para documentar pruebas programadas, calibracion, control interno, reglas de Westgard, precision y decision de corrida. "
        "Debe validarse con el procedimiento operativo estandar del laboratorio."
    )

    st.markdown('<div class="small-title">Datos de corrida analitica</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    test_name = c1.selectbox("Prueba", list(REFERENCE_RANGES.keys()))
    method = c2.selectbox("Metodo", ["Quimica clinica", "Inmunoensayo", "Hematologia", "Coagulometria", "PCR/qPCR", "ELISA", "Otro"])
    instrument = c3.text_input("Equipo / analizador", placeholder="Ejemplo: Analizador 01")
    c4, c5, c6 = st.columns(3)
    reagent_lot = c4.text_input("Lote de reactivo")
    calibrator_lot = c5.text_input("Lote de calibrador")
    control_lot = c6.text_input("Lote de control")
    planned_tests = st.multiselect("Pruebas que se van a realizar en esta corrida", list(REFERENCE_RANGES.keys()), default=[test_name])

    checklist_items = {
        "Reactivos vigentes y sin vencimiento": st.checkbox("Reactivos vigentes y sin vencimiento"),
        "Calibrador vigente y reconstituido correctamente": st.checkbox("Calibrador vigente y reconstituido correctamente"),
        "Controles internos procesados": st.checkbox("Controles internos procesados"),
        "Temperatura/condiciones ambientales verificadas": st.checkbox("Temperatura/condiciones ambientales verificadas"),
        "Mantenimiento o verificacion del equipo documentado": st.checkbox("Mantenimiento o verificacion del equipo documentado"),
        "Criterios de aceptacion definidos antes de liberar": st.checkbox("Criterios de aceptacion definidos antes de liberar"),
    }
    checklist_ok = all(checklist_items.values())

    st.markdown('<div class="section-title">Curva de calibracion</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    concentrations_raw = col_a.text_area("Concentraciones de calibradores", value="0, 25, 50, 100, 200")
    signal_raw = col_b.text_area("Senales / absorbancias", value="0.01, 0.22, 0.49, 1.01, 2.03")
    concentrations = parse_numeric_series(concentrations_raw)
    signals = parse_numeric_series(signal_raw)
    calibration = linear_regression(concentrations, signals)
    st.plotly_chart(build_calibration_figure(concentrations, signals, calibration), width="stretch")
    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Pendiente", f"{calibration['slope']:.4f}")
    with k2:
        metric_card("Intercepto", f"{calibration['intercept']:.4f}")
    with k3:
        metric_card("R2", f"{calibration['r2']:.4f}")
    r2_threshold = st.number_input("Criterio minimo R2", min_value=0.0, max_value=1.0, value=0.990, step=0.001, format="%.3f")
    calibration_ok = calibration["r2"] >= r2_threshold
    st.success("Calibracion aceptable segun R2 configurado.") if calibration_ok else st.error("Calibracion no aceptable: revisar calibradores, pipeteo, reactivos o equipo.")

    st.markdown('<div class="section-title">Control interno: Levey-Jennings y Westgard</div>', unsafe_allow_html=True)
    q1, q2 = st.columns(2)
    target_mean = q1.number_input("Media asignada del control", value=100.0, step=0.1)
    target_sd = q2.number_input("Desviacion estandar asignada", min_value=0.001, value=5.0, step=0.1)
    qc_values_raw = st.text_area("Valores consecutivos del control", value="98, 101, 104, 107, 111, 108, 106, 103, 102, 101")
    qc_values = parse_numeric_series(qc_values_raw)
    st.plotly_chart(build_levey_jennings_figure(qc_values, target_mean, target_sd), width="stretch")
    westgard_df = pd.DataFrame(build_westgard_findings(qc_values, target_mean, target_sd))
    st.dataframe(westgard_df, width="stretch", hide_index=True)
    westgard_ok = not westgard_df["Resultado"].astype(str).str.contains("Rechazar", case=False, na=False).any()

    st.markdown('<div class="section-title">Precision, CV y error total</div>', unsafe_allow_html=True)
    precision_raw = st.text_area("Replicados de precision", value="99.1, 100.3, 98.8, 101.0, 100.1")
    precision_values = parse_numeric_series(precision_raw)
    if len(precision_values) >= 2:
        precision_mean = sum(precision_values) / len(precision_values)
        variance = sum((value - precision_mean) ** 2 for value in precision_values) / (len(precision_values) - 1)
        precision_sd = variance ** 0.5
        cv = (precision_sd / precision_mean * 100) if precision_mean else 0.0
    else:
        precision_mean = 0.0
        precision_sd = 0.0
        cv = 0.0
    p1, p2, p3 = st.columns(3)
    with p1:
        metric_card("Media precision", f"{precision_mean:.3f}")
    with p2:
        metric_card("DE precision", f"{precision_sd:.3f}")
    with p3:
        metric_card("CV %", f"{cv:.2f}")
    max_cv = st.number_input("CV maximo permitido (%)", min_value=0.0, value=5.0, step=0.1)
    bias_percent = st.number_input("Sesgo estimado (%)", value=0.0, step=0.1)
    total_error = abs(bias_percent) + 1.65 * cv
    allowable_total_error = st.number_input("Error total permitido (%)", min_value=0.0, value=10.0, step=0.1)
    precision_ok = cv <= max_cv
    total_error_ok = total_error <= allowable_total_error
    st.write(f"Error total estimado: **{total_error:.2f}%**")

    mandatory_df = pd.DataFrame(
        [
            {"Control": "Checklist preanalitico/analitico", "Estado": "OK" if checklist_ok else "Pendiente"},
            {"Control": "Curva de calibracion", "Estado": "OK" if calibration_ok else "No aceptable"},
            {"Control": "Westgard / Levey-Jennings", "Estado": "OK" if westgard_ok else "Rechazar corrida"},
            {"Control": "Precision / CV", "Estado": "OK" if precision_ok else "No aceptable"},
            {"Control": "Error total", "Estado": "OK" if total_error_ok else "No aceptable"},
        ]
    )
    st.markdown('<div class="section-title">Decision tecnica de corrida</div>', unsafe_allow_html=True)
    st.dataframe(mandatory_df, width="stretch", hide_index=True)
    decision_ok = checklist_ok and calibration_ok and westgard_ok and precision_ok and total_error_ok
    if decision_ok:
        st.success("Corrida aceptable segun criterios configurados del prototipo.")
        decision = "Aceptada"
    else:
        st.error("Corrida no aceptable o pendiente. No liberar resultados hasta revisar acciones correctivas.")
        decision = "No aceptada / pendiente"

    qc_payload = {
        "test_name": test_name,
        "method": method,
        "instrument": instrument,
        "reagent_lot": reagent_lot,
        "calibrator_lot": calibrator_lot,
        "control_lot": control_lot,
        "r2": f"{calibration['r2']:.4f}",
        "cv": f"{cv:.2f}%",
        "decision": decision,
        "planned_tests": ", ".join(planned_tests),
    }
    _ = st.download_button(
        "Descargar reporte tecnico de control de calidad",
        data=qc_text_report(qc_payload).encode("utf-8"),
        file_name="control_calidad_bionexus.txt",
        mime="text/plain",
        type="primary",
    )
    return None


def safety_view() -> None:
    st.markdown('<div class="section-title">Seguridad, trazabilidad y siguiente fase</div>', unsafe_allow_html=True)
    st.write("- Esta version usa contrasenas de prototipo por modulo. Para uso real deben reemplazarse por login institucional.")
    st.write("- Para uso real se necesita roles por usuario: bacteriologo/laboratorista, medico, administrador y auditor.")
    st.write("- La base de datos debe ser segura, cifrada, con copias de respaldo y control de acceso.")
    st.write("- Debe existir auditoria: quien ingreso, consulto, edito, descargo o libero cada informe.")
    st.write("- El estado del informe debe manejar borrador, revisado, liberado, corregido y anulado.")
    st.write("- La IA debe usar fuentes curadas, versionadas y trazables, no internet abierto sin filtro.")
    st.write("- Para antimicrobianos: no formula antibiotico ni dosis sin cultivo/antibiograma, guias institucionales y validacion medica.")
    st.write("- Para integracion hospitalaria futura: HL7/FHIR, LOINC, SNOMED CT, CIE-10, unidades estandarizadas y consentimiento informado.")

    st.markdown('<div class="section-title">Catalogo curado de valores de referencia</div>', unsafe_allow_html=True)
    st.warning(
        "Este catalogo es una base prototipo versionada. En uso real debe reemplazarse o validarse con el manual oficial del laboratorio, "
        "metodo, equipo, edad, sexo y poblacion atendida."
    )
    st.caption(f"Version: {REFERENCE_CATALOG_VERSION}")
    st.caption(f"Fuente: {REFERENCE_CATALOG_SOURCE}")
    st.dataframe(reference_catalog_dataframe(), width="stretch", hide_index=True)

    st.markdown('<div class="section-title">Estandares e interoperabilidad</div>', unsafe_allow_html=True)
    standards_df = pd.DataFrame(
        [
            {"Estandar": "HL7/FHIR", "Uso en BioNexus IA": "Observation y DiagnosticReport para resultados e informes."},
            {"Estandar": "LOINC", "Uso en BioNexus IA": "Codigos de pruebas de laboratorio."},
            {"Estandar": "SNOMED CT", "Uso en BioNexus IA": "Hallazgos, sintomas, procedimientos y conceptos clinicos."},
            {"Estandar": "CIE-10/ICD-10", "Uso en BioNexus IA": "Codificacion diagnostica institucional."},
            {"Estandar": "Unidades estandarizadas", "Uso en BioNexus IA": "Cada resultado cuantitativo debe tener unidad."},
            {"Estandar": "Consentimiento informado", "Uso en BioNexus IA": "Formato imprimible para firma del paciente/acudiente."},
        ]
    )
    st.dataframe(standards_df, width="stretch", hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Descargar consentimiento informado",
            data=consent_form_text().encode("utf-8"),
            file_name="consentimiento_informado_bionexus.txt",
            mime="text/plain",
            type="primary",
        )
    with c2:
        st.download_button(
            "Descargar trazabilidad y estandares",
            data=standards_traceability_text().encode("utf-8"),
            file_name="trazabilidad_estandares_bionexus.txt",
            mime="text/plain",
        )

    with st.expander("Vista para imprimir: consentimiento informado"):
        st.text(consent_form_text())

    with st.expander("Vista para imprimir: trazabilidad e interoperabilidad"):
        st.text(standards_traceability_text())


init_db()
render_styles()
hero()

intake_tab, follow_tab, dashboard_tab, lab_tab, safety_tab = st.tabs(
    ["Ingreso del paciente", "Seguimiento por ID", "Resumen de pacientes", "Laboratorio y QC", "Validacion y seguridad"]
)
with intake_tab:
    if require_module_password("ingreso", "Ingreso del paciente"):
        _ = chat_intake_view()
with follow_tab:
    if require_module_password("seguimiento", "Seguimiento por ID"):
        _ = follow_up_view()
with dashboard_tab:
    if require_module_password("resumen", "Resumen de pacientes"):
        _ = dashboard_view()
with lab_tab:
    if require_module_password("laboratorio", "Laboratorio y control de calidad"):
        _ = laboratory_qc_view()
with safety_tab:
    if require_module_password("seguridad", "Validacion y seguridad"):
        _ = safety_view()
