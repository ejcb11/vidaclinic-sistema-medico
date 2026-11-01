# ==============================================================================
# VidaClinic — Generador de Reportes Corporativos (PDF & Excel)
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

"""Generación de reportes en Excel (.xlsx) y PDF."""

import io
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from bcv import get_tasa_bcv, usd_to_bs, format_bs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, 'static', 'images', 'logo.jpg')
RECIBO_BG_PATH = os.path.join(BASE_DIR, 'static', 'images', 'recibo_bg_letter.jpg')

def draw_recibo_watermark(canvas, doc):
    canvas.saveState()
    if os.path.exists(RECIBO_BG_PATH):
        try:
            canvas.drawImage(
                RECIBO_BG_PATH,
                0, 0,
                width=doc.pagesize[0],
                height=doc.pagesize[1],
                preserveAspectRatio=False
            )
        except Exception:
            pass
    canvas.restoreState()

# Estilos base para Excel
HEADER_FILL = PatternFill(start_color="047857", end_color="047857", fill_type="solid")
HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Segoe UI", size=14, bold=True, color="065F46")
SUBTITLE_FONT = Font(name="Segoe UI", size=9, italic=True, color="475569")
DATA_FONT = Font(name="Segoe UI", size=10)
BOLD_FONT = Font(name="Segoe UI", size=10, bold=True)
THIN_BORDER = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

def adjust_excel_column_widths(sheet):
    for col_idx, col in enumerate(sheet.columns, 1):
        max_len = 0
        col_letter = get_column_letter(col_idx)
        for cell in col:
            if cell.coordinate in sheet.merged_cells:
                continue
            val = str(cell.value or '')
            if len(val) > max_len:
                max_len = len(val)
        sheet.column_dimensions[col_letter].width = max(max_len + 4, 14)

# Reportes Excel
def generate_citas_excel(citas) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Citas"

    ws.merge_cells("A1:I1")
    ws["A1"] = "VIDACLINIC - REPORTE DE CITAS MÉDICAS"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:I2")
    ws["A2"] = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.append([])

    headers = [
        "Código", "Fecha", "Hora", "Paciente", "Cédula", 
        "Médico Tratante", "Especialidad", "Padecimiento / Motivo", 
        "Costo ($)", "Dividendo Médico ($)", "Estado", "Pago Médico"
    ]
    ws.append(headers)

    for cell in ws[4]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for c in citas:
        row = [
            c['codigo'],
            c['fecha'],
            c['hora'],
            f"{c['paciente_nombre']} {c['paciente_apellido']}",
            c['paciente_cedula'],
            f"Dr(a). {c['doctor_nombre']} {c['doctor_apellido']}",
            c['especialidad_nombre'],
            c['padecimiento'],
            c['costo_consulta'],
            c['monto_doctor'],
            c['estado'],
            c['estado_pago_medico']
        ]
        ws.append(row)

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, min_col=1, max_col=12):
        for cell in row:
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if cell.column in [9, 10]:
                cell.number_format = '$#,##0.00'
                cell.alignment = Alignment(horizontal="right")

    adjust_excel_column_widths(ws)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_liquidaciones_excel(liquidaciones) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Liquidaciones a Médicos"

    ws.merge_cells("A1:H1")
    ws["A1"] = "VIDACLINIC - HISTORIAL DE PAGOS Y LIQUIDACIONES A MÉDICOS"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.append([])

    headers = [
        "Comprobante", "Fecha Pago", "Médico", "Especialidad", 
        "Consultas", "Monto Total ($)", "Dividendo Médico ($)", 
        "Retención Clínica ($)", "Método Pago", "Referencia"
    ]
    ws.append(headers)

    for cell in ws[4]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for l in liquidaciones:
        ws.append([
            l['numero_comprobante'],
            l['fecha_pago'],
            f"Dr(a). {l['doctor_nombre']} {l['doctor_apellido']}",
            l['especialidad_nombre'],
            l['total_consultas'],
            l['monto_total_consultas'],
            l['monto_dividendo_doctor'],
            l['monto_retenido_clinica'],
            l['metodo_pago'],
            l['numero_referencia'] or 'N/A'
        ])

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, min_col=1, max_col=10):
        for cell in row:
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if cell.column in [6, 7, 8]:
                cell.number_format = '$#,##0.00'
                cell.alignment = Alignment(horizontal="right")

    adjust_excel_column_widths(ws)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_pacientes_excel(pacientes) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Directorio de Pacientes"

    ws.merge_cells("A1:H1")
    ws["A1"] = "VIDACLINIC - PADRÓN OFICIAL DE PACIENTES"
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = f"Fecha de reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.append([])

    headers = ["ID", "Nombres", "Apellidos", "Cédula", "Nacimiento", "Género", "Teléfono", "Email", "Grupo Sangre"]
    ws.append(headers)

    for cell in ws[4]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for p in pacientes:
        ws.append([
            p['id'],
            p['nombre'],
            p['apellido'],
            p['cedula'],
            p['fecha_nacimiento'],
            p['genero'],
            p['telefono'],
            p['email'],
            p['grupo_sanguineo']
        ])

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, min_col=1, max_col=9):
        for cell in row:
            cell.font = DATA_FONT
            cell.border = THIN_BORDER

    adjust_excel_column_widths(ws)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# Estilos base para PDF
