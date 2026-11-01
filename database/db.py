# ==============================================================================
# VidaClinic — Capa de Acceso a Datos (DAO SQLite3)
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

"""Acceso a datos y operaciones SQLite3."""

import sqlite3
import os
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vidaclinic.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        if return_id:
            return cur.lastrowid
        return cur.rowcount
    finally:
        conn.close()

# Dashboard y KPIs
def get_dashboard_kpis():
    today = date.today().isoformat()
    
    total_pacientes = query_db("SELECT COUNT(*) AS total FROM pacientes", one=True)['total']
    total_doctores = query_db("SELECT COUNT(*) AS total FROM doctores WHERE estado = 'Activo'", one=True)['total']
    citas_hoy = query_db("SELECT COUNT(*) AS total FROM citas WHERE fecha = ?", (today,), one=True)['total']
    citas_totales = query_db("SELECT COUNT(*) AS total FROM citas", one=True)['total']
    citas_atendidas = query_db("SELECT COUNT(*) AS total FROM citas WHERE estado = 'Atendida'", one=True)['total']
    
    ingresos = query_db("""
        SELECT 
            COALESCE(SUM(costo_consulta), 0) AS ingresos_totales,
            COALESCE(SUM(monto_doctor), 0) AS total_dividendos_doctores,
            COALESCE(SUM(monto_clinica), 0) AS total_ganancia_clinica
        FROM citas
        WHERE estado = 'Atendida'
    """, one=True)
    
    dividendos_pendientes = query_db("""
        SELECT COALESCE(SUM(monto_doctor), 0) AS total 
        FROM citas 
        WHERE estado = 'Atendida' AND estado_pago_medico = 'Pendiente'
    """, one=True)['total']

    dividendos_liquidados = query_db("""
        SELECT COALESCE(SUM(monto_dividendo_doctor), 0) AS total 
        FROM liquidaciones_pago
    """, one=True)['total']

    return {
        'total_pacientes': total_pacientes,
        'total_doctores': total_doctores,
        'citas_hoy': citas_hoy,
        'citas_totales': citas_totales,
        'citas_atendidas': citas_atendidas,
        'ingresos_totales': ingresos['ingresos_totales'],
        'total_dividendos_doctores': ingresos['total_dividendos_doctores'],
        'total_ganancia_clinica': ingresos['total_ganancia_clinica'],
        'dividendos_pendientes': dividendos_pendientes,
        'dividendos_liquidados': dividendos_liquidados
    }

def get_chart_data():
    citas_por_esp = query_db("""
        SELECT e.nombre, COUNT(c.id) AS cantidad
        FROM especialidades e
        LEFT JOIN citas c ON e.id = c.especialidad_id
        GROUP BY e.id, e.nombre
        ORDER BY cantidad DESC
    """)
    
    estados_citas = query_db("""
        SELECT estado, COUNT(*) AS cantidad
        FROM citas
        GROUP BY estado
    """)

    return {
        'especialidades_labels': [row['nombre'] for row in citas_por_esp],
        'especialidades_data': [row['cantidad'] for row in citas_por_esp],
        'estados_labels': [row['estado'] for row in estados_citas],
        'estados_data': [row['cantidad'] for row in estados_citas]
    }

# Cargos y especialidades
def get_cargos():
    return query_db("SELECT * FROM cargos ORDER BY nombre ASC")

def get_cargo(id):
    return query_db("SELECT * FROM cargos WHERE id = ?", (id,), one=True)

