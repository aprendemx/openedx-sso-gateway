"""
Simulación de la respuesta de Llave MX, SOLO para ambientes de prueba.

Sirve para probar casos que no se pueden reproducir con una identidad real de
pruebas (p. ej. una persona con un solo apellido): se inicia sesión con Llave MX
de verdad y este paso reemplaza algunos campos de `details` antes de que el
pipeline los guarde y el MFE de registro los reciba en pipelineUserDetails.

Se activa con un dict en settings (vacío o ausente = paso inactivo):

    SSO_GATEWAY_SIMULAR_LLAVEMX = {"segundo_apellido": ""}

Nunca corre en producción: si LMS_BASE es un host de producción, se ignora.
"""
import logging

logger = logging.getLogger(__name__)

SETTING = 'SSO_GATEWAY_SIMULAR_LLAVEMX'
HOSTS_PRODUCCION = frozenset({'cursos.aprende.gob.mx', 'cursos.mexicox.gob.mx'})
CAMPOS_PERMITIDOS = frozenset({
    'nombres', 'primer_apellido', 'segundo_apellido', 'curp',
    'es_extranjero', 'estado', 'municipio',
})


def simulacion_activa(overrides, lms_base):
    """Devuelve los campos a reemplazar, o {} si la simulación no debe correr."""
    if not overrides or not isinstance(overrides, dict):
        return {}
    if (lms_base or '').split(':')[0] in HOSTS_PRODUCCION:
        return {}
    return {k: v for k, v in overrides.items() if k in CAMPOS_PERMITIDOS}


def aplicar_simulacion(details, overrides):
    """Copia de `details` con los campos simulados; recalcula el nombre completo."""
    nuevos = {**(details or {}), **overrides}
    if {'nombres', 'primer_apellido', 'segundo_apellido'} & overrides.keys():
        partes = (nuevos.get('nombres'), nuevos.get('primer_apellido'), nuevos.get('segundo_apellido'))
        nuevos['name'] = ' '.join(p.strip() for p in partes if p and p.strip())
        nuevos['fullname'] = nuevos['name']
    return nuevos


def simular_llavemx(backend, details=None, *args, **kwargs):
    """Paso de pipeline: reemplaza campos de Llave MX según SSO_GATEWAY_SIMULAR_LLAVEMX."""
    if getattr(backend, 'name', None) != 'llavemx':
        return None

    from django.conf import settings  # pylint: disable=import-outside-toplevel

    lms_base = getattr(settings, 'LMS_BASE', '')
    configurado = getattr(settings, SETTING, None)
    overrides = simulacion_activa(configurado, lms_base)
    if not overrides:
        if configurado:
            logger.error('[SSOGateway] %s ignorado: %s es producción o no hay campos válidos.', SETTING, lms_base)
        return None

    nuevos = aplicar_simulacion(details, overrides)
    # El plugin de Llave MX también lee estos datos de la sesión como respaldo.
    try:
        sesion = dict(backend.strategy.session_get('llavemx_details') or {})
        sesion.update({k: nuevos[k] for k in overrides})
        backend.strategy.session_set('llavemx_details', sesion)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning('[SSOGateway] simular_llavemx: no se pudo actualizar la sesión: %s', exc)

    logger.warning('[SSOGateway] SIMULACIÓN de Llave MX activa en %s: campos=%s', lms_base, sorted(overrides))
    return {'details': nuevos}