def get_pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ClinicTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#065F46'),
        alignment=1
    ))
    styles.add(ParagraphStyle(
        'ClinicSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=1
    ))
    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    ))
    styles.add(ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#065F46')
    ))
    return styles

def generate_citas_pdf(citas) -> io.BytesIO:
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_pdf_styles()
    story = []

    story.append(Paragraph("VIDACLINIC", styles['ClinicTitle']))
    story.append(Paragraph("VidaClinic | Reporte Oficial de Citas Agendadas", styles['ClinicSubtitle']))
    story.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['ClinicSubtitle']))
    story.append(Spacer(1, 15))

    table_data = [[
        Paragraph("Código", styles['TableHeader']),
        Paragraph("Fecha", styles['TableHeader']),
        Paragraph("Paciente", styles['TableHeader']),
        Paragraph("Médico", styles['TableHeader']),
        Paragraph("Especialidad", styles['TableHeader']),
        Paragraph("Padecimiento", styles['TableHeader']),
        Paragraph("Costo ($)", styles['TableHeader']),
        Paragraph("Estado", styles['TableHeader'])
    ]]

    for c in citas:
        table_data.append([
            Paragraph(str(c['codigo']), styles['TableCellBold']),
            Paragraph(f"{c['fecha']}<br/>{c['hora']}", styles['TableCell']),
            Paragraph(f"{c['paciente_nombre']} {c['paciente_apellido']}", styles['TableCell']),
            Paragraph(f"Dr. {c['doctor_apellido']}", styles['TableCell']),
            Paragraph(str(c['especialidad_nombre']), styles['TableCell']),
            Paragraph(str(c['padecimiento'])[:40] + ('...' if len(c['padecimiento']) > 40 else ''), styles['TableCell']),
            Paragraph(f"${c['costo_consulta']:.2f}", styles['TableCell']),
            Paragraph(str(c['estado']), styles['TableCell'])
        ])

    col_widths = [55, 55, 95, 80, 75, 110, 45, 50]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FDF4')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(t)
    doc.build(story, onFirstPage=draw_recibo_watermark, onLaterPages=draw_recibo_watermark)
    output.seek(0)
    return output

