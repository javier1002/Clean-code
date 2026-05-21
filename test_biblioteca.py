import pytest
import datetime
from abc import ABC
import biblioteca  # Módulo original que contiene proc, usuarios_db, libros_db, etc.

# ==============================================================================
# PATRÓN: FACTORY (Generador robusto de entidades de prueba)
# ==============================================================================
class EntidadTestDataFactory:
    """Fábrica encargada de centralizar la creación de cargas útiles y estados 
    para mitigar la redundancia de datos bajo criterios de mantenibilidad ISO."""
    
    @staticmethod
    def crear_usuario_payload(nombre="Alvaro Arroyo", email="alvaro@uni.edu", tipo="E"):
        return [nombre, email, tipo]
        
    @staticmethod
    def crear_libro_payload(titulo="Clean Code", autor="Robert Martin", ejemplares=3):
        return [titulo, autor, ejemplares]

    @staticmethod
    def inyectar_usuario_en_db(uid, tipo="E", mult=0, activo=True):
        return {"id": uid, "n": "Test User", "e": "user@uni.edu", "tipo": tipo, "mult": mult, "act": activo}

    @staticmethod
    def inyectar_libro_en_db(lid, ejemplares=3, disponibles=2):
        return {"id": lid, "tit": "Test Book", "aut": "Test Author", "ej": ejemplares, "disp": disponibles}

    @staticmethod
    def inyectar_prestamo_en_db(pid, uid, lid, dias_atraso=0):
        fp = datetime.datetime(2026, 5, 1)
        # 7 días estándar para estudiantes en el sistema original
        fd_esp = fp + datetime.timedelta(days=7) 
        f_dev = fd_esp + datetime.timedelta(days=dias_atraso) if dias_atraso > 0 else None
        return {
            "id": pid, 
            "u": uid, 
            "l": lid, 
            "fp": fp, 
            "fd_esp": fd_esp, 
            "dev": f_dev
        }


# ==============================================================================
# INYECCIÓN DE DEPENDENCIAS: Contexto de Persistencia Aislado
# ==============================================================================
class ContextoBibliotecaDB:
    """Componente intermedio de abstracción. Permite inyectar el control de 
    las listas globales de biblioteca de forma segura y rastreable."""
    def __init__(self, modulo_target):
        self._mod = modulo_target

    def purgar_todo(self):
        self._mod.usuarios_db.clear()
        self._mod.libros_db.clear()
        self._mod.prestamos_db.clear()

    def obtener_usuarios(self): return self._mod.usuarios_db
    def obtener_libros(self): return self._mod.libros_db
    def obtener_prestamos(self): return self._mod.prestamos_db


# ==============================================================================
# JERARQUÍA DE HERENCIA: Estructura Base de Pruebas Automatizadas (ISO 25010)
# ==============================================================================
class BaseBibliotecaTest(ABC):
    """Clase Base Abstracta del Sistema de Pruebas. Define el contrato operativo 
    y el aislamiento de dependencias de bajo nivel."""
    
    @pytest.fixture(autouse=True)
    def setup_contexto(self):
        # Inyección de dependencias a través del constructor del contexto adaptado
        self.db_context = ContextoBibliotecaDB(biblioteca)
        self.db_context.purgar_todo()
        self.factory = EntidadTestDataFactory


