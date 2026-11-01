# ==============================================================================
# VidaClinic — Suite de Pruebas Automatizadas
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

import os
import sys
from app import app
from database.init_db import init_database

print("[TEST] Inicializando base de datos para pruebas...")
init_database()

client = app.test_client()

# 1. Login page
res = client.get('/login')
assert res.status_code == 200, f"Login GET failed: {res.status_code}"
assert "Panel Administrativo" in res.data.decode('utf-8')
assert "Agendar Cita Paciente" in res.data.decode('utf-8')
print("[OK] Pagina /login y banner de paciente funcionan correctamente.")

# 2. Public appointment scheduling page
res = client.get('/agendar-cita')
assert res.status_code == 200, f"Agendar Cita GET failed: {res.status_code}"
assert "Solicitud de Consulta Médica" in res.data.decode('utf-8')
print("[OK] Pagina /agendar-cita GET funciona correctamente.")

# 3. Public appointment booking POST
import time
unique_cedula = f"V-{int(time.time() * 100) % 100000000}"
# Use a future dynamic day to guarantee no collisions across runs
from datetime import timedelta, date
test_date = (date.today() + timedelta(days=50 + (int(time.time()) % 1000))).isoformat()

form_data = {
    'nombre': 'Valeria',
    'apellido': 'Gomez',
    'cedula': unique_cedula,
    'telefono': '0414-9988776',
    'email': 'valeria@gmail.com',
    'fecha_nacimiento': '1998-05-12',
    'genero': 'Femenino',
    'direccion': 'Calle Las Flores, Edif A',
    'doctor_id': '2',
    'fecha': test_date,
    'hora': '10:30',
    'padecimiento': 'Migrañas recurrentes y dolor ocular severo',
    'motivo': 'Control y evaluacion general'
}
res = client.post('/agendar-cita', data=form_data, follow_redirects=True)
assert res.status_code == 200, f"Agendar Cita POST failed: {res.status_code}"
assert "Comprobante Digital de Consulta Médica" in res.data.decode('utf-8')
print("[OK] Agendamiento publico de cita POST funciona y redirige al comprobante.")

# 4. Public PDF voucher download
res = client.get('/cita-publica/1/pdf')
assert res.status_code == 200, f"Public PDF failed: {res.status_code}"
assert res.headers['Content-Type'] == 'application/pdf'
assert len(res.data) > 1000
print(f"[OK] Generacion de PDF comprobante de cita publica funciona (Tamano: {len(res.data)} bytes).")

# 5. Admin Login
res = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
assert res.status_code == 200, f"Admin login failed: {res.status_code}"
assert "Control de Consulta Médica" in res.data.decode('utf-8')
print("[OK] Login administrativo correcto.")

# 6. Admin Dashboard & Subpages
for endpoint in ['/dashboard', '/citas', '/pacientes', '/medicos', '/dividendos', '/reportes', '/database']:
    res = client.get(endpoint)
    assert res.status_code == 200, f"GET {endpoint} falló con {res.status_code}"
    print(f"[OK] Endpoint administrativo {endpoint} responde con HTTP 200.")

# 7. Excel Reports
res = client.get('/reportes/citas/excel')
assert res.status_code == 200, f"Excel citas failed: {res.status_code}"
assert len(res.data) > 2000
print(f"[OK] Reporte Excel de citas funciona ({len(res.data)} bytes).")

res = client.get('/reportes/liquidaciones/excel')
assert res.status_code == 200, f"Excel liquidaciones failed: {res.status_code}"
assert len(res.data) > 2000
print(f"[OK] Reporte Excel de liquidaciones/dividendos funciona ({len(res.data)} bytes).")

res = client.get('/reportes/pacientes/excel')
assert res.status_code == 200, f"Excel pacientes failed: {res.status_code}"
assert len(res.data) > 2000
print(f"[OK] Reporte Excel de pacientes funciona ({len(res.data)} bytes).")

# 8. PDF Reports
res = client.get('/reportes/citas/pdf')
assert res.status_code == 200, f"PDF citas failed: {res.status_code}"
assert res.headers['Content-Type'] == 'application/pdf'
assert len(res.data) > 2000
print(f"[OK] Reporte PDF de citas funciona ({len(res.data)} bytes).")

res = client.get('/liquidaciones/1/pdf')
assert res.status_code == 200, f"PDF liquidacion failed: {res.status_code}"
assert res.headers['Content-Type'] == 'application/pdf'
assert len(res.data) > 2000
print(f"[OK] Comprobante PDF de liquidacion/dividendo funciona ({len(res.data)} bytes).")

# 9. SQLite .db file download endpoint
res = client.get('/database/download-db')
assert res.status_code == 200, f"Download .db failed: {res.status_code}"
assert len(res.data) > 1000
print(f"[OK] Descarga de archivo SQLite3 (.db) funciona ({len(res.data)} bytes).")

# 10. BCV Exchange Rate API endpoint
res = client.get('/api/tasa-bcv')
assert res.status_code == 200, f"API tasa BCV failed: {res.status_code}"
data_bcv = res.get_json()
assert 'tasa' in data_bcv and data_bcv['tasa'] > 0
print(f"[OK] Endpoint /api/tasa-bcv responde correctamente (Tasa BCV: {data_bcv['tasa']} Bs./USD).")

print("\n--- TODOS LOS TESTS PASARON EXITOSAMENTE ---")
