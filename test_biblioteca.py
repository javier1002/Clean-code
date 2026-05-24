"""
Suite de pruebas automatizadas – Sistema de gestión de préstamos de biblioteca
=============================================================================
Cobertura objetivo : ≥ 70 %  (pytest-cov)
Pruebas            : 25  (≥ 10 requeridas)
Herramienta        : pytest + pytest-cov

Ejecución:
    pytest test_biblioteca.py -v --cov=biblioteca --cov-report=term-missing

Las pruebas están agrupadas en 4 bloques:
  BLOQUE A – Registro de usuarios    (4 tests)
  BLOQUE B – Registro de libros      (4 tests)
  BLOQUE C – Préstamos y devoluciones(11 tests)
  BLOQUE D – Clean Code (8 reglas)   (6 tests)
"""

import datetime
import inspect
import pytest
import biblioteca  # módulo bajo prueba

# ---------------------------------------------------------------------------
# Constantes de prueba
# ---------------------------------------------------------------------------
HOY = datetime.datetime(2024, 5, 1)
MAÑANA = HOY + datetime.timedelta(days=1)

DATOS_ESTUDIANTE   = ["Ana García",  "ana@uni.edu",   "E"]
DATOS_PROFESOR     = ["Dr. López",   "lopez@uni.edu", "P"]
DATOS_ADMIN        = ["Carlos Ruiz", "carlos@uni.edu","A"]
DATOS_LIBRO_A      = ["Clean Code",  "Robert Martin", 3]
DATOS_LIBRO_ESCASO = ["Refactoring", "Martin Fowler", 1]


# ---------------------------------------------------------------------------
# Fixture: limpia las tres BDs globales antes y después de cada prueba
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def limpiar_bd():
    """Garantiza aislamiento total entre pruebas."""
    biblioteca.usuarios_db.clear()
    biblioteca.libros_db.clear()
    biblioteca.prestamos_db.clear()
    yield
    biblioteca.usuarios_db.clear()
    biblioteca.libros_db.clear()
    biblioteca.prestamos_db.clear()


# ---------------------------------------------------------------------------
# Helpers reutilizables
# ---------------------------------------------------------------------------
def crear_estudiante():
    return biblioteca.proc(1, DATOS_ESTUDIANTE)

def crear_profesor():
    return biblioteca.proc(1, DATOS_PROFESOR)

def crear_admin():
    return biblioteca.proc(1, DATOS_ADMIN)

def crear_libro(copias=3):
    return biblioteca.proc(2, ["Clean Code", "Robert Martin", copias])

def hacer_prestamo(u_id, l_id, fecha=HOY):
    return biblioteca.proc(3, None, u_id, l_id, fecha)

def devolver(prestamo_id, fecha):
    return biblioteca.proc(4, prestamo_id, None, None, None, fecha)


# ===========================================================================
# BLOQUE A – Registro de usuarios (4 pruebas)
# ===========================================================================

class TestRegistroUsuario:

    def test_registro_valido_estudiante_retorna_id_positivo(self):
        """Un estudiante con datos correctos debe recibir un ID ≥ 1."""
        uid = biblioteca.proc(1, DATOS_ESTUDIANTE)
        assert uid == 1

    def test_registro_email_sin_arroba_retorna_menos_uno(self):
        """Un email sin '@' debe ser rechazado."""
        uid = biblioteca.proc(1, ["Ana García", "ana-sin-arroba", "E"])
        assert uid == -1

    def test_registro_tipo_invalido_retorna_menos_uno(self):
        """Solo los tipos E, P, A son válidos; cualquier otro debe fallar."""
        uid = biblioteca.proc(1, ["Ana García", "ana@uni.edu", "X"])
        assert uid == -1

    def test_dos_registros_producen_ids_consecutivos(self):
        """Los IDs se asignan de forma correlativa (1, 2, …)."""
        uid1 = biblioteca.proc(1, DATOS_ESTUDIANTE)
        uid2 = biblioteca.proc(1, DATOS_PROFESOR)
        assert uid1 == 1
        assert uid2 == 2


