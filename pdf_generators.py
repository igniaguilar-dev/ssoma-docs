from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

W, H = A4
GOLD  = colors.HexColor('#F5A623')
DARK  = colors.HexColor('#1A1A2E')
GRAY  = colors.HexColor('#F2F2F2')
RED_C = colors.HexColor('#C0392B')
AMB   = colors.HexColor('#F39C12')
GRN   = colors.HexColor('#27AE60')

def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7, alignment=TA_CENTER))
    s.add(ParagraphStyle('TD', fontName='Helvetica',      fontSize=7, alignment=TA_LEFT))
    s.add(ParagraphStyle('TDC',fontName='Helvetica',      fontSize=7, alignment=TA_CENTER))
    s.add(ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, alignment=TA_CENTER))
    s.add(ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=9,  alignment=TA_CENTER))
    s.add(ParagraphStyle('SM', fontName='Helvetica',      fontSize=7.5))
    return s

def _nivel_color(n):
    n = str(n).strip().upper()
    if n in ('A','ALTO'):   return RED_C
    if n in ('M','MEDIO'):  return AMB
    if n in ('B','BAJO'):   return GRN
    return colors.white

# ══════════════════════════════════════════════════════════
# IPERC
# ══════════════════════════════════════════════════════════
def generar_iperc_pdf(datos, path):
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=1*cm, rightMargin=1*cm,
                             topMargin=1.2*cm, bottomMargin=1*cm)
    st   = _styles()
    els  = []

    # Encabezado
    hdr = Table([
        [Paragraph('<b>METASIL</b>', st['H1']),
         Paragraph('IPERC CONTINUO', st['H1']),
         Paragraph('UNIDAD MINERA<br/>SAN JUAN DE CHORUNGA', st['H2'])]
    ], colWidths=[4*cm, 9*cm, 5*cm])
    hdr.setStyle(TableStyle([
        ('BOX',      (0,0),(-1,-1), 0.5, DARK),
        ('INNERGRID',(0,0),(-1,-1), 0.5, DARK),
        ('BACKGROUND',(1,0),(1,0), GOLD),
        ('VALIGN',   (0,0),(-1,-1),'MIDDLE'),
        ('ROWHEIGHT', (0,0),(-1,-1), 1.2*cm),
    ]))
    els.append(hdr); els.append(Spacer(1, 4))

    # Datos generales
    def lbl(t): return Paragraph(f'<b>{t}</b>', st['SM'])
    def val(t): return Paragraph(str(t), st['SM'])

    gen = Table([
        [lbl('ÁREA/PROYECTO:'), val(datos.get('area','')),
         lbl('ZONA/NIVEL:'),    val(datos.get('zona','')),
         lbl('TURNO:'),         val(datos.get('turno','')),
         lbl('FECHA:'),         val(datos.get('fecha',''))],
        [lbl('LABOR/LUGAR:'),   val(datos.get('labor','')), '', '', '', '', '', ''],
        [lbl('ACTIVIDAD/TAREA:'), val(datos.get('actividad','')), '', '', '', '', '', ''],
    ], colWidths=[2.8*cm,3.5*cm,2.2*cm,2.5*cm,1.5*cm,1.5*cm,1.5*cm,3*cm])
    gen.setStyle(TableStyle([
        ('BOX',      (0,0),(-1,-1),0.5,DARK),
        ('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('SPAN',(1,1),(7,1)),('SPAN',(1,2),(7,2)),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
        ('BACKGROUND',(0,0),(0,-1),GRAY),
        ('BACKGROUND',(2,0),(2,0),GRAY),
        ('BACKGROUND',(4,0),(4,0),GRAY),
        ('BACKGROUND',(6,0),(6,0),GRAY),
    ]))
    els.append(gen); els.append(Spacer(1,4))

    # Trabajadores
    trab_rows = [[Paragraph('<b>HORA</b>',st['TH']),
                  Paragraph('<b>NOMBRES Y APELLIDOS</b>',st['TH']),
                  Paragraph('<b>FIRMA</b>',st['TH'])]]
    for t in (datos.get('trabajadores') or []):
        trab_rows.append([val(t.get('hora','')), val(t.get('nombre','')), ''])
    while len(trab_rows) < 7:
        trab_rows.append(['','',''])
    tw = Table(trab_rows, colWidths=[2.5*cm, 8*cm, 8*cm])
    tw.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(-1,0),GOLD),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
    ]))
    els.append(Paragraph('<b>DATOS DE LOS TRABAJADORES</b>', st['H2']))
    els.append(Spacer(1,3)); els.append(tw); els.append(Spacer(1,6))

    # Tabla IPERC
    ip_rows = [[
        Paragraph('<b>PELIGRO / ASPECTO</b>',st['TH']),
        Paragraph('<b>RIESGO / IMPACTO</b>',st['TH']),
        Paragraph('<b>NIVEL ANTES</b>',st['TH']),
        Paragraph('<b>MEDIDAS DE CONTROL</b>',st['TH']),
        Paragraph('<b>NIVEL DESPUÉS</b>',st['TH']),
    ]]
    for p in (datos.get('peligros') or []):
        na = p.get('nivel_antes','')
        nd = p.get('nivel_despues','')
        ip_rows.append([
            Paragraph(p.get('peligro',''), st['TD']),
            Paragraph(p.get('riesgo',''),  st['TD']),
            Paragraph(str(na), st['TDC']),
            Paragraph(p.get('medidas',''), st['TD']),
            Paragraph(str(nd), st['TDC']),
        ])
    while len(ip_rows) < 8:
        ip_rows.append(['','','','',''])

    ip = Table(ip_rows, colWidths=[4*cm,4*cm,2.5*cm,6*cm,2.5*cm])
    ip_style = [
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(-1,0),GOLD),('FONTSIZE',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWHEIGHT',(0,0),(-1,-1),0.7*cm),
    ]
    for row_i, p in enumerate(datos.get('peligros',[]), start=1):
        na = str(p.get('nivel_antes','')).strip().upper()
        nd = str(p.get('nivel_despues','')).strip().upper()
        for col, nivel in [(2, na), (4, nd)]:
            c = _nivel_color(nivel)
            if c != colors.white:
                ip_style.append(('BACKGROUND',(col,row_i),(col,row_i), c))
                ip_style.append(('TEXTCOLOR',(col,row_i),(col,row_i), colors.white))
    ip.setStyle(TableStyle(ip_style))
    els.append(Paragraph('<b>IPERC CONTINUO</b>', st['H2']))
    els.append(Spacer(1,3)); els.append(ip); els.append(Spacer(1,6))

    # Secuencia
    seq = Table([
        [Paragraph('<b>SECUENCIA PARA CONTROLAR EL PELIGRO Y REDUCIR EL RIESGO</b>', st['TH'])],
        [Paragraph(datos.get('secuencia',''), st['SM'])],
    ], colWidths=[19*cm])
    seq.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(0,0),GOLD),('ROWHEIGHT',(0,1),(0,1),1.5*cm),
    ]))
    els.append(seq); els.append(Spacer(1,6))

    # Supervisor
    sv = Table([[
        Paragraph(f'<b>Supervisor:</b> {datos.get("supervisor","")}', st['SM']),
        Paragraph(f'<b>Medida correctiva:</b> {datos.get("medida_correctiva","")}', st['SM']),
    ]], colWidths=[9.5*cm, 9.5*cm])
    sv.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('ROWHEIGHT',(0,0),(-1,-1),1.2*cm),
    ]))
    els.append(sv)
    doc.build(els)


