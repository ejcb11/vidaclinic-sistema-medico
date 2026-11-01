-- ==============================================================
-- VidaClinic — Esquema DDL Relacional SQLite3
-- Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
-- Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
-- ==============================================================

PRAGMA foreign_keys = ON;

-- 1. TABLA DE CARGOS / JERARQUÍAS MÉDICAS
CREATE TABLE IF NOT EXISTS cargos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA DE ESPECIALIDADES MÉDICAS
CREATE TABLE IF NOT EXISTS especialidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    costo_base REAL NOT NULL DEFAULT 50.00,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLA DE DOCTORES (MÉDICOS)
CREATE TABLE IF NOT EXISTS doctores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    cedula TEXT NOT NULL UNIQUE,
    especialidad_id INTEGER NOT NULL,
    cargo_id INTEGER NOT NULL,
    telefono TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    honorario_consulta REAL NOT NULL DEFAULT 50.00,
    porcentaje_dividendo REAL NOT NULL DEFAULT 70.00, -- % para el médico p/c
    estado TEXT NOT NULL DEFAULT 'Activo' CHECK(estado IN ('Activo', 'Inactivo')),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (especialidad_id) REFERENCES especialidades(id) ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON DELETE RESTRICT
);

-- 4. TABLA DE PACIENTES
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    cedula TEXT NOT NULL UNIQUE,
    fecha_nacimiento TEXT NOT NULL,
    genero TEXT NOT NULL CHECK(genero IN ('Femenino', 'Masculino', 'Otro')),
    telefono TEXT NOT NULL,
    email TEXT NOT NULL,
    direccion TEXT,
    grupo_sanguineo TEXT DEFAULT 'O+',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLA DE LIQUIDACIONES DE PAGO A MÉDICOS
CREATE TABLE IF NOT EXISTS liquidaciones_pago (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_comprobante TEXT NOT NULL UNIQUE,
    doctor_id INTEGER NOT NULL,
    total_consultas INTEGER NOT NULL,
    monto_total_consultas REAL NOT NULL,
    monto_dividendo_doctor REAL NOT NULL,
    monto_retenido_clinica REAL NOT NULL,
    fecha_pago TEXT NOT NULL,
    metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('Transferencia Bancaria', 'Efectivo', 'Cheque', 'Pago Móvil')),
    numero_referencia TEXT,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'Liquidado',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctores(id) ON DELETE RESTRICT
);

-- 6. TABLA DE CITAS MÉDICAS (Con Padecimiento y Control de Dividendo P/C)
CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    paciente_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    especialidad_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    padecimiento TEXT NOT NULL, -- Requerimiento expreso de la orden médica
    costo_consulta REAL NOT NULL,
    porcentaje_doctor REAL NOT NULL, -- % al momento de registrar la cita
    monto_doctor REAL NOT NULL,      -- Monto neto para el médico
    monto_clinica REAL NOT NULL,     -- Monto para gastos clínicos
    estado TEXT NOT NULL DEFAULT 'Programada' CHECK(estado IN ('Programada', 'Atendida', 'Cancelada')),
    estado_pago_medico TEXT NOT NULL DEFAULT 'Pendiente' CHECK(estado_pago_medico IN ('Pendiente', 'Liquidado')),
    liquidacion_id INTEGER,
    diagnostico_observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctores(id) ON DELETE RESTRICT,
    FOREIGN KEY (especialidad_id) REFERENCES especialidades(id) ON DELETE RESTRICT,
    FOREIGN KEY (liquidacion_id) REFERENCES liquidaciones_pago(id) ON DELETE SET NULL
);

-- 7. TABLA DE USUARIOS DEL SISTEMA (ROLES: Administrador, Paciente)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('Administrador', 'Paciente')),
    paciente_id INTEGER,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE SET NULL
);

-- Índices para búsquedas optimizadas
CREATE INDEX IF NOT EXISTS idx_citas_fecha ON citas(fecha);
CREATE INDEX IF NOT EXISTS idx_citas_doctor ON citas(doctor_id);
CREATE INDEX IF NOT EXISTS idx_citas_paciente ON citas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_doctores_especialidad ON doctores(especialidad_id);