def insert_cargo(nombre, descripcion):
    return execute_db("INSERT INTO cargos (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion), return_id=True)

def get_especialidades():
    return query_db("SELECT * FROM especialidades ORDER BY nombre ASC")

def get_especialidad(id):
    return query_db("SELECT * FROM especialidades WHERE id = ?", (id,), one=True)

def insert_especialidad(nombre, descripcion, costo_base):
    return execute_db(
        "INSERT INTO especialidades (nombre, descripcion, costo_base) VALUES (?, ?, ?)",
        (nombre, descripcion, float(costo_base)),
        return_id=True
    )

# Doctores
def get_doctores(solo_activos=False):
    sql = """
        SELECT d.*, e.nombre AS especialidad_nombre, c.nombre AS cargo_nombre
        FROM doctores d
        JOIN especialidades e ON d.especialidad_id = e.id
        JOIN cargos c ON d.cargo_id = c.id
    """
    if solo_activos:
        sql += " WHERE d.estado = 'Activo'"
    sql += " ORDER BY d.apellido ASC, d.nombre ASC"
    return query_db(sql)

def get_doctor(id):
    return query_db("""
        SELECT d.*, e.nombre AS especialidad_nombre, c.nombre AS cargo_nombre
        FROM doctores d
        JOIN especialidades e ON d.especialidad_id = e.id
        JOIN cargos c ON d.cargo_id = c.id
        WHERE d.id = ?
    """, (id,), one=True)

def insert_doctor(nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario_consulta, porcentaje_dividendo, estado='Activo'):
    return execute_db("""
        INSERT INTO doctores (nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario_consulta, porcentaje_dividendo, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, float(honorario_consulta), float(porcentaje_dividendo), estado), return_id=True)

def update_doctor(id, nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario_consulta, porcentaje_dividendo, estado):
    return execute_db("""
        UPDATE doctores
        SET nombre = ?, apellido = ?, cedula = ?, especialidad_id = ?, cargo_id = ?, telefono = ?, email = ?, honorario_consulta = ?, porcentaje_dividendo = ?, estado = ?
        WHERE id = ?
    """, (nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, float(honorario_consulta), float(porcentaje_dividendo), estado, id))

# Pacientes
def get_pacientes():
    return query_db("SELECT * FROM pacientes ORDER BY apellido ASC, nombre ASC")

def get_paciente(id):
    return query_db("SELECT * FROM pacientes WHERE id = ?", (id,), one=True)

def get_paciente_by_cedula(cedula):
    return query_db("SELECT * FROM pacientes WHERE cedula = ?", (cedula,), one=True)

def insert_paciente(nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo):
    return execute_db("""
        INSERT INTO pacientes (nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo), return_id=True)

def update_paciente(id, nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo):
    return execute_db("""
        UPDATE pacientes
        SET nombre = ?, apellido = ?, cedula = ?, fecha_nacimiento = ?, genero = ?, telefono = ?, email = ?, direccion = ?, grupo_sanguineo = ?
        WHERE id = ?
    """, (nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo, id))

# Citas médicas
def get_citas(doctor_id=None, paciente_id=None, estado=None, fecha=None):
    sql = """
        SELECT 
            c.*, 
            p.nombre AS paciente_nombre, p.apellido AS paciente_apellido, p.cedula AS paciente_cedula, p.telefono AS paciente_telefono,
            d.nombre AS doctor_nombre, d.apellido AS doctor_apellido,
            e.nombre AS especialidad_nombre
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN doctores d ON c.doctor_id = d.id
        JOIN especialidades e ON c.especialidad_id = e.id
        WHERE 1=1
    """
    params = []
    if doctor_id:
        sql += " AND c.doctor_id = ?"
        params.append(doctor_id)
    if paciente_id:
        sql += " AND c.paciente_id = ?"
        params.append(paciente_id)
    if estado:
        sql += " AND c.estado = ?"
        params.append(estado)
    if fecha:
        sql += " AND c.fecha = ?"
        params.append(fecha)

    sql += " ORDER BY c.fecha DESC, c.hora DESC"
    return query_db(sql, params)

def get_cita(id):
    return query_db("""
        SELECT 
            c.*, 
            p.nombre AS paciente_nombre, p.apellido AS paciente_apellido, p.cedula AS paciente_cedula, p.telefono AS paciente_telefono, p.email AS paciente_email, p.direccion AS paciente_direccion,
            d.nombre AS doctor_nombre, d.apellido AS doctor_apellido, d.cedula AS doctor_cedula, d.telefono AS doctor_telefono,
            e.nombre AS especialidad_nombre,
            lp.numero_comprobante AS liquidacion_comprobante, lp.fecha_pago AS liquidacion_fecha
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN doctores d ON c.doctor_id = d.id
        JOIN especialidades e ON c.especialidad_id = e.id
        LEFT JOIN liquidaciones_pago lp ON c.liquidacion_id = lp.id
        WHERE c.id = ?
    """, (id,), one=True)

def check_cita_collision(doctor_id, fecha, hora, exclude_cita_id=None):
    sql = """
        SELECT COUNT(*) AS total 
        FROM citas 
        WHERE doctor_id = ? AND fecha = ? AND hora = ? AND estado != 'Cancelada'
    """
    params = [doctor_id, fecha, hora]
    if exclude_cita_id:
        sql += " AND id != ?"
        params.append(exclude_cita_id)
    res = query_db(sql, params, one=True)
    return res['total'] > 0

def insert_cita(paciente_id, doctor_id, fecha, hora, padecimiento):
    doctor = get_doctor(doctor_id)
    if not doctor:
        raise ValueError("Médico no encontrado")

    count = query_db("SELECT COUNT(*) AS total FROM citas", one=True)['total']
    codigo = f"CIT-{1000 + count + 1}"

    costo = float(doctor['honorario_consulta'])
    pct_doctor = float(doctor['porcentaje_dividendo'])
    monto_doctor = round((costo * pct_doctor) / 100.0, 2)
    monto_clinica = round(costo - monto_doctor, 2)

    return execute_db("""
        INSERT INTO citas (
            codigo, paciente_id, doctor_id, especialidad_id, fecha, hora, 
            padecimiento, costo_consulta, porcentaje_doctor, monto_doctor, monto_clinica, 
            estado, estado_pago_medico
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Programada', 'Pendiente')
    """, (
        codigo, paciente_id, doctor_id, doctor['especialidad_id'], fecha, hora,
        padecimiento, costo, pct_doctor, monto_doctor, monto_clinica
    ), return_id=True)

def atender_cita(cita_id, diagnostico_observaciones):
    return execute_db("""
        UPDATE citas
        SET estado = 'Atendida', diagnostico_observaciones = ?
        WHERE id = ?
    """, (diagnostico_observaciones, cita_id))

def cancelar_cita(cita_id):
    return execute_db("""
        UPDATE citas
        SET estado = 'Cancelada'
        WHERE id = ?
    """, (cita_id,))

# Dividendos y liquidaciones
def get_dividendos_por_doctor():
    return query_db("""
        SELECT 
            d.id AS doctor_id,
            d.nombre, d.apellido, d.cedula, d.porcentaje_dividendo,
            e.nombre AS especialidad_nombre,
            COUNT(CASE WHEN c.estado = 'Atendida' AND c.estado_pago_medico = 'Pendiente' THEN 1 END) AS consultas_pendientes,
            COALESCE(SUM(CASE WHEN c.estado = 'Atendida' AND c.estado_pago_medico = 'Pendiente' THEN c.monto_doctor END), 0) AS monto_pendiente_pago,
            COALESCE(SUM(CASE WHEN c.estado = 'Atendida' AND c.estado_pago_medico = 'Liquidado' THEN c.monto_doctor END), 0) AS monto_total_liquidado
        FROM doctores d
        JOIN especialidades e ON d.especialidad_id = e.id
        LEFT JOIN citas c ON d.id = c.doctor_id
        GROUP BY d.id
        ORDER BY monto_pendiente_pago DESC, d.apellido ASC
    """)

def get_citas_pendientes_pago_doctor(doctor_id):
    return query_db("""
        SELECT 
            c.*, 
            p.nombre AS paciente_nombre, p.apellido AS paciente_apellido
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        WHERE c.doctor_id = ? AND c.estado = 'Atendida' AND c.estado_pago_medico = 'Pendiente'
        ORDER BY c.fecha ASC, c.hora ASC
    """, (doctor_id,))

def generar_liquidacion_pago(doctor_id, citas_ids, metodo_pago, numero_referencia, observaciones):
    if not citas_ids:
        raise ValueError("Debe seleccionar al menos una consulta para liquidar.")

    placeholders = ",".join("?" * len(citas_ids))
    citas_seleccionadas = query_db(f"""
        SELECT * FROM citas 
        WHERE id IN ({placeholders}) AND doctor_id = ? AND estado = 'Atendida' AND estado_pago_medico = 'Pendiente'
    """, (*citas_ids, doctor_id))

    if len(citas_seleccionadas) == 0:
        raise ValueError("No se encontraron consultas válidas pendientes para liquidar.")

    total_consultas = len(citas_seleccionadas)
    monto_total_consultas = sum(c['costo_consulta'] for c in citas_seleccionadas)
    monto_dividendo_doctor = sum(c['monto_doctor'] for c in citas_seleccionadas)
    monto_retenido_clinica = sum(c['monto_clinica'] for c in citas_seleccionadas)

    count_liq = query_db("SELECT COUNT(*) AS total FROM liquidaciones_pago", one=True)['total']
    current_year = datetime.now().year
    numero_comprobante = f"LIQ-{current_year}-{str(count_liq + 1).zfill(4)}"
    fecha_pago = date.today().isoformat()

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO liquidaciones_pago (
                numero_comprobante, doctor_id, total_consultas, monto_total_consultas,
                monto_dividendo_doctor, monto_retenido_clinica, fecha_pago,
                metodo_pago, numero_referencia, observaciones, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Liquidado')
        """, (
            numero_comprobante, doctor_id, total_consultas, monto_total_consultas,
            monto_dividendo_doctor, monto_retenido_clinica, fecha_pago,
            metodo_pago, numero_referencia, observaciones
        ))
        liquidacion_id = cur.lastrowid

        for c in citas_seleccionadas:
            cur.execute("""
                UPDATE citas
                SET estado_pago_medico = 'Liquidado', liquidacion_id = ?
                WHERE id = ?
            """, (liquidacion_id, c['id']))

        conn.commit()
        return liquidacion_id
    finally:
        conn.close()

def get_liquidaciones():
    return query_db("""
        SELECT 
            lp.*,
            d.nombre AS doctor_nombre, d.apellido AS doctor_apellido, d.cedula AS doctor_cedula,
            e.nombre AS especialidad_nombre
        FROM liquidaciones_pago lp
        JOIN doctores d ON lp.doctor_id = d.id
        JOIN especialidades e ON d.especialidad_id = e.id
        ORDER BY lp.fecha_pago DESC, lp.id DESC
    """)

def get_liquidacion(id):
    liq = query_db("""
        SELECT 
            lp.*,
            d.nombre AS doctor_nombre, d.apellido AS doctor_apellido, d.cedula AS doctor_cedula, d.telefono AS doctor_telefono, d.email AS doctor_email,
            e.nombre AS especialidad_nombre,
            c.nombre AS cargo_nombre
        FROM liquidaciones_pago lp
        JOIN doctores d ON lp.doctor_id = d.id
        JOIN especialidades e ON d.especialidad_id = e.id
        JOIN cargos c ON d.cargo_id = c.id
        WHERE lp.id = ?
    """, (id,), one=True)
    
    if not liq:
        return None

    citas = query_db("""
        SELECT 
            c.*, 
            p.nombre AS paciente_nombre, p.apellido AS paciente_apellido, p.cedula AS paciente_cedula
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        WHERE c.liquidacion_id = ?
        ORDER BY c.fecha ASC, c.hora ASC
    """, (id,))

    return {
        **dict(liq),
        'citas': citas
    }

# Usuarios y autenticación
def get_user_by_username(username):
    return query_db("SELECT * FROM usuarios WHERE username = ?", (username,), one=True)

def get_user_by_id(id):
    return query_db("SELECT * FROM usuarios WHERE id = ?", (id,), one=True)
