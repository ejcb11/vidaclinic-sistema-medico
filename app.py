# ==============================================================================
# VidaClinic — Sistema Integral de Gestión Hospitalaria y Consulta Médica
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

"""Servidor web principal."""

import os
import hashlib
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, send_file, jsonify, send_from_directory
)

from database.db import (
    get_db_connection, get_dashboard_kpis, get_chart_data,
    get_cargos, insert_cargo, get_especialidades, insert_especialidad,
    get_doctores, get_doctor, insert_doctor, update_doctor,
    get_pacientes, get_paciente, get_paciente_by_cedula, insert_paciente, update_paciente,
    get_citas, get_cita, insert_cita, atender_cita, cancelar_cita, check_cita_collision,
    get_dividendos_por_doctor, get_citas_pendientes_pago_doctor, generar_liquidacion_pago,
    get_liquidaciones, get_liquidacion, get_user_by_username
)
from database.init_db import init_database
from validators import (
    validate_letters_only, validate_cedula, validate_email, 
    validate_phone, validate_percentage, validate_amount, 
    validate_ailment, validate_appointment_date
)
from reports import (
    generate_citas_excel, generate_liquidaciones_excel, generate_pacientes_excel,
    generate_citas_pdf, generate_recibo_cita_pdf, generate_recibo_liquidacion_pdf
)
from bcv import get_tasa_bcv, usd_to_bs, format_bs

app = Flask(__name__)
app.secret_key = 'vidaclinic_super_secret_key_2026'

# Garantizar base de datos inicializada
_db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'vidaclinic.db')
if not os.path.exists(_db_file):
    init_database(reset=False)

# Filtros personalizados de Jinja para conversión de monedas
@app.template_filter('to_bs')
def to_bs_filter(amount_usd, tasa=None):
    bs_val = usd_to_bs(amount_usd, tasa)
    return format_bs(bs_val)

@app.template_filter('usd_to_bs_val')
def usd_to_bs_val_filter(amount_usd, tasa=None):
    return usd_to_bs(amount_usd, tasa)

