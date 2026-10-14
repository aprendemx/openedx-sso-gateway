"""
Identidad verificada de Llave MX — lógica pura, sin dependencias de Django.

Llave MX entrega nombre, apellidos y CURP verificados contra RENAPO. En un registro
nuevo, esos datos deben quedar en la ficha del alumno (ExtraInfo) y en el nombre del
perfil (que se imprime en la constancia), aunque el formulario haya enviado otros.

Es la misma regla que aplica el formulario de registro (fork del MFE de authn); aquí
se repite en el servidor porque la API de registro puede llamarse sin pasar por él.
"""
import re
from datetime import timedelta

CURP_GENERICA_EXTRANJERO = 'XEXX010101HDFXXX04'
CURP_RE = re.compile(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9]{2}$')

# Cuenta creada y ligada a Llave MX en el mismo acceso. Medido en producción
# (oct 2026): el 99.86% de los registros con Llave MX se ligan en menos de 10 min.
# Se prefiere una ventana corta: tomar por nueva una cuenta antigua sobrescribiría
# sus datos; lo contrario solo deja el caso como antes.
VENTANA_REGISTRO_NUEVO = timedelta(minutes=10)


def _limpiar(valor):
    return (valor or '').strip().upper()


def identidad_llavemx(details):
    """
    Devuelve la identidad de Llave MX que debe fijarse, con None en lo que no se fija.

    - Nombres: se fijan nombre y ambos apellidos si vienen nombre y primer apellido
      (un segundo apellido vacío es dato verificado: la persona no lo tiene).
    - CURP: si viene una CURP válida, esa. Si la persona es extranjera, la genérica.
      Si es nacional y no viene CURP (anómalo), no se fija.
    """
    details = details or {}
    nombres = _limpiar(details.get('nombres'))
    primer_apellido = _limpiar(details.get('primer_apellido'))
    segundo_apellido = _limpiar(details.get('segundo_apellido'))
    curp = _limpiar(details.get('curp'))
    es_extranjero = bool(details.get('es_extranjero') or details.get('esExtranjero')) \
        or curp == CURP_GENERICA_EXTRANJERO

    identidad = {
        'nombres': None,
        'primer_apellido': None,
        'segundo_apellido': None,
        'curp': None,
        'nombre_completo': None,
    }
    if nombres and primer_apellido:
        identidad.update({
            'nombres': nombres,
            'primer_apellido': primer_apellido,
            'segundo_apellido': segundo_apellido,
            'nombre_completo': ' '.join(p for p in (nombres, primer_apellido, segundo_apellido) if p),
        })
    if curp and CURP_RE.match(curp) and curp != CURP_GENERICA_EXTRANJERO:
        identidad['curp'] = curp
    elif es_extranjero:
        identidad['curp'] = CURP_GENERICA_EXTRANJERO
    return identidad


def es_registro_nuevo(fecha_alta, is_new, new_association, ahora):
    """
    True si la cuenta nace en este acceso con Llave MX.

    - is_new: create_user creó la cuenta en el pipeline.
    - new_association + fecha_alta reciente: el formulario de registro creó la cuenta
      (en ese flujo is_new llega en False) y este acceso la liga por primera vez.
    Una cuenta antigua que se liga por primera vez NO es registro nuevo.
    """
    if is_new:
        return True
    if not new_association or fecha_alta is None:
        return False
    return timedelta(0) <= ahora - fecha_alta <= VENTANA_REGISTRO_NUEVO
