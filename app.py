from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3, os, uuid, json
from datetime import datetime
from pdf_generators import generar_iperc_pdf, generar_petar_pdf, generar_checklist_pdf

app = Flask(__name__)
app.secret_key = 'ssoma-secret-2024'
BASE = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE, 'static', 'uploads')
PDF_FOLDER    = os.path.join(BASE, 'static', 'pdfs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER,    exist_ok=True)

ITEMS = [
    ('1.1', 'Evaluación de riesgos documentada (IPERC Continuo)', 'formulario_iperc'),
    ('1.2', 'Identificación de peligros',                         'desde_iperc'),
    ('1.3', 'Sistema de protección contra caídas',                'subir_pdf'),
    ('1.4', 'Jerarquía de controles – Check List Arnés',          'formulario_arnes'),
    ('1.5', 'PETAR para trabajo en altura firmados',              'formulario_petar'),
    ('1.7', 'Personal autorizado con EMO vigente',                'subir_foto'),
    ('2.2', 'Se verifican sistemas primarios',                    'no_aplica'),
    ('3.1', 'Capacitación en uso de EPP anticaídas',              'subir_foto_pdf'),
    ('3.2', 'Capacitación en uso de correa antitrauma',           'no_aplica'),
]

FORM_TEMPLATES = {
    'formulario_iperc':  'form_iperc.html',
    'formulario_petar':  'form_petar.html',
    'formulario_arnes':  'form_arnes.html',
}

def get_db():
    db = sqlite3.connect(os.path.join(BASE, 'ssoma.db'))
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        item_code TEXT NOT NULL,
        tipo TEXT NOT NULL,
        filename TEXT,
        original_name TEXT,
        datos_json TEXT,
        pdf_filename TEXT,
        descripcion TEXT,
        fecha TEXT,
        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (obra_id) REFERENCES obras(id))''')
    db.commit(); db.close()

@app.route('/')
def index():
    db = get_db()
    obras = db.execute('SELECT * FROM obras ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('index.html', obras=obras)

@app.route('/obra/nueva', methods=['POST'])
def nueva_obra():
    nombre = request.form.get('nombre','').strip()
    if nombre:
        db = get_db()
        db.execute('INSERT INTO obras (nombre) VALUES (?)', (nombre,))
        db.commit(); db.close()
        flash('Obra creada correctamente', 'success')
    return redirect(url_for('index'))

@app.route('/obra/<int:obra_id>')
def obra(obra_id):
    db = get_db()
    obra_row = db.execute('SELECT * FROM obras WHERE id=?', (obra_id,)).fetchone()
    if not obra_row:
        return redirect(url_for('index'))
    docs = db.execute(
        'SELECT * FROM documentos WHERE obra_id=? ORDER BY uploaded_at DESC', (obra_id,)).fetchall()
    db.close()
    docs_por_item = {}
    for d in docs:
        docs_por_item.setdefault(d['item_code'], []).append(d)
    activos     = [i for i in ITEMS if i[2] != 'no_aplica']
    completados = sum(1 for c,_,_ in activos if c in docs_por_item)
    pct         = round(completados / len(activos) * 100) if activos else 0
    return render_template('obra.html', obra=obra_row, items=ITEMS,
                           docs_por_item=docs_por_item,
                           completados=completados, total=len(activos), pct=pct)

@app.route('/obra/<int:obra_id>/item/<item_code>', methods=['GET','POST'])
def item_action(obra_id, item_code):
    db       = get_db()
    obra_row = db.execute('SELECT * FROM obras WHERE id=?', (obra_id,)).fetchone()
    item     = next((i for i in ITEMS if i[0] == item_code), None)
    if not obra_row or not item:
        db.close(); return redirect(url_for('index'))
    tipo = item[2]
    today = datetime.today().strftime('%Y-%m-%d')

    if tipo == 'no_aplica':
        db.close()
        flash('Este item no aplica por ahora', 'warning')
        return redirect(url_for('obra', obra_id=obra_id))

    if tipo == 'desde_iperc':
        docs_iperc = db.execute(
            'SELECT * FROM documentos WHERE obra_id=? AND item_code="1.1" ORDER BY uploaded_at DESC',
            (obra_id,)).fetchall()
        registros = [{'doc': d, 'datos': json.loads(d['datos_json'])}
                     for d in docs_iperc if d['datos_json']]
        db.close()
        return render_template('desde_iperc.html', obra=obra_row, item=item, registros=registros)

    if request.method == 'POST':
        if tipo == 'formulario_iperc':
            trabajadores = []
            for i in range(1,10):
                n = request.form.get(f'trabajador_{i}','').strip()
                if n:
                    trabajadores.append({'hora': request.form.get(f'hora_{i}',''), 'nombre': n})
            peligros = []
            for i in range(25):
                p = request.form.get(f'peligro_{i}','').strip()
                if not p: continue
                peligros.append({
                    'peligro': p,
                    'riesgo':        request.form.get(f'riesgo_{i}',''),
                    'nivel_antes':   request.form.get(f'nivel_antes_{i}',''),
                    'medidas':       request.form.get(f'medidas_{i}',''),
                    'nivel_despues': request.form.get(f'nivel_despues_{i}',''),
                })
            datos = {
                'area': request.form.get('area',''), 'zona': request.form.get('zona',''),
                'turno': request.form.get('turno',''), 'fecha': request.form.get('fecha',''),
                'labor': request.form.get('labor',''), 'actividad': request.form.get('actividad',''),
                'trabajadores': trabajadores, 'peligros': peligros,
                'secuencia': request.form.get('secuencia',''),
                'supervisor': request.form.get('supervisor',''),
                'medida_correctiva': request.form.get('medida_correctiva',''),
            }
            pdf_name = f"iperc_{uuid.uuid4().hex[:8]}.pdf"
            generar_iperc_pdf(datos, os.path.join(PDF_FOLDER, pdf_name))
            db.execute(
                'INSERT INTO documentos (obra_id,item_code,tipo,datos_json,pdf_filename,fecha,descripcion) VALUES (?,?,?,?,?,?,?)',
                (obra_id, item_code, tipo, json.dumps(datos), pdf_name,
                 datos['fecha'], f"IPERC – {datos['actividad'][:50]}"))
            db.commit(); db.close()
            flash('IPERC guardado y PDF generado correctamente', 'success')
            return redirect(url_for('obra', obra_id=obra_id))

        elif tipo == 'formulario_petar':
            personal = []
            for i in range(1,10):
                n = request.form.get(f'personal_{i}','').strip()
                if n:
                    personal.append({'ocupacion': request.form.get(f'ocupacion_{i}',''), 'nombre': n})
            epp_keys = ['casco_barbiquejo','arnes_cuerpo_entero','mameluco','correa_lampara',
                        'guantes_jebe','morral_lona','botas_jebe','protector_oidos',
                        'respirador','linea_anclaje','protector_visual','correa_antitrauma']
            datos = {
                'area': request.form.get('area',''), 'lugar': request.form.get('lugar',''),
                'fecha': request.form.get('fecha',''), 'hora_inicio': request.form.get('hora_inicio',''),
                'hora_final': request.form.get('hora_final',''), 'numero': request.form.get('numero',''),
                'cert_medica': request.form.get('cert_medica','no'),
                'cap_altura':  request.form.get('cap_altura','no'),
                'trab_calificados': request.form.get('trab_calificados','no'),
                'descripcion_trabajo': request.form.get('descripcion_trabajo',''),
                'herramientas': request.form.get('herramientas',''),
                'procedimiento': request.form.get('procedimiento',''),
                'supervisor_nombre': request.form.get('supervisor_nombre',''),
                'supervisor_cip':    request.form.get('supervisor_cip',''),
                'jefe_nombre': request.form.get('jefe_nombre',''),
                'personal': personal,
                'epp': [k for k in epp_keys if request.form.get(f'epp_{k}')],
            }
            pdf_name = f"petar_{uuid.uuid4().hex[:8]}.pdf"
            generar_petar_pdf(datos, os.path.join(PDF_FOLDER, pdf_name))
            db.execute(
                'INSERT INTO documentos (obra_id,item_code,tipo,datos_json,pdf_filename,fecha,descripcion) VALUES (?,?,?,?,?,?,?)',
                (obra_id, item_code, tipo, json.dumps(datos), pdf_name,
                 datos['fecha'], f"PETAR N°{datos['numero']} – {datos['lugar']}"))
            db.commit(); db.close()
            flash('PETAR guardado y PDF generado correctamente', 'success')
            return redirect(url_for('obra', obra_id=obra_id))

        elif tipo == 'formulario_arnes':
            arnes_subs = ['1.1','1.2','1.3','1.4','1.5','1.6']
            linea_subs = ['2.1','2.2','2.3','2.4','2.5']
            block_subs = ['3.1','3.2','3.3','3.4','3.5','3.6']
            datos = {
                'fecha': request.form.get('fecha',''), 'area': request.form.get('area',''),
                'supervisor': request.form.get('supervisor',''),
                'codigo_arnes': request.form.get('codigo_arnes',''),
                'codigo_linea': request.form.get('codigo_linea',''),
                'codigo_block': request.form.get('codigo_block',''),
                'observaciones':    request.form.get('observaciones',''),
                'recomendaciones':  request.form.get('recomendaciones',''),
                'realizado_nombre': request.form.get('realizado_nombre',''),
                'realizado_cargo':  request.form.get('realizado_cargo',''),
                'revisado_nombre':  request.form.get('revisado_nombre',''),
                'revisado_cargo':   request.form.get('revisado_cargo',''),
                'items_arnes': {s: request.form.get(f'arnes_{s}','') for s in arnes_subs},
                'items_linea': {s: request.form.get(f'linea_{s}','') for s in linea_subs},
                'items_block': {s: request.form.get(f'block_{s}','') for s in block_subs},
            }
            pdf_name = f"arnes_{uuid.uuid4().hex[:8]}.pdf"
            generar_checklist_pdf(datos, os.path.join(PDF_FOLDER, pdf_name))
            db.execute(
                'INSERT INTO documentos (obra_id,item_code,tipo,datos_json,pdf_filename,fecha,descripcion) VALUES (?,?,?,?,?,?,?)',
                (obra_id, item_code, tipo, json.dumps(datos), pdf_name,
                 datos['fecha'], f"Check List Arnés – {datos['supervisor']}"))
            db.commit(); db.close()
            flash('Check List guardado y PDF generado correctamente', 'success')
            return redirect(url_for('obra', obra_id=obra_id))

        elif tipo in ('subir_foto','subir_pdf','subir_foto_pdf'):
            file  = request.files.get('archivo')
            fecha = request.form.get('fecha', today)
            desc  = request.form.get('descripcion','')
            if file and file.filename:
                ext   = file.filename.rsplit('.',1)[1].lower()
                uname = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, uname))
                db.execute(
                    'INSERT INTO documentos (obra_id,item_code,tipo,filename,original_name,fecha,descripcion) VALUES (?,?,?,?,?,?,?)',
                    (obra_id, item_code, tipo, uname, file.filename, fecha, desc))
                db.commit(); db.close()
                flash('Archivo subido correctamente', 'success')
                return redirect(url_for('obra', obra_id=obra_id))
            flash('Por favor selecciona un archivo', 'danger')

    db.close()
    tmpl = FORM_TEMPLATES.get(tipo, 'item_form.html')
    return render_template(tmpl, obra=obra_row, item=item, tipo=tipo, today=today)

@app.route('/pdf/<filename>')
def ver_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/obra/<int:obra_id>/eliminar/<int:doc_id>', methods=['POST'])
def eliminar_doc(obra_id, doc_id):
    db  = get_db()
    doc = db.execute('SELECT * FROM documentos WHERE id=? AND obra_id=?', (doc_id, obra_id)).fetchone()
    if doc:
        for f, folder in [(doc['filename'], UPLOAD_FOLDER),(doc['pdf_filename'], PDF_FOLDER)]:
            if f:
                try: os.remove(os.path.join(folder, f))
                except: pass
        db.execute('DELETE FROM documentos WHERE id=?', (doc_id,))
        db.commit()
        flash('Documento eliminado', 'success')
    db.close()
    return redirect(url_for('obra', obra_id=obra_id))

init_db()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