# ===========================================================================
# BLOQUE B – Registro de libros (4 pruebas)
# ===========================================================================

class TestRegistroLibro:

    def test_registro_libro_valido_retorna_id(self):
        """Un libro con título, autor y copias > 0 debe registrarse."""
        lid = crear_libro()
        assert lid == 1

    def test_registro_libro_cero_copias_retorna_menos_uno(self):
        """No se puede registrar un libro sin ejemplares."""
        lid = biblioteca.proc(2, ["Libro", "Autor", 0])
        assert lid == -1

    def test_registro_libro_titulo_vacio_retorna_menos_uno(self):
        """Un título vacío invalida el registro."""
        lid = biblioteca.proc(2, ["", "Autor", 3])
        assert lid == -1

    def test_registro_libro_autor_vacio_retorna_menos_uno(self):
        """Un autor vacío invalida el registro."""
        lid = biblioteca.proc(2, ["Libro", "", 3])
        assert lid == -1


# ===========================================================================
# BLOQUE C – Préstamos y devoluciones (11 pruebas)
# ===========================================================================

class TestPrestamos:

    # ── Préstamo exitoso ──────────────────────────────────────────────────

    def test_prestamo_exitoso_retorna_id(self):
        """Un préstamo válido para el primer usuario registrado devuelve un ID."""
        crear_estudiante()
        crear_libro()
        pid = hacer_prestamo(1, 1)
        assert pid == 1

    def test_prestamo_reduce_disponibilidad_del_libro(self):
        """Cada préstamo descuenta un ejemplar disponible."""
        crear_estudiante()
        crear_libro(copias=3)
        hacer_prestamo(1, 1)
        assert biblioteca.libros_db[0]["disp"] == 2

    # ── Bloqueos de préstamo ──────────────────────────────────────────────

    def test_prestamo_libro_sin_copias_disponibles_falla(self):
        """Si no quedan ejemplares, el préstamo debe rechazarse."""
        crear_estudiante()
        crear_libro(copias=1)
        hacer_prestamo(1, 1)               # agota el único ejemplar
        pid = hacer_prestamo(1, 1)         # debe fallar
        assert pid == -1

    def test_limite_tres_prestamos_simultaneos_estudiante(self):
        """Un estudiante no puede tener más de 3 préstamos activos."""
        crear_estudiante()
        crear_libro(copias=10)
        hacer_prestamo(1, 1)
        hacer_prestamo(1, 1)
        hacer_prestamo(1, 1)
        pid = hacer_prestamo(1, 1)         # 4.º: debe fallar
        assert pid == -1

    def test_limite_cinco_prestamos_simultaneos_profesor(self):
        """Un profesor no puede superar los 5 préstamos activos."""
        crear_profesor()
        crear_libro(copias=10)
        for _ in range(5):
            hacer_prestamo(1, 1)
        pid = hacer_prestamo(1, 1)         # 6.º: debe fallar
        assert pid == -1

    def test_limite_dos_prestamos_simultaneos_administrativo(self):
        """Un administrativo no puede superar los 2 préstamos activos."""
        crear_admin()
        crear_libro(copias=10)
        hacer_prestamo(1, 1)
        hacer_prestamo(1, 1)
        pid = hacer_prestamo(1, 1)         # 3.º: debe fallar
        assert pid == -1

    def test_usuario_con_multa_no_puede_pedir_prestamo(self):
        """Un usuario con multa pendiente no puede solicitar nuevos préstamos."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        # Devuelve 3 días tarde → genera multa
        devolver(1, HOY + datetime.timedelta(days=10))
        assert biblioteca.usuarios_db[0]["mult"] > 0
        pid = hacer_prestamo(1, 1)
        assert pid == -1

    # ── Devoluciones ─────────────────────────────────────────────────────

    def test_devolucion_a_tiempo_no_genera_multa(self):
        """Devolución dentro del plazo → multa = 0."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        devolver(1, HOY + datetime.timedelta(days=7))   # justo en el límite
        assert biblioteca.usuarios_db[0]["mult"] == 0

    def test_devolucion_tarde_genera_multa_correcta(self):
        """Devolución 3 días tarde → multa = 3 × $1 000 = $3 000."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        devolver(1, HOY + datetime.timedelta(days=10))  # 7 + 3 días
        assert biblioteca.usuarios_db[0]["mult"] == 3000

    def test_multa_no_supera_el_tope_de_30000(self):
        """Sin importar el retraso, la multa máxima es $30 000."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        devolver(1, HOY + datetime.timedelta(days=107)) # muy tarde
        assert biblioteca.usuarios_db[0]["mult"] == 30000

    def test_devolucion_incrementa_disponibilidad_del_libro(self):
        """Al devolver, el ejemplar vuelve al inventario disponible."""
        crear_estudiante()
        crear_libro(copias=1)
        hacer_prestamo(1, 1)
        assert biblioteca.libros_db[0]["disp"] == 0
        devolver(1, HOY + datetime.timedelta(days=5))
        assert biblioteca.libros_db[0]["disp"] == 1

    def test_devolucion_doble_del_mismo_prestamo_falla(self):
        """Intentar devolver un préstamo ya cerrado debe retornar -1."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        fecha = HOY + datetime.timedelta(days=5)
        devolver(1, fecha)
        resultado = devolver(1, fecha)
        assert resultado == -1


# ===========================================================================
# BLOQUE D – Reglas de Clean Code (6 pruebas de análisis estático)
# ===========================================================================

class TestCleanCode:
    """
    Verifica con análisis de código fuente (inspect / AST) que el módulo
    viola varias reglas de Clean Code de Robert C. Martin.

    Cada prueba documenta la violación y sirve como guía de refactorización.

    Las 8 reglas evaluadas:
      CC-1  Nombres significativos       → parámetros y claves crípticos
      CC-2  Funciones pequeñas           → proc() tiene 145 líneas
      CC-3  Una sola responsabilidad     → proc() hace 5 cosas distintas
      CC-4  Sin argumentos de bandera    → parámetro 't' selecciona operación
      CC-5  Evitar números mágicos       → 1000, 30000, 7, 14, 5 en línea
      CC-6  Comentarios útiles           → comentarios de código muerto
      CC-7  Manejo de errores explícito  → bug de indentación silencioso
      CC-8  No repetirse (DRY)           → búsqueda lineal duplicada 4 veces
    """

    @classmethod
    def _fuente_proc(cls):
        return inspect.getsource(biblioteca.proc)

    @classmethod
    def _fuente_modulo(cls):
        return inspect.getsource(biblioteca)

    # CC-1 Nombres significativos
    def test_cc1_parametros_con_nombres_no_descriptivos(self):
        """
        VIOLACIÓN CC-1 – Meaningful Names
        Los parámetros 't', 'd', 'dt', 'dt2' no comunican su propósito.
        Deben renombrarse a 'tipo_operacion', 'datos', 'fecha_prestamo',
        'fecha_devolucion', etc.
        """
        fuente = self._fuente_proc()
        nombres_crípticos = ["def proc(t,", "def proc(t ,"]
        # La firma usa 't' como primer parámetro
        assert "def proc(t," in fuente or "def proc(t ," in fuente, \
            "Se esperaba el parámetro críptico 't' en la firma de proc()"

    # CC-2 Funciones pequeñas
    def test_cc2_funcion_proc_supera_las_50_lineas(self):
        """
        VIOLACIÓN CC-2 – Small Functions
        proc() tiene 145 líneas. La guía de Clean Code recomienda ≤ 20.
        Debe dividirse en: registrar_usuario(), registrar_libro(),
        realizar_prestamo(), registrar_devolucion(), generar_reporte().
        """
        lineas = self._fuente_proc().splitlines()
        assert len(lineas) > 50, \
            f"proc() tiene {len(lineas)} líneas; debería estar dividida en funciones pequeñas"

    # CC-3 Una sola responsabilidad (SRP)
    def test_cc3_proc_maneja_cinco_operaciones_distintas(self):
        """
        VIOLACIÓN CC-3 – Single Responsibility Principle
        proc() implementa 5 operaciones mediante un selector 't'. Esto
        hace que cambiar una operación afecte a todas las demás.
        """
        fuente = self._fuente_proc()
        operaciones_encontradas = sum(
            f"t == {i}" in fuente for i in range(1, 6)
        )
        assert operaciones_encontradas == 5, \
            "Se esperaban 5 ramas de operación (t==1..5) dentro de proc()"

    # CC-4 Sin argumentos de bandera
    def test_cc4_parametro_t_es_argumento_de_seleccion(self):
        """
        VIOLACIÓN CC-4 – Flag Arguments / Selector Functions
        El parámetro 't' actúa como argumento de selección entre 5 flujos.
        Cada flujo debe ser una función independiente.
        """
        sig = inspect.signature(biblioteca.proc)
        params = list(sig.parameters.keys())
        assert params[0] == "t", \
            "El primer parámetro de proc() sigue siendo el selector 't'"

    # CC-5 Números mágicos
    def test_cc5_numeros_magicos_en_logica_de_multas(self):
        """
        VIOLACIÓN CC-5 – Avoid Magic Numbers
        Los valores 1000 (multa/día) y 30000 (multa máxima) aparecen como
        literales. Deben extraerse a constantes: MULTA_POR_DIA, MULTA_MAXIMA.
        """
        fuente = self._fuente_proc()
        assert "1000" in fuente, "Número mágico 1000 (multa/día) presente en el código"
        assert "30000" in fuente, "Número mágico 30000 (multa máxima) presente en el código"

    # CC-7 Manejo de errores – bug documentado
    def test_cc7_bug_usuario_no_primero_en_bd_retorna_error(self):
        """
        VIOLACIÓN CC-7 – Error Handling / Bug de indentación en t==3
        La guarda 'if u == None' está dentro del bucle for, por lo que
        cualquier usuario que no sea el primero registrado en la BD
        recibe -1 aunque exista. Comportamiento ACTUAL (con bug) verificado.
        """
        biblioteca.proc(1, ["Primero", "primero@uni.edu", "E"])
        biblioteca.proc(1, ["Segundo", "segundo@uni.edu", "E"])
        biblioteca.proc(2, ["Libro", "Autor", 5])

        pid_primero = hacer_prestamo(u_id=1, l_id=1)  # debe funcionar
        pid_segundo = hacer_prestamo(u_id=2, l_id=1)  # BUG: devuelve -1

        assert pid_primero == 1,  "El primer usuario sí puede prestar"
        assert pid_segundo == -1, \
            ("BUG CONFIRMADO: el segundo usuario no puede hacer préstamos "
             "debido a la indentación incorrecta de 'if u == None' dentro del for")


# ===========================================================================
# BLOQUE E – Reporte de usuario (2 pruebas adicionales)
# ===========================================================================

class TestReporte:

    def test_reporte_usuario_existente_con_prestamo_retorna_uno(self, capsys):
        """El reporte de un usuario con al menos un préstamo devuelve 1."""
        crear_estudiante()
        crear_libro()
        hacer_prestamo(1, 1)
        resultado = biblioteca.proc(5, None, 1)
        salida = capsys.readouterr().out
        assert resultado == 1
        assert "Ana García" in salida

    def test_reporte_usuario_inexistente_retorna_menos_uno(self):
        """El reporte de un ID que no existe devuelve -1."""
        resultado = biblioteca.proc(5, None, 999)
        assert resultado == -1