"""
Pruebas de sso_gateway.identidad (lógica pura, sin Django).

    python -m unittest discover -s tests
"""
import importlib.util
import pathlib
import unittest
from datetime import datetime, timedelta, timezone

# Se carga el módulo directo para no importar sso_gateway/__init__ ni Django.
_ruta = pathlib.Path(__file__).resolve().parents[1] / 'sso_gateway' / 'identidad.py'
_spec = importlib.util.spec_from_file_location('identidad', _ruta)
identidad_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(identidad_mod)

identidad_llavemx = identidad_mod.identidad_llavemx
es_registro_nuevo = identidad_mod.es_registro_nuevo
CURP_GENERICA = identidad_mod.CURP_GENERICA_EXTRANJERO

CURP = 'PULD800101MDFRPN09'
BASE = {'nombres': 'Diana', 'primer_apellido': 'Prueba', 'segundo_apellido': 'López', 'curp': CURP}


class IdentidadLlaveMX(unittest.TestCase):

    def test_nacional_completo(self):
        i = identidad_llavemx(BASE)
        self.assertEqual(i['nombres'], 'DIANA')
        self.assertEqual(i['primer_apellido'], 'PRUEBA')
        self.assertEqual(i['segundo_apellido'], 'LÓPEZ')
        self.assertEqual(i['curp'], CURP)
        self.assertEqual(i['nombre_completo'], 'DIANA PRUEBA LÓPEZ')

    def test_segundo_apellido_vacio_se_fija(self):
        i = identidad_llavemx({**BASE, 'segundo_apellido': ''})
        self.assertEqual(i['segundo_apellido'], '')
        self.assertEqual(i['nombre_completo'], 'DIANA PRUEBA')

    def test_sin_nombre_o_primer_apellido_no_fija_nombres(self):
        for faltante in ('nombres', 'primer_apellido'):
            i = identidad_llavemx({**BASE, faltante: ''})
            self.assertIsNone(i['nombres'])
            self.assertIsNone(i['nombre_completo'])
            self.assertEqual(i['curp'], CURP)

    def test_extranjero_sin_curp_usa_generica(self):
        i = identidad_llavemx({**BASE, 'curp': '', 'es_extranjero': True})
        self.assertEqual(i['curp'], CURP_GENERICA)

    def test_curp_generica_implica_extranjero(self):
        i = identidad_llavemx({**BASE, 'curp': CURP_GENERICA})
        self.assertEqual(i['curp'], CURP_GENERICA)

    def test_nacional_sin_curp_no_fija_curp(self):
        self.assertIsNone(identidad_llavemx({**BASE, 'curp': ''})['curp'])

    def test_curp_invalida_no_se_fija(self):
        self.assertIsNone(identidad_llavemx({**BASE, 'curp': 'ABC'})['curp'])

    def test_details_vacios(self):
        i = identidad_llavemx(None)
        self.assertTrue(all(v is None for v in i.values()))


class RegistroNuevo(unittest.TestCase):
    AHORA = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)

    def test_create_user_lo_creo(self):
        self.assertTrue(es_registro_nuevo(None, True, False, self.AHORA))

    def test_formulario_lo_creo_hace_segundos(self):
        self.assertTrue(es_registro_nuevo(self.AHORA - timedelta(seconds=20), False, True, self.AHORA))

    def test_limite_de_la_ventana(self):
        self.assertTrue(es_registro_nuevo(self.AHORA - timedelta(minutes=10), False, True, self.AHORA))
        self.assertFalse(es_registro_nuevo(self.AHORA - timedelta(minutes=11), False, True, self.AHORA))

    def test_cuenta_antigua_que_se_liga_por_primera_vez(self):
        self.assertFalse(es_registro_nuevo(self.AHORA - timedelta(days=700), False, True, self.AHORA))

    def test_login_con_vinculo_existente(self):
        self.assertFalse(es_registro_nuevo(self.AHORA - timedelta(seconds=20), False, False, self.AHORA))

    def test_sin_fecha_de_alta(self):
        self.assertFalse(es_registro_nuevo(None, False, True, self.AHORA))

    def test_fecha_en_el_futuro(self):
        self.assertFalse(es_registro_nuevo(self.AHORA + timedelta(minutes=1), False, True, self.AHORA))


if __name__ == '__main__':
    unittest.main()
