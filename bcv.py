"""Módulo de consulta y conversión de divisas con Tasa Oficial del Banco Central de Venezuela (BCV)."""

import os
import json
import urllib.request
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, 'database', 'tasa_bcv_cache.json')

# Tasa de respaldo inicial en caso de desconexión total a internet
FALLBACK_RATE = 886.23

_memory_cache = {
    'data': None,
    'timestamp': None
}

def fetch_bcv_from_api():
    """Consulta la API pública de DolarApi Venezuela para obtener la tasa oficial BCV."""
    url = 'https://ve.dolarapi.com/v1/dolares/oficial'
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=4) as response:
        payload = json.loads(response.read().decode('utf-8'))
        rate = float(payload.get('promedio') or payload.get('venta') or payload.get('compra') or 0)
        if rate <= 0:
            raise ValueError("Tasa retornada inválida")
        
        fecha_raw = payload.get('fechaActualizacion', '')
        fecha_fmt = datetime.now().strftime('%d/%m/%Y')
        if fecha_raw:
            try:
                dt = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                fecha_fmt = dt.strftime('%d/%m/%Y')
            except Exception:
                pass

        return {
            'tasa': round(rate, 4),
            'promedio': round(rate, 2),
            'fecha': fecha_fmt,
            'fecha_actualizacion': datetime.now().isoformat(),
            'fuente': 'Banco Central de Venezuela (BCV)',
            'moneda': 'USD',
            'simbolo': 'Bs.'
        }

def save_cache_to_file(data):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_cache_from_file():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def get_tasa_bcv(force_refresh=False):
    """
    Retorna la tasa BCV actualizada.
    Utiliza caché en memoria (30 minutos), respaldo en archivo y fallback seguro.
    """
    global _memory_cache
    now = datetime.now()

    # Si tenemos caché en memoria y no ha expirado (30 min)
    if not force_refresh and _memory_cache['data'] and _memory_cache['timestamp']:
        diff = (now - _memory_cache['timestamp']).total_seconds()
        if diff < 1800:
            return _memory_cache['data']

    # Intentar consultar la API del BCV
    try:
        data = fetch_bcv_from_api()
        _memory_cache['data'] = data
        _memory_cache['timestamp'] = now
        save_cache_to_file(data)
        return data
    except Exception:
        pass

    # Si falla la red, cargar del caché en disco
    file_cache = load_cache_from_file()
    if file_cache:
        _memory_cache['data'] = file_cache
        _memory_cache['timestamp'] = now
        return file_cache

    # Fallback predeterminado seguro
    fallback = {
        'tasa': FALLBACK_RATE,
        'promedio': FALLBACK_RATE,
        'fecha': now.strftime('%d/%m/%Y'),
        'fecha_actualizacion': now.isoformat(),
        'fuente': 'Banco Central de Venezuela (BCV)',
        'moneda': 'USD',
        'simbolo': 'Bs.'
    }
    _memory_cache['data'] = fallback
    _memory_cache['timestamp'] = now
    return fallback

def usd_to_bs(amount_usd, tasa=None):
    """Convierte un monto en dólares a bolívares según la tasa BCV."""
    try:
        val = float(amount_usd or 0)
    except (ValueError, TypeError):
        val = 0.0

    if tasa is None:
        tasa = get_tasa_bcv()['tasa']
    else:
        try:
            tasa = float(tasa)
        except (ValueError, TypeError):
            tasa = FALLBACK_RATE

    return round(val * tasa, 2)

def format_bs(amount_bs):
    """Formatea un monto en bolívares: Bs. 1,234.56"""
    try:
        val = float(amount_bs or 0)
    except (ValueError, TypeError):
        val = 0.0
    return f"Bs. {val:,.2f}"
