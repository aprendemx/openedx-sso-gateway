"""
Pruebas de sso_gateway.simulacion (lógica pura, sin Django).

    python -m unittest discover -s tests
"""
import importlib.util
import pathlib
import unittest

_ruta = pathlib.Path(__file__).resolve().parents[1] / 'sso_gateway' / 'simulacion.py'
_spec = importlib.util.spec_from_file_location('simulacion', _ruta)
simulacion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(simulacion)

DETAILS = {
    'nombres': 'DIANA', 'primer_apellido': 'PRUEBA', 'segundo_apellido': 'LÓPEZ',
    'name': 'DIANA PRUEBA LÓPEZ', 'fullname': 'DIANA PRUEBA LÓPEZ', 'curp': 'X',
}


class SimulacionActivaTest(unittest.TestCase):
    def test_sin_setting_no_simula(self):
        self.assertEqual(simulacion.simulacion_activa(None, 'dev-cursos.aprende.gob.mx'), {})
        self.assertEqual(simulacion.simulacion_activa({}, 'dev-cursos.aprende.gob.mx'), {})

    def test_produccion_nunca_simula(self):
        for host in ('cursos.aprende.gob.mx', 'cursos.aprende.gob.mx:443', 'cursos.mexicox.gob.mx'):
            self.assertEqual(simulacion.simulacion_activa({'segundo_apellido': ''}, host), {})

    def test_pruebas_simula_solo_campos_permitidos(self):
        self.assertEqual(
            simulacion.simulacion_activa({'segundo_apellido': '', 'email': 'otro@x.mx'}, 'dev-cursos.aprende.gob.mx'),
            {'segundo_apellido': ''},
        )


class AplicarSimulacionTest(unittest.TestCase):
    def test_un_solo_apellido_recalcula_nombre(self):
        nuevos = simulacion.aplicar_simulacion(DETAILS, {'segundo_apellido': ''})
        self.assertEqual(nuevos['segundo_apellido'], '')
        self.assertEqual(nuevos['name'], 'DIANA PRUEBA')
        self.assertEqual(nuevos['fullname'], 'DIANA PRUEBA')
        self.assertEqual(DETAILS['segundo_apellido'], 'LÓPEZ')  # no muta el original

    def test_campo_ajeno_al_nombre_no_lo_toca(self):
        nuevos = simulacion.aplicar_simulacion(DETAILS, {'curp': 'OTRA'})
        self.assertEqual(nuevos['name'], DETAILS['name'])


if __name__ == '__main__':
    unittest.main()