# Decoradores
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debe iniciar sesión para acceder al sistema.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'Administrador':
            flash("Acceso restringido: Esta sección requiere rol de Administrador.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Variables globales para plantillas
@app.context_processor
def inject_global_data():
    tasa_data = get_tasa_bcv()
    return {
        'current_user': session.get('user_name', 'Invitado'),
        'current_role': session.get('role', 'Invitado'),
        'is_admin': session.get('role') == 'Administrador',
        'is_patient': session.get('role') == 'Paciente',
        'current_patient_id': session.get('patient_id'),
        'today_date': date.today().isoformat(),
        'tasa_bcv': tasa_data,
        'usd_to_bs': usd_to_bs,
        'format_bs': format_bs
    }

# API pública para obtener tasa BCV
@app.route('/api/tasa-bcv')
def api_tasa_bcv():
    refresh = request.args.get('refresh') == '1'
    return jsonify(get_tasa_bcv(force_refresh=refresh))

# Agendamiento público
@app.route('/agendar-cita', methods=['GET', 'POST'])
def agendar_cita_publico():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        cedula = request.form.get('cedula', '').strip()
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip() or '2000-01-01'
        genero = request.form.get('genero', 'Femenino')
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        direccion = request.form.get('direccion', '').strip()
        grupo_sanguineo = request.form.get('grupo_sanguineo', 'O+')

        doctor_id = request.form.get('doctor_id', type=int)
        fecha = request.form.get('fecha', '').strip()
        hora = request.form.get('hora', '').strip()
        padecimiento = request.form.get('padecimiento', '').strip()

        ok_nom, err_nom = validate_letters_only(nombre, "Nombre")
        if not ok_nom:
            flash(err_nom, "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_ape, err_ape = validate_letters_only(apellido, "Apellido")
        if not ok_ape:
            flash(err_ape, "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_ced, err_ced = validate_cedula(cedula)
        if not ok_ced:
            flash(err_ced, "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_tel, err_tel = validate_phone(telefono)
        if not ok_tel:
            flash(err_tel, "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_mail, err_mail = validate_email(email)
        if not ok_mail:
            flash(err_mail, "danger")
            return redirect(url_for('agendar_cita_publico'))

        if not doctor_id:
            flash("Debe seleccionar un médico tratante.", "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_date, err_date = validate_appointment_date(fecha)
        if not ok_date:
            flash(err_date, "danger")
            return redirect(url_for('agendar_cita_publico'))

        if not hora:
            flash("Especifique la hora deseada para su consulta.", "danger")
            return redirect(url_for('agendar_cita_publico'))

        ok_ail, err_ail = validate_ailment(padecimiento)
        if not ok_ail:
            flash(err_ail, "danger")
            return redirect(url_for('agendar_cita_publico'))

        if check_cita_collision(doctor_id, fecha, hora):
            flash("El médico seleccionado ya tiene una cita ocupada en esa fecha y horario. Por favor seleccione otro turno.", "warning")
            return redirect(url_for('agendar_cita_publico'))

        paciente = get_paciente_by_cedula(cedula)
        if paciente:
            paciente_id = paciente['id']
            update_paciente(paciente_id, nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo)
        else:
            paciente_id = insert_paciente(nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo)

        try:
            cita_id = insert_cita(paciente_id, doctor_id, fecha, hora, padecimiento)
            flash("¡Su cita médica ha sido agendada con éxito!", "success")
            return redirect(url_for('cita_confirmada', id=cita_id))
        except Exception as e:
            flash(f"Error al procesar la cita: {str(e)}", "danger")
            return redirect(url_for('agendar_cita_publico'))

    doctores = get_doctores(solo_activos=True)
    especialidades = get_especialidades()
    return render_template('citas/agendar_publico.html', doctores=doctores, especialidades=especialidades)

@app.route('/cita-confirmada/<int:id>')
def cita_confirmada(id):
    cita = get_cita(id)
    if not cita:
        flash("La cita solicitada no fue encontrada.", "danger")
        return redirect(url_for('login'))
    return render_template('citas/confirmacion_publica.html', cita=cita)

@app.route('/cita-publica/<int:id>/pdf')
def cita_publica_pdf(id):
    cita = get_cita(id)
    if not cita:
        flash("Cita no encontrada.", "danger")
        return redirect(url_for('login'))
    pdf_buffer = generate_recibo_cita_pdf(cita)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Comprobante_Cita_{cita['codigo']}.pdf"
    )

# Autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = get_user_by_username(username)
        if user:
            pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if user['password_hash'] == pwd_hash:
                if user['rol'] != 'Administrador':
                    flash("Acceso restringido: Este panel es exclusivo para personal administrativo. Los pacientes pueden agendar citas desde el banner inferior.", "warning")
                    return redirect(url_for('login'))

                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_name'] = user['nombre_completo']
                session['role'] = user['rol']
                session['patient_id'] = user['paciente_id']
                flash("¡Bienvenido! Sesión de Administrador iniciada con éxito.", "success")
                return redirect(url_for('dashboard'))

        flash("Credenciales incorrectas. Verifique su usuario y contraseña.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión satisfactoriamente.", "info")
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
@app.route('/dashboard')
@admin_required
def dashboard():
    kpis = get_dashboard_kpis()
    chart_data = get_chart_data()
    ultimas_citas = get_citas()[:8]
    dividendos_resumen = get_dividendos_por_doctor()
    return render_template('dashboard.html', kpis=kpis, chart_data=chart_data, ultimas_citas=ultimas_citas, dividendos_resumen=dividendos_resumen)

# Citas médicas
@app.route('/citas')
@login_required
def citas_index():
    paciente_filter = session.get('patient_id') if session.get('role') == 'Paciente' else None
    doctor_filter = request.args.get('doctor_id', type=int)
    estado_filter = request.args.get('estado')
    fecha_filter = request.args.get('fecha')

    citas = get_citas(doctor_id=doctor_filter, paciente_id=paciente_filter, estado=estado_filter, fecha=fecha_filter)
    doctores = get_doctores(solo_activos=True)
    pacientes = get_pacientes()
    especialidades = get_especialidades()

    return render_template(
        'citas/index.html',
        citas=citas,
        doctores=doctores,
        pacientes=pacientes,
        especialidades=especialidades,
        selected_doctor=doctor_filter,
        selected_estado=estado_filter,
        selected_fecha=fecha_filter
    )

@app.route('/citas/nueva', methods=['POST'])
@login_required
def citas_nueva():
    paciente_id = session.get('patient_id') if session.get('role') == 'Paciente' else request.form.get('paciente_id', type=int)
    doctor_id = request.form.get('doctor_id', type=int)
    fecha = request.form.get('fecha', '').strip()
    hora = request.form.get('hora', '').strip()
    padecimiento = request.form.get('padecimiento', '').strip()

    if not paciente_id:
        flash("Debe seleccionar un paciente.", "danger")
        return redirect(url_for('citas_index'))

    if not doctor_id:
        flash("Debe seleccionar un médico tratante.", "danger")
        return redirect(url_for('citas_index'))

    ok_date, err_date = validate_appointment_date(fecha)
    if not ok_date:
        flash(err_date, "danger")
        return redirect(url_for('citas_index'))

    if not hora:
        flash("Debe especificar la hora de la cita.", "danger")
        return redirect(url_for('citas_index'))

    ok_ailment, err_ailment = validate_ailment(padecimiento)
    if not ok_ailment:
        flash(err_ailment, "danger")
        return redirect(url_for('citas_index'))

    if check_cita_collision(doctor_id, fecha, hora):
        flash("El médico seleccionado ya tiene una cita agendada en esa misma fecha y hora. Por favor elija otro horario.", "warning")
        return redirect(url_for('citas_index'))

    try:
        insert_cita(paciente_id, doctor_id, fecha, hora, padecimiento)
        flash("¡Cita médica agendada exitosamente!", "success")
    except Exception as e:
        flash(f"Error al agendar cita: {str(e)}", "danger")

    return redirect(url_for('citas_index'))

@app.route('/citas/<int:id>/atender', methods=['POST'])
@login_required
def citas_atender(id):
    diagnostico = request.form.get('diagnostico', '').strip()
    atender_cita(id, diagnostico)
    flash("La consulta médica ha sido marcada como ATENDIDA. El dividendo médico ha quedado registrado.", "success")
    return redirect(url_for('citas_index'))

@app.route('/citas/<int:id>/cancelar', methods=['POST'])
@login_required
def citas_cancelar(id):
    cancelar_cita(id)
    flash("La cita ha sido cancelada.", "info")
    return redirect(url_for('citas_index'))

@app.route('/citas/<int:id>/recibo')
@login_required
def citas_recibo(id):
    cita = get_cita(id)
    if not cita:
        flash("Cita no encontrada.", "danger")
        return redirect(url_for('citas_index'))
    return render_template('citas/recibo.html', cita=cita)

@app.route('/citas/<int:id>/pdf')
@login_required
def citas_recibo_pdf(id):
    cita = get_cita(id)
    if not cita:
        flash("Cita no encontrada.", "danger")
        return redirect(url_for('citas_index'))
    pdf_buffer = generate_recibo_cita_pdf(cita)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Comprobante_Cita_{cita['codigo']}.pdf"
    )

# Médicos y cargos
@app.route('/medicos')
@admin_required
def medicos_index():
    doctores = get_doctores()
    cargos = get_cargos()
    especialidades = get_especialidades()
    return render_template('medicos/index.html', doctores=doctores, cargos=cargos, especialidades=especialidades)

@app.route('/medicos/nuevo', methods=['POST'])
@admin_required
def medicos_nuevo():
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    cedula = request.form.get('cedula', '').strip()
    especialidad_id = request.form.get('especialidad_id', type=int)
    cargo_id = request.form.get('cargo_id', type=int)
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()
    honorario = request.form.get('honorario_consulta')
    porcentaje = request.form.get('porcentaje_dividendo')

    ok_nom, err_nom = validate_letters_only(nombre, "Nombre del médico")
    if not ok_nom:
        flash(err_nom, "danger")
        return redirect(url_for('medicos_index'))

    ok_ape, err_ape = validate_letters_only(apellido, "Apellido del médico")
    if not ok_ape:
        flash(err_ape, "danger")
        return redirect(url_for('medicos_index'))

    ok_ced, err_ced = validate_cedula(cedula)
    if not ok_ced:
        flash(err_ced, "danger")
        return redirect(url_for('medicos_index'))

    ok_tel, err_tel = validate_phone(telefono)
    if not ok_tel:
        flash(err_tel, "danger")
        return redirect(url_for('medicos_index'))

    ok_mail, err_mail = validate_email(email)
    if not ok_mail:
        flash(err_mail, "danger")
        return redirect(url_for('medicos_index'))

    ok_hon, err_hon = validate_amount(honorario, "Honorario de consulta")
    if not ok_hon:
        flash(err_hon, "danger")
        return redirect(url_for('medicos_index'))

    ok_pct, err_pct = validate_percentage(porcentaje, "Porcentaje de dividendo (p/c)")
    if not ok_pct:
        flash(err_pct, "danger")
        return redirect(url_for('medicos_index'))

    try:
        insert_doctor(nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario, porcentaje)
        flash(f"Dr(a). {nombre} {apellido} registrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al registrar médico: {str(e)}", "danger")

    return redirect(url_for('medicos_index'))

@app.route('/medicos/<int:id>/editar', methods=['POST'])
@admin_required
def medicos_editar(id):
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    cedula = request.form.get('cedula', '').strip()
    especialidad_id = request.form.get('especialidad_id', type=int)
    cargo_id = request.form.get('cargo_id', type=int)
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()
    honorario = request.form.get('honorario_consulta')
    porcentaje = request.form.get('porcentaje_dividendo')
    estado = request.form.get('estado', 'Activo')

    ok_nom, err_nom = validate_letters_only(nombre, "Nombre del médico")
    if not ok_nom:
        flash(err_nom, "danger")
        return redirect(url_for('medicos_index'))

    ok_ape, err_ape = validate_letters_only(apellido, "Apellido del médico")
    if not ok_ape:
        flash(err_ape, "danger")
        return redirect(url_for('medicos_index'))

    update_doctor(id, nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario, porcentaje, estado)
    flash("Información del médico actualizada satisfactoriamente.", "success")
    return redirect(url_for('medicos_index'))

@app.route('/cargos/nuevo', methods=['POST'])
@admin_required
def cargos_nuevo():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    ok_nom, err_nom = validate_letters_only(nombre, "Nombre del cargo")
    if not ok_nom:
        flash(err_nom, "danger")
        return redirect(url_for('medicos_index'))

    try:
        insert_cargo(nombre, descripcion)
        flash("Nuevo cargo institucional creado con éxito.", "success")
    except Exception as e:
        flash(f"Error al crear cargo: {str(e)}", "danger")
    return redirect(url_for('medicos_index'))

@app.route('/especialidades/nueva', methods=['POST'])
@admin_required
def especialidades_nueva():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    costo_base = request.form.get('costo_base', '50.0')

    ok_nom, err_nom = validate_letters_only(nombre, "Nombre de la especialidad")
    if not ok_nom:
        flash(err_nom, "danger")
        return redirect(url_for('medicos_index'))

    try:
        insert_especialidad(nombre, descripcion, costo_base)
        flash("Especialidad médica registrada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al registrar especialidad: {str(e)}", "danger")
    return redirect(url_for('medicos_index'))

# Pacientes
@app.route('/pacientes')
@login_required
def pacientes_index():
    pacientes = get_pacientes()
    return render_template('pacientes/index.html', pacientes=pacientes)

@app.route('/pacientes/nuevo', methods=['POST'])
@login_required
def pacientes_nuevo():
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    cedula = request.form.get('cedula', '').strip()
    fecha_nac = request.form.get('fecha_nacimiento', '').strip()
    genero = request.form.get('genero', 'Femenino')
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()
    direccion = request.form.get('direccion', '').strip()
    grupo_sangre = request.form.get('grupo_sanguineo', 'O+')

    ok_nom, err_nom = validate_letters_only(nombre, "Nombre del paciente")
    if not ok_nom:
        flash(err_nom, "danger")
        return redirect(url_for('pacientes_index'))

    ok_ape, err_ape = validate_letters_only(apellido, "Apellido del paciente")
    if not ok_ape:
        flash(err_ape, "danger")
        return redirect(url_for('pacientes_index'))

    ok_ced, err_ced = validate_cedula(cedula)
    if not ok_ced:
        flash(err_ced, "danger")
        return redirect(url_for('pacientes_index'))

    ok_tel, err_tel = validate_phone(telefono)
    if not ok_tel:
        flash(err_tel, "danger")
        return redirect(url_for('pacientes_index'))

    ok_mail, err_mail = validate_email(email)
    if not ok_mail:
        flash(err_mail, "danger")
        return redirect(url_for('pacientes_index'))

    try:
        insert_paciente(nombre, apellido, cedula, fecha_nac, genero, telefono, email, direccion, grupo_sangre)
        flash(f"Paciente {nombre} {apellido} registrado(a) exitosamente.", "success")
    except Exception as e:
        flash(f"Error al registrar paciente: {str(e)}", "danger")

    return redirect(url_for('pacientes_index'))

# Dividendos y liquidaciones
@app.route('/dividendos')
@admin_required
def dividendos_index():
    doctor_selected_id = request.args.get('doctor_id', type=int)
    dividendos_doctores = get_dividendos_por_doctor()
    liquidaciones = get_liquidaciones()

    citas_pendientes = []
    doctor_activo = None
    if doctor_selected_id:
        citas_pendientes = get_citas_pendientes_pago_doctor(doctor_selected_id)
        doctor_activo = get_doctor(doctor_selected_id)

    return render_template(
        'dividendos/index.html',
        dividendos_doctores=dividendos_doctores,
        liquidaciones=liquidaciones,
        citas_pendientes=citas_pendientes,
        doctor_activo=doctor_activo,
        doctor_selected_id=doctor_selected_id
    )

@app.route('/liquidaciones/nueva', methods=['POST'])
@admin_required
def liquidaciones_nueva():
    doctor_id = request.form.get('doctor_id', type=int)
    citas_ids = request.form.getlist('citas_ids', type=int)
    metodo_pago = request.form.get('metodo_pago', 'Transferencia Bancaria')
    numero_referencia = request.form.get('numero_referencia', '').strip()
    observaciones = request.form.get('observaciones', '').strip()

    if not doctor_id:
        flash("Seleccione un médico.", "danger")
        return redirect(url_for('dividendos_index'))

    if not citas_ids:
        flash("Debe seleccionar al menos una consulta médica atendida para liquidar.", "warning")
        return redirect(url_for('dividendos_index', doctor_id=doctor_id))

    try:
        liq_id = generar_liquidacion_pago(doctor_id, citas_ids, metodo_pago, numero_referencia, observaciones)
        flash("¡Pago a médico y liquidación de dividendos procesada exitosamente!", "success")
        return redirect(url_for('liquidaciones_recibo', id=liq_id))
    except Exception as e:
        flash(f"Error al generar pago: {str(e)}", "danger")
        return redirect(url_for('dividendos_index', doctor_id=doctor_id))

@app.route('/liquidaciones/<int:id>/recibo')
@admin_required
def liquidaciones_recibo(id):
    liq = get_liquidacion(id)
    if not liq:
        flash("Comprobante de liquidación no encontrado.", "danger")
        return redirect(url_for('dividendos_index'))
    return render_template('dividendos/recibo_pago.html', liq=liq)

@app.route('/liquidaciones/<int:id>/pdf')
@admin_required
def liquidaciones_recibo_pdf(id):
    liq = get_liquidacion(id)
    if not liq:
        flash("Comprobante no encontrado.", "danger")
        return redirect(url_for('dividendos_index'))
    pdf_buffer = generate_recibo_liquidacion_pdf(liq)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Comprobante_Pago_{liq['numero_comprobante']}.pdf"
    )

# Reportes
@app.route('/reportes')
@login_required
def reportes_index():
    kpis = get_dashboard_kpis()
    return render_template('reportes/index.html', kpis=kpis)

@app.route('/reportes/citas/excel')
@login_required
def reportes_citas_excel():
    paciente_id = session.get('patient_id') if session.get('role') == 'Paciente' else None
    citas = get_citas(paciente_id=paciente_id)
    excel_buffer = generate_citas_excel(citas)
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"Reporte_Citas_{date.today().isoformat()}.xlsx"
    )

@app.route('/reportes/citas/pdf')
@login_required
def reportes_citas_pdf():
    paciente_id = session.get('patient_id') if session.get('role') == 'Paciente' else None
    citas = get_citas(paciente_id=paciente_id)
    pdf_buffer = generate_citas_pdf(citas)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Reporte_Citas_{date.today().isoformat()}.pdf"
    )

@app.route('/reportes/liquidaciones/excel')
@admin_required
def reportes_liquidaciones_excel():
    liquidaciones = get_liquidaciones()
    excel_buffer = generate_liquidaciones_excel(liquidaciones)
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"Reporte_Liquidaciones_Medicos_{date.today().isoformat()}.xlsx"
    )

@app.route('/reportes/pacientes/excel')
@admin_required
def reportes_pacientes_excel():
    pacientes = get_pacientes()
    excel_buffer = generate_pacientes_excel(pacientes)
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"Padron_Pacientes_{date.today().isoformat()}.xlsx"
    )

# Base de datos
@app.route('/database')
@admin_required
def database_index():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'vidaclinic.db')
    size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    size_kb = round(size_bytes / 1024, 2)
    kpis = get_dashboard_kpis()
    return render_template('db_admin/index.html', size_kb=size_kb, kpis=kpis)

@app.route('/database/download-db')
@admin_required
def database_download():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'vidaclinic.db')
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f"Backup_vidaclinic_{date.today().isoformat()}.db"
    )

@app.route('/database/reset-demo', methods=['POST'])
@admin_required
def database_reset():
    init_database(reset=True)
    flash("Base de datos reiniciada a los datos de demostración.", "success")
    return redirect(url_for('database_index'))

if __name__ == '__main__':
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'vidaclinic.db')
    if not os.path.exists(db_file):
        init_database(reset=False)
    
    app.run(host='127.0.0.1', port=5000, debug=True)