def generate_recibo_cita_pdf(cita) -> io.BytesIO:
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = get_pdf_styles()
    story = []

    if os.path.exists(LOGO_PATH):
        try:
            story.append(RLImage(LOGO_PATH, width=130, height=45))
            story.append(Spacer(1, 10))
        except Exception:
            pass

    story.append(Paragraph("VIDACLINIC - COMPROBANTE DE CONSULTA MÉDICA", styles['ClinicTitle']))
    story.append(Paragraph(f"Código Único de Cita: <b>{cita['codigo']}</b> | Estado: <b>{cita['estado']}</b>", styles['ClinicSubtitle']))
    story.append(Spacer(1, 15))

    datos_paciente = [
        [Paragraph("<b>DATOS DEL PACIENTE</b>", styles['TableHeader']), Paragraph("", styles['TableHeader'])],
        [Paragraph("<b>Nombre Completo:</b>", styles['TableCell']), Paragraph(f"{cita['paciente_nombre']} {cita['paciente_apellido']}", styles['TableCell'])],
        [Paragraph("<b>Cédula / Documento:</b>", styles['TableCell']), Paragraph(str(cita['paciente_cedula']), styles['TableCell'])],
        [Paragraph("<b>Teléfono:</b>", styles['TableCell']), Paragraph(str(cita['paciente_telefono']), styles['TableCell'])],
        [Paragraph("<b>Correo:</b>", styles['TableCell']), Paragraph(str(cita['paciente_email']), styles['TableCell'])],
    ]
    t_paciente = Table(datos_paciente, colWidths=[150, 380])
    t_paciente.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#059669')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_paciente)
    story.append(Spacer(1, 12))

    tasa_info = get_tasa_bcv()
    tasa_val = tasa_info['tasa']
    monto_bs = usd_to_bs(cita['costo_consulta'], tasa_val)

    datos_consulta = [
        [Paragraph("<b>DETALLES DE LA ATENCIÓN MÉDICA</b>", styles['TableHeader']), Paragraph("", styles['TableHeader'])],
        [Paragraph("<b>Médico Tratante:</b>", styles['TableCell']), Paragraph(f"Dr(a). {cita['doctor_nombre']} {cita['doctor_apellido']}", styles['TableCell'])],
        [Paragraph("<b>Especialidad Médica:</b>", styles['TableCell']), Paragraph(str(cita['especialidad_nombre']), styles['TableCell'])],
        [Paragraph("<b>Fecha y Hora:</b>", styles['TableCell']), Paragraph(f"{cita['fecha']} a las {cita['hora']} hrs", styles['TableCell'])],
        [Paragraph("<b>Padecimiento Registrado:</b>", styles['TableCellBold']), Paragraph(str(cita['padecimiento']), styles['TableCell'])],
        [Paragraph("<b>Costo Total Consulta:</b>", styles['TableCellBold']), Paragraph(f"<b>${cita['costo_consulta']:.2f} USD</b>", styles['TableCellBold'])],
        [Paragraph("<b>Equivalente en Bolívares:</b>", styles['TableCellBold']), Paragraph(f"<b>{format_bs(monto_bs)}</b> (Tasa BCV: Bs. {tasa_val:.2f}/USD)", styles['TableCellBold'])],
    ]
    if cita['diagnostico_observaciones']:
        datos_consulta.append([
            Paragraph("<b>Diagnóstico / Indicaciones:</b>", styles['TableCellBold']),
            Paragraph(str(cita['diagnostico_observaciones']), styles['TableCell'])
        ])

    t_consulta = Table(datos_consulta, colWidths=[150, 380])
    t_consulta.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#047857')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_consulta)
    story.append(Spacer(1, 35))

    firmas = [
        [Paragraph("___________________________________<br/><b>Firma y Sello del Médico</b>", styles['ClinicSubtitle']),
         Paragraph("___________________________________<br/><b>Conformidad del Paciente</b>", styles['ClinicSubtitle'])]
    ]
    t_firmas = Table(firmas, colWidths=[260, 260])
    t_firmas.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(t_firmas)

    doc.build(story, onFirstPage=draw_recibo_watermark, onLaterPages=draw_recibo_watermark)
    output.seek(0)
    return output