# ══════════════════════════════════════════════════════════
# PETAR
# ══════════════════════════════════════════════════════════
def generar_petar_pdf(datos, path):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.2*cm, bottomMargin=1*cm)
    st  = _styles()
    els = []

    # Encabezado
    hdr = Table([[
        Paragraph('<b>METASIL</b>', st['H1']),
        Paragraph('PERMISO PARA TRABAJOS EN ALTURA (PETAR)', st['H1']),
        Table([
            [Paragraph('<b>Código:</b> SEG-ERC-01-F-01', st['SM'])],
            [Paragraph('<b>Versión:</b> 01', st['SM'])],
            [Paragraph(f'<b>Fecha:</b> 09/11/2024', st['SM'])],
            [Paragraph('<b>Página:</b> 1 de 1', st['SM'])],
        ], colWidths=[5*cm])
    ]], colWidths=[3.5*cm, 10.5*cm, 5*cm])
    hdr.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(1,0),(1,0),GOLD),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWHEIGHT',(0,0),(-1,-1),1.8*cm),
    ]))
    els.append(hdr); els.append(Spacer(1,4))

    def lbl(t): return Paragraph(f'<b>{t}</b>', st['SM'])
    def val(t): return Paragraph(str(t), st['SM'])
    def yesno(v): return '☑ SÍ  ☐ NO' if v == 'si' else '☐ SÍ  ☑ NO'

    # Datos generales
    gen = Table([
        [lbl('ÁREA:'), val(datos.get('area','')),
         lbl('LUGAR:'), val(datos.get('lugar','')),
         lbl('FECHA:'), val(datos.get('fecha',''))],
        [lbl('HORA INICIO:'), val(datos.get('hora_inicio','')),
         lbl('HORA FINAL:'),  val(datos.get('hora_final','')),
         lbl('NÚMERO:'),      val(datos.get('numero',''))],
    ], colWidths=[2.5*cm,4*cm,2.5*cm,4.5*cm,2.5*cm,3*cm])
    gen.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(0,-1),GRAY),('BACKGROUND',(2,0),(2,-1),GRAY),
        ('BACKGROUND',(4,0),(4,-1),GRAY),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
    ]))
    els.append(gen); els.append(Spacer(1,4))

    # Verificaciones
    ver = Table([
        [Paragraph('<b>TRABAJADORES CUENTAN CON "AUTORIZACIÓN INTERNA" PARA TRABAJOS EN ALTURA:</b>', st['SM']), '', ''],
        [val('Certificado de suficiencia médica vigente'),
         val(yesno(datos.get('cert_medica','no'))), ''],
        [val('Capacitación sobre "Trabajo en Altura"'),
         val(yesno(datos.get('cap_altura','no'))), ''],
        [val('Son trabajadores calificados'),
         val(yesno(datos.get('trab_calificados','no'))), ''],
    ], colWidths=[12*cm, 4*cm, 3*cm])
    ver.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('SPAN',(0,0),(2,0)),('BACKGROUND',(0,0),(2,0),GRAY),
        ('FONTSIZE',(0,0),(-1,-1),7),('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
    ]))
    els.append(ver); els.append(Spacer(1,4))

    # Descripción del trabajo
    desc = Table([
        [Paragraph('<b>1.- DESCRIPCIÓN DEL TRABAJO:</b>', st['SM'])],
        [val(datos.get('descripcion_trabajo',''))],
    ], colWidths=[19*cm])
    desc.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(0,0),GRAY),('ROWHEIGHT',(0,1),(0,1),1.2*cm),
        ('FONTSIZE',(0,0),(-1,-1),7),
    ]))
    els.append(desc); els.append(Spacer(1,4))

    # Personal
    p_rows = [[lbl('OCUPACIÓN'), lbl('NOMBRES Y APELLIDOS'), lbl('FIRMA INICIO'), lbl('FIRMA TÉRMINO')]]
    for p in (datos.get('personal') or []):
        p_rows.append([val(p.get('ocupacion','')), val(p.get('nombre','')), '', ''])
    while len(p_rows) < 7:
        p_rows.append(['','','',''])
    pt = Table(p_rows, colWidths=[4*cm,6*cm,4.5*cm,4.5*cm])
    pt.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(-1,0),GOLD),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
    ]))
    els.append(Paragraph('<b>2.- RESPONSABLES DEL TRABAJO / PERSONAL AUTORIZADO:</b>', st['SM']))
    els.append(Spacer(1,3)); els.append(pt); els.append(Spacer(1,4))

    # EPP
    EPP_LABELS = {
        'casco_barbiquejo': 'Casco con barbiquejo/carrilera',
        'arnes_cuerpo_entero': 'Arnés de cuerpo entero',
        'mameluco': 'Mameluco', 'correa_lampara': 'Correa para lámpara',
        'guantes_jebe': 'Guantes de jebe', 'morral_lona': 'Morral de lona',
        'botas_jebe': 'Botas de jebe', 'protector_oidos': 'Protector de oídos',
        'respirador': 'Respirador c/gases, polvo',
        'linea_anclaje': 'Línea de anclaje doble vía',
        'protector_visual': 'Protector visual',
        'correa_antitrauma': 'Correa antitrauma',
    }
    epp_sel = set(datos.get('epp', []))
    all_epp = list(EPP_LABELS.keys())
    epp_rows = [[Paragraph('<b>3.- EQUIPO DE PROTECCIÓN PERSONAL</b>', st['SM']), '']]
    for i in range(0, len(all_epp), 2):
        left  = all_epp[i]
        right = all_epp[i+1] if i+1 < len(all_epp) else ''
        lmark = '☑' if left  in epp_sel else '☐'
        rmark = '☑' if right in epp_sel else '☐'
        rlabel = EPP_LABELS.get(right,'')
        epp_rows.append([
            val(f'{lmark}  {EPP_LABELS[left]}'),
            val(f'{rmark}  {rlabel}') if right else val(''),
        ])
    et = Table(epp_rows, colWidths=[9.5*cm, 9.5*cm])
    et.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('SPAN',(0,0),(1,0)),('BACKGROUND',(0,0),(1,0),GRAY),
        ('FONTSIZE',(0,0),(-1,-1),7),('ROWHEIGHT',(0,0),(-1,-1),0.5*cm),
    ]))
    els.append(et); els.append(Spacer(1,4))

    # Herramientas
    herb = Table([
        [Paragraph('<b>4.- HERRAMIENTAS, EQUIPOS Y MATERIAL:</b>', st['SM'])],
        [val(datos.get('herramientas',''))],
    ], colWidths=[19*cm])
    herb.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(0,0),GRAY),('ROWHEIGHT',(0,1),(0,1),1*cm),
        ('FONTSIZE',(0,0),(-1,-1),7),
    ]))
    els.append(herb); els.append(Spacer(1,4))

    # Procedimiento
    proc = Table([
        [Paragraph('<b>5.- PROCEDIMIENTO / PLAN DE TRABAJO:</b>', st['SM'])],
        [val(datos.get('procedimiento',''))],
    ], colWidths=[19*cm])
    proc.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(0,0),GRAY),('ROWHEIGHT',(0,1),(0,1),1.5*cm),
        ('FONTSIZE',(0,0),(-1,-1),7),
    ]))
    els.append(proc); els.append(Spacer(1,4))

    # Firmas
    firma = Table([[
        Table([
            [Paragraph('<b>Autorizado por: Ingeniero Supervisor</b>', st['SM'])],
            [val(datos.get('supervisor_nombre',''))],
            [val(f"CIP: {datos.get('supervisor_cip','')}")],
            [Paragraph('Firma: ___________________', st['SM'])],
        ], colWidths=[9*cm]),
        Table([
            [Paragraph('<b>Autorizado por: Jefe de Área</b>', st['SM'])],
            [val(datos.get('jefe_nombre',''))],
            [''],
            [Paragraph('Firma: ___________________', st['SM'])],
        ], colWidths=[9*cm]),
    ]], colWidths=[9.5*cm, 9.5*cm])
    firma.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('FONTSIZE',(0,0),(-1,-1),7),('ROWHEIGHT',(0,0),(-1,-1),2*cm),
    ]))
    els.append(firma)
    doc.build(els)


