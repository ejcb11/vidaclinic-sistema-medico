# ==============================================================================
# VidaClinic — Módulo de Validación de Integridad de Datos
# Copyright (c) 2026 Eduardo Contreras (@ejcb11). Todos los derechos reservados.
# Obra protegida para exhibición en portafolio. Consulte LICENSE.txt
# ==============================================================================

"""Validación de formularios y campos."""

import re
from datetime import datetime, date

REGEX_SOLO_LETRAS = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
REGEX_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
REGEX_TELEFONO = re.compile(r"^[\+]?[0-9\s\-\(\)]{7,20}$")
REGEX_CEDULA = re.compile(r"^[VvEeJjPp0-9\-]{5,15}$")

def validate_letters_only(text: str, field_name: str = "Campo", min_len: int = 2) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, f"El {field_name} es obligatorio."
    
    clean_text = text.strip()
    if len(clean_text) < min_len:
        return False, f"El {field_name} debe tener al menos {min_len} caracteres."
    
    if not REGEX_SOLO_LETRAS.match(clean_text):
        return False, f"El {field_name} sólo puede contener letras y espacios (sin números ni símbolos especiales)."
    
    return True, ""

def validate_cedula(cedula: str) -> tuple[bool, str]:
    if not cedula or not cedula.strip():
        return False, "La cédula / documento de identidad es obligatoria."
    
    clean = cedula.strip()
    if not REGEX_CEDULA.match(clean):
        return False, "El formato de cédula/documento no es válido (solo números o prefijo V-, E-)."
    
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    if not email or not email.strip():
        return False, "El correo electrónico es obligatorio."
    
    clean = email.strip()
    if not REGEX_EMAIL.match(clean):
        return False, "El formato del correo electrónico no es válido."
    
    return True, ""

def validate_phone(phone: str) -> tuple[bool, str]:
    if not phone or not phone.strip():
        return False, "El teléfono de contacto es obligatorio."
    
    clean = phone.strip()
    if not REGEX_TELEFONO.match(clean):
        return False, "El teléfono debe contener números y puede incluir prefijos (+, -)."
    
    return True, ""

def validate_percentage(pct_val, field_name: str = "Porcentaje de dividendo") -> tuple[bool, str]:
    try:
        val = float(pct_val)
        if val <= 0 or val > 100:
            return False, f"El {field_name} debe ser un valor entre 1% y 100%."
        return True, ""
    except (ValueError, TypeError):
        return False, f"El {field_name} debe ser un valor numérico válido."

def validate_amount(amount_val, field_name: str = "Honorario / Costo") -> tuple[bool, str]:
    try:
        val = float(amount_val)
        if val <= 0:
            return False, f"El {field_name} debe ser mayor a 0."
        return True, ""
    except (ValueError, TypeError):
        return False, f"El {field_name} debe ser un valor numérico válido."

def validate_ailment(padecimiento: str) -> tuple[bool, str]:
    if not padecimiento or not padecimiento.strip():
        return False, "El padecimiento o motivo de consulta es obligatorio."
    
    clean = padecimiento.strip()
    if len(clean) < 5:
        return False, "Describa el padecimiento con al menos 5 caracteres."
    
    return True, ""

def validate_appointment_date(date_str: str) -> tuple[bool, str]:
    if not date_str or not date_str.strip():
        return False, "La fecha de la cita es obligatoria."
    
    try:
        appt_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        today = date.today()
        if appt_date < today:
            return False, f"No se puede agendar una cita en una fecha pasada ({date_str})."
        return True, ""
    except ValueError:
        return False, "Formato de fecha inválido. Debe ser AAAA-MM-DD."