# ==============================================================================
# SUBCLASE 1: Validaciones de Datos e Invariantes del Dominio
# ==============================================================================
class TestOperacionesUnitarias(BaseBibliotecaTest):
    """Subclase enfocada en la robustez y análisis de límites funcionales (t=1, t=2)."""

    def test_tc01_registrar_estudiante_exitoso(self):
        payload = self.factory.crear_usuario_payload(tipo="E")
        res = biblioteca.proc(1, payload)
        assert res == 1
        assert len(self.db_context.obtener_usuarios()) == 1

    def test_tc02_registrar_profesor_exitoso(self):
        payload = self.factory.crear_usuario_payload(tipo="P")
        res = biblioteca.proc(1, payload)
        assert res == 1
        assert self.db_context.obtener_usuarios()[0]["tipo"] == "P"

    def test_tc03_registrar_administrativo_exitoso(self):
        payload = self.factory.crear_usuario_payload(tipo="A")
        res = biblioteca.proc(1, payload)
        assert res == 1
        assert self.db_context.obtener_usuarios()[0]["tipo"] == "A"

    def test_tc04_rechazar_correo_sin_arroba(self):
        payload = self.factory.crear_usuario_payload(email="correo_invalido.com")
        res = biblioteca.proc(1, payload)
        assert res == -1

    def test_tc05_rechazar_tipo_usuario_desconocido(self):
        payload = self.factory.crear_usuario_payload(tipo="X")
        res = biblioteca.proc(1, payload)
        assert res == -1

    def test_tc06_rechazar_campo_nombre_vacio(self):
        payload = self.factory.crear_usuario_payload(nombre="")
        res = biblioteca.proc(1, payload)
        assert res == -1

    def test_tc07_registrar_libro_con_stock_valido(self):
        payload = self.factory.crear_libro_payload(ejemplares=5)
        res = biblioteca.proc(2, payload)
        assert res == 1
        assert self.db_context.obtener_libros()[0]["disp"] == 5

    def test_tc08_rechazar_libro_con_stock_cero(self):
        payload = self.factory.crear_libro_payload(ejemplares=0)
        res = biblioteca.proc(2, payload)
        assert res == -1

    def test_tc09_rechazar_libro_con_autor_vacio(self):
        payload = self.factory.crear_libro_payload(autor="")
        res = biblioteca.proc(2, payload)
        assert res == -1


# ==============================================================================
# SUBCLASE 2: Pruebas Basadas en Estado e Integración Segura (Tolerancia a fallos)
# ==============================================================================
class TestOperacionesEstadoInyectado(BaseBibliotecaTest):
    """Subclase que inyecta estados específicos en los repositorios para evaluar
    lógicas transaccionales y de cálculo financiero (t=3, t=4, t=5)."""

    def test_tc10_prestamo_usuario_no_existente(self):
        hoy = datetime.datetime(2026, 5, 21)
        res = biblioteca.proc(3, None, u_id=404, l_id=1, dt=hoy)
        assert res == -1

    def test_tc11_devolucion_consistente_a_tiempo(self):
        # Inyección controlada vía DI
        self.db_context.obtener_usuarios().append(self.factory.inyectar_usuario_en_db(uid=10))
        self.db_context.obtener_libros().append(self.factory.inyectar_libro_en_db(lid=5, disponibles=1))
        self.db_context.obtener_prestamos().append(self.factory.inyectar_prestamo_en_db(pid=1, uid=10, lid=5))

        # Se retorna el día exacto de la fecha esperada
        fecha_retorno = datetime.datetime(2026, 5, 8)
        res = biblioteca.proc(4, d=1, dt2=fecha_retorno)
        
        assert res == 1
        assert self.db_context.obtener_libros()[0]["disp"] == 2
        assert self.db_context.obtener_usuarios()[0]["mult"] == 0

    def test_tc12_devolucion_tardia_aplica_tope_multa(self):
        self.db_context.obtener_usuarios().append(self.factory.inyectar_usuario_en_db(uid=11))
        self.db_context.obtener_libros().append(self.factory.inyectar_libro_en_db(lid=6))
        self.db_context.obtener_prestamos().append(self.factory.inyectar_prestamo_en_db(pid=2, uid=11, lid=6))

        # 40 días de retraso exceden el tope máximo de $30.000 de la regla de negocio
        fecha_tardia = datetime.datetime(2026, 6, 17)
        res = biblioteca.proc(4, d=2, dt2=fecha_tardia)
        
        assert res == 1
        assert self.db_context.obtener_usuarios()[0]["mult"] == 30000

    def test_tc13_reporte_falla_usuario_inexistente(self):
        res = biblioteca.proc(5, None, u_id=999)
        assert res == -1

    def test_tc14_codigo_operacion_invalido_retorna_error(self):
        res = biblioteca.proc(999, None)
        assert res == -1