# ══════════════════════════════════════════════════════════
# CHECK LIST ARNÉS
# ══════════════════════════════════════════════════════════
def generar_checklist_pdf(datos, path):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.2*cm, bottomMargin=1*cm)
    st  = _styles()
    els = []

    # Encabezado
    hdr = Table([[
        Paragraph('<b>METASIL</b>', st['H1']),
        Paragraph('CHECK LIST DE PRE-USO<br/>ARNÉS Y RETRÁCTIL', st['H1']),
        Table([
            [Paragraph('<b>CÓDIGO:</b> MET-RE-009', st['SM'])],
            [Paragraph('<b>REVISIÓN:</b> 01', st['SM'])],
            [Paragraph('<b>PÁGINA:</b> 1 DE 1', st['SM'])],
        ], colWidths=[5*cm])
    ]], colWidths=[3.5*cm, 10.5*cm, 5*cm])
    hdr.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(1,0),(1,0),GOLD),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWHEIGHT',(0,0),(-1,-1),1.5*cm),
    ]))
    els.append(hdr); els.append(Spacer(1,6))

    def lbl(t): return Paragraph(f'<b>{t}</b>', st['SM'])
    def val(t): return Paragraph(str(t), st['SM'])

    # Cabecera
    cab = Table([
        [lbl('Fecha:'), val(datos.get('fecha','')), lbl('Área:'), val(datos.get('area',''))],
        [lbl('Supervisor:'), val(datos.get('supervisor','')), '', ''],
    ], colWidths=[2.5*cm, 6*cm, 2.5*cm, 8*cm])
    cab.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('SPAN',(1,1),(3,1)),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.55*cm),
    ]))
    els.append(cab); els.append(Spacer(1,6))

    # Leyenda
    ley = Table([[
        val('B: Bueno'), val('M: Malo'), val('N: No Tiene'), val('NA: No Aplica')
    ]], colWidths=[4*cm,4*cm,4*cm,7*cm])
    ley.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(-1,-1),GRAY),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,0),(-1,-1),0.45*cm),
    ]))
    els.append(ley); els.append(Spacer(1,4))

    def cond(v): return Paragraph(str(v).upper() if v else '', st['TDC'])

    CONDICION_HDR = [lbl('B'), lbl('M'), lbl('N'), lbl('NA')]

    def section(title, code_label, code_val, items_dict, labels):
        rows = [
            [Paragraph(f'<b>{title}</b>', st['SM']),
             Paragraph(f'<b>CÓDIGO:</b> {code_val}', st['SM']), '', '', '', ''],
            [Paragraph('<b>N°</b>', st['TH']),
             Paragraph('<b>ELEMENTOS A INSPECCIONAR</b>', st['TH'])] + CONDICION_HDR,
        ]
        for code, label in labels:
            v = items_dict.get(code, '')
            rows.append([val(code), val(label),
                         cond('✓' if v=='B' else ''),
                         cond('✓' if v=='M' else ''),
                         cond('✓' if v=='N' else ''),
                         cond('✓' if v=='NA' else '')])
        t = Table(rows, colWidths=[1.5*cm,11*cm,1.5*cm,1.5*cm,1.5*cm,2*cm])
        t.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
            ('SPAN',(0,0),(1,0)),('SPAN',(2,0),(5,0)),
            ('BACKGROUND',(0,0),(5,0),GOLD),
            ('BACKGROUND',(0,1),(5,1),GRAY),
            ('FONTSIZE',(0,0),(-1,-1),7),('ROWHEIGHT',(0,0),(-1,-1),0.5*cm),
        ]))
        return t

    ARNES_LABELS = [
        ('1.1','Correa de Hombro'),('1.2','Banda Secundaria'),
        ('1.3','Banda Subglutea'),('1.4','Banda de muslo'),
        ('1.5','Hebillas'),('1.6','Anillos D'),
    ]
    LINEA_LABELS = [
        ('2.1','Mosquetón'),('2.2','Costuras'),
        ('2.3','Línea de sujeción'),
        ('2.4','Gancho de seguridad de cierre y bloqueo automático'),
        ('2.5','Absorbedor de energía (Amortiguador)'),
    ]
    BLOCK_LABELS = [
        ('3.1','La manija de anclaje está en buenas condiciones'),
        ('3.2','El mosquetón no cuenta con malformaciones, corrosión y/o grietamiento'),
        ('3.3','La carcasa se encuentra en buen estado'),
        ('3.4','El cable y/o cinta se despliega y retrae'),
        ('3.5','Se encuentra activado el indicador de impacto'),
        ('3.6','El tejido trenzado se encuentra en buen estado'),
    ]

    els.append(section('1  Aspectos Generales', 'CÓDIGO', datos.get('codigo_arnes',''),
                        datos.get('items_arnes',{}), ARNES_LABELS))
    els.append(Spacer(1,4))
    els.append(section('2  Línea de anclaje', 'CÓDIGO', datos.get('codigo_linea',''),
                        datos.get('items_linea',{}), LINEA_LABELS))
    els.append(Spacer(1,4))
    els.append(section('3  Block retráctil', 'CÓDIGO', datos.get('codigo_block',''),
                        datos.get('items_block',{}), BLOCK_LABELS))
    els.append(Spacer(1,6))

    # Observaciones y firmas
    obs = Table([
        [Paragraph('<b>OBSERVACIONES:</b>', st['SM']),
         Paragraph('<b>RECOMENDACIONES:</b>', st['SM'])],
        [val(datos.get('observaciones','')), val(datos.get('recomendaciones',''))],
    ], colWidths=[9.5*cm, 9.5*cm])
    obs.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('BACKGROUND',(0,0),(1,0),GRAY),('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWHEIGHT',(0,1),(1,1),1.2*cm),
    ]))
    els.append(obs); els.append(Spacer(1,6))

    firmas = Table([[
        Table([
            [Paragraph('<b>REALIZADO POR:</b>', st['SM'])],
            [val(f"Nombre: {datos.get('realizado_nombre','')}")],
            [val(f"Cargo:  {datos.get('realizado_cargo','')}")],
        ], colWidths=[9*cm]),
        Table([
            [Paragraph('<b>REVISADO POR:</b>', st['SM'])],
            [val(f"Nombre: {datos.get('revisado_nombre','')}")],
            [val(f"Cargo:  {datos.get('revisado_cargo','')}")],
        ], colWidths=[9*cm]),
    ]], colWidths=[9.5*cm, 9.5*cm])
    firmas.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,DARK),('INNERGRID',(0,0),(-1,-1),0.5,DARK),
        ('FONTSIZE',(0,0),(-1,-1),7),('ROWHEIGHT',(0,0),(-1,-1),1.8*cm),
    ]))
    els.append(firmas)
    doc.build(els)