def generate_recibo_liquidacion_pdf(liq) -> io.BytesIO:
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = get_pdf_styles()
    story = []

    if os.path.exists(LOGO_PATH):
        try:
            story.append(RLImage(LOGO_PATH, width=130, height=45))
            story.append(Spacer(1, 10))
        except Exception:
            pass

    story.append(Paragraph("VIDACLINIC - COMPROBANTE DE LIQUIDACIÓN DE HONORARIOS", styles['ClinicTitle']))
    story.append(Paragraph(f"N° Comprobante: <b>{liq['numero_comprobante']}</b> | Fecha de Pago: <b>{liq['fecha_pago']}</b>", styles['ClinicSubtitle']))
    story.append(Spacer(1, 15))

    datos_doctor = [
        [Paragraph("<b>DATOS DEL PROFESIONAL MÉDICO</b>", styles['TableHeader']), Paragraph("", styles['TableHeader'])],
        [Paragraph("<b>Médico:</b>", styles['TableCell']), Paragraph(f"Dr(a). {liq['doctor_nombre']} {liq['doctor_apellido']}", styles['TableCell'])],
        [Paragraph("<b>Cédula / Colegiatura:</b>", styles['TableCell']), Paragraph(str(liq['doctor_cedula']), styles['TableCell'])],
        [Paragraph("<b>Especialidad:</b>", styles['TableCell']), Paragraph(str(liq['especialidad_nombre']), styles['TableCell'])],
        [Paragraph("<b>Cargo Institucional:</b>", styles['TableCell']), Paragraph(str(liq.get('cargo_nombre', 'Médico Titular')), styles['TableCell'])],
        [Paragraph("<b>Método de Pago:</b>", styles['TableCell']), Paragraph(f"{liq['metodo_pago']} (Ref: {liq['numero_referencia'] or 'N/A'})", styles['TableCell'])],
    ]
    t_doc = Table(datos_doctor, colWidths=[150, 380])
    t_doc.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#047857')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_doc)
    story.append(Spacer(1, 12))

    tasa_info = get_tasa_bcv()
    tasa_val = tasa_info['tasa']
    monto_bs = usd_to_bs(liq['monto_dividendo_doctor'], tasa_val)

    datos_monto = [
        [Paragraph("<b>RESUMEN DE LIQUIDACIÓN DE DIVIDENDOS</b>", styles['TableHeader']), Paragraph("", styles['TableHeader'])],
        [Paragraph("<b>Total de Consultas Atendidas:</b>", styles['TableCell']), Paragraph(f"{liq['total_consultas']} consulta(s)", styles['TableCell'])],
        [Paragraph("<b>Monto Bruto Facturado:</b>", styles['TableCell']), Paragraph(f"${liq['monto_total_consultas']:.2f} USD", styles['TableCell'])],
        [Paragraph("<b>Gastos Operativos Retenidos Clínica:</b>", styles['TableCell']), Paragraph(f"- ${liq['monto_retenido_clinica']:.2f} USD", styles['TableCell'])],
        [Paragraph("<b>TOTAL DIVIDENDO NETO A PAGAR:</b>", styles['TableCellBold']), Paragraph(f"<b>${liq['monto_dividendo_doctor']:.2f} USD</b>", styles['TableCellBold'])],
        [Paragraph("<b>Neto a Transferir en Bolívares:</b>", styles['TableCellBold']), Paragraph(f"<b>{format_bs(monto_bs)}</b> (Tasa BCV: Bs. {tasa_val:.2f})", styles['TableCellBold'])],
    ]
    t_monto = Table(datos_monto, colWidths=[200, 330])
    t_monto.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#047857')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_monto)
    story.append(Spacer(1, 35))

    firmas = [
        [Paragraph("___________________________________<br/><b>Administración / Finanzas</b>", styles['ClinicSubtitle']),
         Paragraph("___________________________________<br/><b>Dr(a). Recibí Conforme</b>", styles['ClinicSubtitle'])]
    ]
    t_firmas = Table(firmas, colWidths=[260, 260])
    t_firmas.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(t_firmas)

    doc.build(story, onFirstPage=draw_recibo_watermark, onLaterPages=draw_recibo_watermark)
    output.seek(0)
    return output
