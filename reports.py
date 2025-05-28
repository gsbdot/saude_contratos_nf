from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO # Para gerar o PDF em memória
from datetime import datetime

# Estilos
styles = getSampleStyleSheet()
style_body = styles['BodyText']
style_title = ParagraphStyle(name='TitleStyle', parent=styles['h1'], alignment=1, spaceAfter=0.5*cm)
style_heading = ParagraphStyle(name='HeadingStyle', parent=styles['h2'], spaceAfter=0.3*cm, spaceBefore=0.5*cm)
style_table_header = ParagraphStyle(name='TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', alignment=1)
style_table_cell = ParagraphStyle(name='TableCell', parent=styles['Normal'])
style_table_cell_right = ParagraphStyle(name='TableCellRight', parent=styles['Normal'], alignment=2) # 2 = RIGHT

def build_pdf_response(buffer, filename):
    from flask import make_response
    response = make_response(buffer.getvalue())
    buffer.close()
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def gerar_pdf_lista_atas(atas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    story = []

    story.append(Paragraph("Relatório - Lista de Todas as Atas", style_title))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", style_body))
    story.append(Spacer(1, 1*cm))

    data = [
        [Paragraph("Número Ata", style_table_header), Paragraph("Ano", style_table_header), Paragraph("Descrição", style_table_header), Paragraph("Assinatura", style_table_header), Paragraph("Validade", style_table_header)]
    ]

    for ata in atas:
        data.append([
            Paragraph(ata.numero_ata, style_table_cell),
            Paragraph(str(ata.ano), style_table_cell),
            Paragraph(ata.descricao if ata.descricao else '-', style_table_cell),
            Paragraph(ata.data_assinatura.strftime('%d/%m/%Y') if ata.data_assinatura else '-', style_table_cell),
            Paragraph(ata.data_validade.strftime('%d/%m/%Y') if ata.data_validade else '-', style_table_cell),
        ])

    table = Table(data, colWidths=[3*cm, 1.5*cm, 7.5*cm, 2.5*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(table)

    doc.build(story)
    return build_pdf_response(buffer, "lista_atas.pdf")


def gerar_pdf_detalhes_ata(ata, itens_ata):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    story = []

    story.append(Paragraph(f"Relatório - Detalhes da Ata: {ata.numero_ata}", style_title))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", style_body))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"<b>Número da Ata:</b> {ata.numero_ata}", style_body))
    story.append(Paragraph(f"<b>Ano:</b> {ata.ano}", style_body))
    story.append(Paragraph(f"<b>Descrição:</b> {ata.descricao if ata.descricao else '-'}", style_body))
    story.append(Paragraph(f"<b>Data de Assinatura:</b> {ata.data_assinatura.strftime('%d/%m/%Y') if ata.data_assinatura else '-'}", style_body))
    story.append(Paragraph(f"<b>Data de Validade:</b> {ata.data_validade.strftime('%d/%m/%Y') if ata.data_validade else '-'}", style_body))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Itens da Ata", style_heading))

    if itens_ata:
        data_itens = [
            [
                Paragraph("Item", style_table_header),
                Paragraph("Un.", style_table_header),
                Paragraph("Qtd. Reg.", style_table_header),
                Paragraph("Saldo Disp.", style_table_header),
                Paragraph("Vlr. Unit.", style_table_header),
                Paragraph("P. Ativo", style_table_header),
                Paragraph("Lote", style_table_header)
            ]
        ]
        for item in itens_ata:
            data_itens.append([
                Paragraph(item.descricao_item, style_table_cell),
                Paragraph(item.unidade_medida if item.unidade_medida else '-', style_table_cell),
                Paragraph(str(item.quantidade_registrada), style_table_cell_right),
                Paragraph(str(item.saldo_disponivel), style_table_cell_right),
                Paragraph(f"{item.valor_unitario_registrado:.2f}" if item.valor_unitario_registrado is not None else '-', style_table_cell_right),
                Paragraph(item.principio_ativo if item.principio_ativo else '-', style_table_cell),
                Paragraph(item.lote if item.lote else '-', style_table_cell)
            ])
        
        table_itens = Table(data_itens, colWidths=[5*cm, 1*cm, 2*cm, 2*cm, 2*cm, 3*cm, 2*cm])
        table_itens.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(table_itens)
    else:
        story.append(Paragraph("Nenhum item cadastrado para esta ata.", style_body))

    doc.build(story)
    return build_pdf_response(buffer, f"detalhes_ata_{ata.numero_ata.replace('/', '_')}.pdf")