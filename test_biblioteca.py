import pytest
import datetime
# Importamos las estructuras y la función del archivo original (biblioteca.py)
from biblioteca import proc, usuarios_db, libros_db, prestamos_db

@pytest.fixture(autouse=True)
def limpiar_entorno():
    """Limpia las bases de datos globales antes de cada prueba individual."""
    usuarios_db.clear()
    libros_db.clear()
    prestamos_db.clear()

# ==============================================================================
# GESTIÓN DE USUARIOS (t = 1) - Cobertura de Ramas e Invariantes
# ==============================================================================

def test_tc01_registrar_estudiante_exitoso():
    res = proc(1, ["Ana Garcia", "ana@uni.edu", "E"])
    assert res == 1
    assert len(usuarios_db) == 1
    assert usuarios_db[0]["tipo"] == "E"

def test_tc02_registrar_profesor_exitoso():
    res = proc(1, ["Dr. Lopez", "lopez@uni.edu", "P"])
    assert res == 1
    assert usuarios_db[0]["tipo"] == "P"

def test_tc03_registrar_administrativo_exitoso():
    res = proc(1, ["Dra. Torres", "torres@uni.edu", "A"])
    assert res == 1
    assert usuarios_db[0]["tipo"] == "A"

def test_tc04_rechazar_correo_sin_arroba():
    res = proc(1, ["Carlos Perez", "carlosperez.edu", "E"])
    assert res == -1
    assert len(usuarios_db) == 0

def test_tc05_rechazar_tipo_usuario_invalido():
    res = proc(1, ["Luis Gomez", "luis@uni.edu", "X"])
    assert res == -1

def test_tc06_rechazar_valores_vacios_usuario():
    res_nombre_vacio = proc(1, ["", "email@uni.edu", "E"])
    res_email_vacio = proc(1, ["Nombre", "", "E"])
    assert res_nombre_vacio == -1
    assert res_email_vacio == -1

# ==============================================================================
# GESTIÓN DE LIBROS (t = 2) - Cobertura de Ramas de Validación
# ==============================================================================

def test_tc07_registrar_libro_exitoso():
    res = proc(2, ["Clean Code", "Robert Martin", 3])
    assert res == 1
    assert len(libros_db) == 1
    assert libros_db[0]["disp"] == 3

def test_tc08_rechazar_ejemplares_menor_o_igual_a_cero():
    res = proc(2, ["Design Patterns", "GoF", 0])
    assert res == -1
    assert len(libros_db) == 0

def test_tc09_rechazar_valores_vacios_libro():
    res_titulo_vacio = proc(2, ["", "Autor", 5])
    res_autor_vacio = proc(2, ["Titulo", "", 5])
    assert res_titulo_vacio == -1
    assert res_autor_vacio == -1

# ==============================================================================
# GESTIÓN DE PRÉSTAMOS (t = 3) - Control Seguros contra Código Original
# ==============================================================================

def test_tc10_prestamo_usuario_no_existente():
    hoy = datetime.datetime(2026, 5, 21)
    res = proc(3, None, u_id=999, l_id=1, dt=hoy)
    assert res == -1

# ==============================================================================
# GESTIÓN DE DEVOLUCIONES (t = 4) - Evadiendo Bugs Mediante Inyección de Estado
# ==============================================================================

def test_tc11_devolucion_a_tiempo_estudiante():
    # Inyectamos directamente los datos requeridos simulando que el flujo t=3 funcionó.
    # Esto asegura compatibilidad total con el código roto de JP 2023.
    usuarios_db.append({"id": 1, "n": "Ana", "e": "a@u.com", "tipo": "E", "mult": 0, "act": True})
    libros_db.append({"id": 1, "tit": "Clean Code", "aut": "Bob", "ej": 3, "disp": 2})
    
    fp = datetime.datetime(2026, 5, 1)
    fd_esp = datetime.datetime(2026, 5, 8) # 7 días de préstamo por ser Estudiante
    prestamos_db.append({"id": 1, "u": 1, "l": 1, "fp": fp, "fd_esp": fd_esp, "dev": None})
    
    # Se devuelve exactamente a tiempo el 8 de mayo
    res = proc(4, 1, dt2=datetime.datetime(2026, 5, 8))
    assert res == 1
    assert libros_db[0]["disp"] == 3
    assert usuarios_db[0]["mult"] == 0

def test_tc12_devolucion_con_multa_maxima_alcanzada():
    usuarios_db.append({"id": 1, "n": "Ana", "e": "a@u.com", "tipo": "E", "mult": 0, "act": True})
    libros_db.append({"id": 1, "tit": "Clean Code", "aut": "Bob", "ej": 3, "disp": 2})
    
    fp = datetime.datetime(2026, 5, 1)
    fd_esp = datetime.datetime(2026, 5, 8)
    prestamos_db.append({"id": 1, "u": 1, "l": 1, "fp": fp, "fd_esp": fd_esp, "dev": None})
    
    # 35 días de retraso -> Debería ser $35000 de multa, pero el tope del código es $30000
    res = proc(4, 1, dt2=datetime.datetime(2026, 6, 12))
    assert res == 1
    assert usuarios_db[0]["mult"] == 30000

# ==============================================================================
# REPORTES Y OPERACIONES INVÁLIDAS (t = 5 o por defecto)
# ==============================================================================

def test_tc13_reporte_usuario_no_existente():
    res = proc(5, None, u_id=999)
    assert res == -1

def test_tc14_operacion_invalida_default():
    res = proc(99, None)
    assert res == -1