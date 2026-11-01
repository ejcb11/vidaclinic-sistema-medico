# ==============================================================================
# VidaClinic — Inicialización y Poblado Semilla de Base de Datos
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

"""Inicialización del esquema y datos iniciales."""

import sqlite3
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vidaclinic.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_database(reset=False):
    if reset and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Cargos
    cargos = [
        ('Médico Titular', 'Atención clínica permanente y consultas especializadas programadas'),
        ('Especialista Senior', 'Especialista con más de 10 años de experiencia e interconsultas complejas'),
        ('Jefe de Departamento', 'Dirección de especialidad médica y coordinación de turnos'),
        ('Médico Residente', 'Atención supervisada en área clínica'),
        ('Médico Consultor Externo', 'Atención por llamada o convenio especial')
    ]
    cursor.executemany("INSERT INTO cargos (nombre, descripcion) VALUES (?, ?)", cargos)

    # Especialidades
    especialidades = [
        ('Cardiología', 'Diagnóstico y tratamiento de afecciones cardíacas y vasculares', 65.00),
        ('Pediatría', 'Salud integral del recién nacido, infante y adolescente', 45.00),
        ('Medicina General', 'Evaluación médica integral, chequeos preventivos y diagnóstico preliminar', 35.00),
        ('Traumatología', 'Tratamiento de fracturas, esguinces y patologías osteoarticulares', 60.00),
        ('Ginecología y Obstetricia', 'Salud femenina, control prenatal y ginecológico anual', 55.00),
        ('Dermatología', 'Tratamiento de piel, mucosas, acné y lesiones cutáneas', 50.00),
        ('Neurología', 'Enfermedades del sistema nervioso central y periférico', 70.00),
        ('Oftalmología', 'Salud ocular, agudeza visual y control de fondo de ojo', 50.00)
    ]
    cursor.executemany("INSERT INTO especialidades (nombre, descripcion, costo_base) VALUES (?, ?, ?)", especialidades)

    # Doctores
    doctores = [
        ('Carlos', 'Mendoza Alarcón', 'V-24158932', 1, 2, '+58 414 1234567', 'carlos.mendoza@vidaclinic.com', 65.00, 70.0, 'Activo'),
        ('Elena', 'Castillo Valera', 'V-19874521', 2, 1, '+58 424 9876543', 'elena.castillo@vidaclinic.com', 45.00, 65.0, 'Activo'),
        ('Javier', 'Morales Silva', 'V-22341789', 4, 3, '+58 412 5551234', 'javier.morales@vidaclinic.com', 60.00, 75.0, 'Activo'),
        ('Sofía', 'Ramírez Delgado', 'V-25412365', 5, 1, '+58 416 3338901', 'sofia.ramirez@vidaclinic.com', 55.00, 70.0, 'Activo'),
        ('Andrés', 'Pérez Quintero', 'V-20114876', 3, 1, '+58 414 7772345', 'andres.perez@vidaclinic.com', 35.00, 60.0, 'Activo')
    ]
    cursor.executemany("""
        INSERT INTO doctores (nombre, apellido, cedula, especialidad_id, cargo_id, telefono, email, honorario_consulta, porcentaje_dividendo, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, doctores)

    # Pacientes
    pacientes = [
        ('Valentina', 'Gómez Rivas', 'V-27891234', '1998-05-14', 'Femenino', '+58 424 1122334', 'valegomez@gmail.com', 'Av. Las Delicias, Residencias Paraíso, Apto 4B', 'O+'),
        ('Roberto', 'Méndez Cárdenas', 'V-18451290', '1985-11-20', 'Masculino', '+58 414 9988776', 'roberto.mendez@gmail.com', 'Calle Bolívar con Miranda, Casa 12', 'A+'),
        ('Lucía', 'Fernández Bravo', 'V-29001452', '2001-03-08', 'Femenino', '+58 412 4433221', 'lucia.fernandez@gmail.com', 'Urb. Los Rosales, Calle 3, Qta. Milagros', 'B+'),
        ('Alejandro', 'Torres Rojas', 'V-15987321', '1979-08-30', 'Masculino', '+58 416 8877665', 'alejandro.torres@hotmail.com', 'Av. 5 de Julio, Edf. Horizonte, Piso 2', 'AB+')
    ]
    cursor.executemany("""
        INSERT INTO pacientes (nombre, apellido, cedula, fecha_nacimiento, genero, telefono, email, direccion, grupo_sanguineo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pacientes)

    # Citas
    citas = [
        (
            'CIT-1001', 1, 1, 1, '2026-10-20', '09:00',
            'Palpitaciones y dolor opresivo precordial tras ejercicio físico leve',
            65.00, 70.0, 45.50, 19.50, 'Atendida', 'Liquidado',
            'Se realiza electrocardiograma. Ritmo sinusal normal con taquicardia aislada. Se receta betabloqueante suave y control en 15 días.'
        ),
        (
            'CIT-1002', 2, 3, 4, '2026-10-22', '10:30',
            'Traumatismo en rodilla derecha con inflamación y limitación de marcha',
            60.00, 75.0, 45.00, 15.00, 'Atendida', 'Pendiente',
            'Signo de bostezo positivo leve. Esguince de ligamento colateral grado I. Reposo e inmovilización.'
        ),
        (
            'CIT-1003', 3, 4, 5, '2026-10-24', '11:00',
            'Chequeo ginecológico anual y citología de rutina',
            55.00, 70.0, 38.50, 16.50, 'Atendida', 'Pendiente',
            'Examen físico dentro de parámetros fisiológicos. Toma de muestra citológica realizada.'
        ),
        (
            'CIT-1004', 4, 5, 3, '2026-10-25', '08:30',
            'Fiebre de 38.5 grados, odinofagia intensa y malestar osteomuscular de 48 horas',
            35.00, 60.0, 21.00, 14.00, 'Programada', 'Pendiente',
            ''
        ),
        (
            'CIT-1005', 1, 2, 2, '2026-10-26', '14:00',
            'Evaluación pediátrica de control y esquema de inmunizaciones',
            45.00, 65.0, 29.25, 15.75, 'Programada', 'Pendiente',
            ''
        )
    ]
    cursor.executemany("""
        INSERT INTO citas (codigo, paciente_id, doctor_id, especialidad_id, fecha, hora, padecimiento, costo_consulta, porcentaje_doctor, monto_doctor, monto_clinica, estado, estado_pago_medico, diagnostico_observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, citas)

    # Liquidación inicial
    cursor.execute("""
        INSERT INTO liquidaciones_pago (numero_comprobante, doctor_id, total_consultas, monto_total_consultas, monto_dividendo_doctor, monto_retenido_clinica, fecha_pago, metodo_pago, numero_referencia, observaciones, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'LIQ-2026-0001', 1, 1, 65.00, 45.50, 19.50, '2026-10-21',
        'Transferencia Bancaria', 'TRANSF-BNC-8849201',
        'Liquidación correspondiente a consulta cardiológica CIT-1001 atendida.',
        'Liquidado'
    ))
    liq_id = cursor.lastrowid
    cursor.execute("UPDATE citas SET liquidacion_id = ? WHERE codigo = 'CIT-1001'", (liq_id,))

    # Usuarios
    usuarios = [
        ('admin', hash_password('admin123'), 'Administrador', 'Administrador', None),
        ('paciente', hash_password('paciente123'), 'Valentina Gómez Rivas', 'Paciente', 1)
    ]
    cursor.executemany("""
        INSERT INTO usuarios (username, password_hash, nombre_completo, rol, paciente_id)
        VALUES (?, ?, ?, ?, ?)
    """, usuarios)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database(reset=True)
