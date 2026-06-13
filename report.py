"""Generador de reportes PDF para BioNexus AI."""

from __future__ import annotations

from io import BytesIO
from typing import Dict, Iterable, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _paragraph_list(items: Iterable[str], style: ParagraphStyle) -> List[Paragraph]:
    return [Paragraph(f"- {item}", style) for item in items]


def build_pdf(case: Dict[str, object], analysis: Dict[str, object]) -> bytes:
    """Construye un PDF descargable en memoria."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "BioNexusTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#0F766E"),
        fontSize=22,
        leading=26,
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "BioNexusHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#155E75"),
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
    )
    body = ParagraphStyle("BioNexusBody", parent=styles["BodyText"], fontSize=9.5, leading=12)
    small = ParagraphStyle("BioNexusSmall", parent=styles["BodyText"], fontSize=8, leading=10)

    summary = analysis["summary"]
    story: List[object] = [
        Paragraph("BioNexus AI - Informe academico multi-omico", title),
        Paragraph("Uso educativo e investigativo. No constituye diagnostico medico ni terapeutico.", body),
        Spacer(1, 8),
        Paragraph("Datos administrativos", heading),
    ]

    admin_rows = [
        ["Campo", "Contenido"],
        ["Nombre del paciente", str(case.get("patient_name", "N/D")) or "N/D"],
        ["Edad del paciente", f"{case.get('age', 'N/D')} anos"],
        ["Genero del paciente", str(case.get("patient_gender", "N/D")) or "N/D"],
        ["ID", str(case.get("patient_id", "N/D")) or "N/D"],
        ["Fecha y hora de expedicion", str(case.get("report_datetime", "N/D")) or "N/D"],
        ["Laboratorio", str(case.get("lab_name", "BioNexus AI")) or "BioNexus AI"],
        ["Bacteriologo a cargo", str(case.get("bacteriologist_name", "N/D")) or "N/D"],
    ]
    story.append(_styled_table(admin_rows))

    story.append(Paragraph("Datos de muestra y fase preanalitica", heading))
    sample_rows = [
        ["Campo", "Contenido"],
        ["Tipo de muestra", str(case.get("sample_type", "N/D"))],
        ["Fecha de toma de muestra", str(case.get("collection_date", "N/D"))],
        ["Fecha de recepcion", str(case.get("reception_date", "N/D"))],
        ["Calidad de muestra", str(case.get("sample_quality", "N/D"))],
        ["Metodo usado", str(case.get("method_used", "N/D"))],
        ["Observaciones preanaliticas", str(case.get("preanalytical_observations", "N/D")) or "N/D"],
    ]
    story.append(_styled_table(sample_rows))

    story.extend(
        [
        Paragraph("Resumen del caso", heading),
        Paragraph(
            f"Sexo reportado: {summary.get('sex', 'N/D')}. "
            f"Diagnostico presuntivo: {summary.get('presumptive_diagnosis', 'N/D')}. "
            f"Clasificacion molecular simulada: {summary.get('molecular_class')}. "
            f"Riesgo academico simulado: {summary.get('risk')}. Confianza: {summary.get('confidence')}.",
            body,
        ),
        ]
    )

    story.append(Paragraph("Sintomas y resultados del laboratorio", heading))
    input_rows = [
        ["Campo", "Contenido"],
        ["Sintomas", ", ".join(case.get("symptoms", [])) or "N/D"],
        ["Resultados del laboratorio", ", ".join(case.get("lab_results", [])) or "N/D"],
        ["Valores de referencia", str(case.get("reference_values", "N/D")) or "N/D"],
        ["Unidades", str(case.get("units", "N/D")) or "N/D"],
        ["Estado del resultado", str(case.get("result_status", "N/D")) or "N/D"],
    ]
    story.append(_styled_table(input_rows))

    story.append(Paragraph("Datos omicos ingresados", heading))
    omics_rows = [
        ["Tipo de dato", "Contenido"],
        ["Genes alterados", ", ".join(case.get("genomic", [])) or "N/D"],
        ["Genes transcriptomicos", ", ".join(case.get("transcriptomic", [])) or "N/D"],
        ["Proteinas alteradas", ", ".join(case.get("proteomic", [])) or "N/D"],
        ["Metabolitos alterados", ", ".join(case.get("metabolomic", [])) or "N/D"],
    ]
    story.append(_styled_table(omics_rows))

    if case.get("recommendation_rows"):
        story.append(Paragraph("Panel sugerido por BioNexus AI", heading))
        recommendation_rows = [["Perfil", "Marcador", "Muestra", "Tecnica", "Validacion"]]
        for row in case["recommendation_rows"][:16]:
            recommendation_rows.append(
                [
                    row["Perfil sugerido"],
                    row["Marcador recomendado"],
                    row.get("Tipo de muestra recomendada", "N/D"),
                    row.get("Tecnica sugerida", "N/D"),
                    row.get("Profesional que debe validar", "N/D"),
                ]
            )
        story.append(_styled_table(recommendation_rows, font_size=6))

    story.append(Paragraph("Biomarcadores candidatos", heading))
    candidate_rows = [["Tipo", "Biomarcador", "Categoria", "Ruta asociada"]]
    for row in analysis["candidates"][:12]:
        candidate_rows.append(
            [
                row["Tipo de dato"],
                row["Biomarcador candidato"],
                row["Categoria"],
                row["Ruta asociada"],
            ]
        )
    story.append(_styled_table(candidate_rows, font_size=7))

    story.append(Paragraph("Rutas posiblemente alteradas", heading))
    if analysis["altered_pathways"]:
        pathway_rows = [["Categoria", "Ruta o proceso", "Evidencia"]]
        for row in analysis["altered_pathways"]:
            pathway_rows.append([row["Categoria"], row["Ruta o proceso"], row["Evidencia"]])
        story.append(_styled_table(pathway_rows, font_size=8))
    else:
        story.append(Paragraph("No se identificaron rutas suficientes con las reglas del prototipo.", body))

    story.append(Paragraph("Interpretacion general", heading))
    story.extend(_paragraph_list(analysis["interpretations"], body))

    story.append(Paragraph("Hipotesis diagnostica", heading))
    story.extend(_paragraph_list(analysis.get("diagnostic_hypothesis", []), body))

    story.append(Paragraph("Nivel de alerta", heading))
    story.append(Paragraph(str(summary.get("alert", "N/D")), body))

    story.append(Paragraph("Posible orientacion terapeutica academica", heading))
    story.extend(_paragraph_list(analysis.get("treatment_orientation", []), body))

    story.append(Paragraph("Recomendaciones de seguimiento", heading))
    follow_up = list(analysis["recommendations"]) + [
        "Programar revision del caso con el equipo academico o profesional responsable.",
        "Documentar cambios en sintomas, resultados de laboratorio y nuevos datos omicos antes de repetir el analisis.",
    ]
    story.extend(_paragraph_list(follow_up, body))

    story.append(Paragraph("Limitaciones y advertencia etica", heading))
    story.extend(_paragraph_list(analysis["limitations"], body))
    story.append(
        Paragraph(
            "Este reporte usa frases de posibilidad: posible asociacion, biomarcador candidato y requiere validacion. "
            "No reemplaza al medico, bacteriologo, bioinformatico ni investigador.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _styled_table(rows: List[List[str]], font_size: int = 8) -> Table:
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table
