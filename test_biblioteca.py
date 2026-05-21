"""
Suite de pruebas automatizadas — Sistema de Gestión de Préstamos de Biblioteca
Ejecutar con: pytest test_biblioteca.py -v
"""

import datetime

try:
    import pytest
except Exception:
    # Fallback minimal shim so editors/linters that can't resolve pytest
    # won't break. When running tests, ensure pytest is installed.
    class _FakePytest:
        def fixture(self, *a, **k):
            def _dec(f):
                return f
            return _dec
    pytest = _FakePytest()

# Importamos el código original. 
# Asegúrate de que el código original esté en un archivo llamado biblioteca.py en la misma carpeta.
from biblioteca import proc, usuarios_db, libros_db, prestamos_db

@pytest.fixture(autouse=True)
def reiniciar_bases_de_datos():
    """Fixture para limpiar las listas globales antes de cada caso de prueba."""
    usuarios_db.clear()
    libros_db.clear()
    prestamos_db.clear()

# ==========================================
# PRUEBAS DE REGISTRO DE USUARIOS (t = 1)
# ==========================================

def test_registrar_usuario_estudiante_exitoso():
    uid = proc(1, ["Ana Garcia", "ana@uni.edu", "E"])
    assert uid == 1
    assert len(usuarios_db) == 1
    assert usuarios_db[0]["n"] == "Ana Garcia"

def test_registrar_usuario_correo_invalido():
    uid = proc(1, ["Pedro Lopez", "pedro.uni.edu", "P"])  # Sin '@'
    assert uid == -1
    assert len(usuarios_db) == 0

def test_registrar_usuario_tipo_invalido():
    uid = proc(1, ["Juan Perez", "juan@uni.edu", "X"])  # Tipo 'X' no existe
    assert uid == -1

# ==========================================
# PRUEBAS DE REGISTRO DE LIBROS (t = 2)
# ==========================================

def test_registrar_libro_exitoso():
    lid = proc(2, ["Clean Code", "Robert Martin", 3])
    assert lid == 1
    assert libros_db[0]["tit"] == "Clean Code"
    assert libros_db[0]["disp"] == 3

def test_registrar_libro_ejemplares_invalidos():
    lid = proc(2, ["Design Patterns", "GoF", 0])  # Debe ser > 0
    assert lid == -1

# ==========================================
# PRUEBAS DE PRÉSTAMOS (t = 3)
# ==========================================
# Nota: Estas pruebas reflejan el comportamiento ideal. Debido a los bugs de 
# indentación del código original, es normal que fallen hasta que se parchee proc().

def test_prestamo_exitoso_estudiante():
    # Registrar prerrequisitos
    proc(1, ["Ana Garcia", "ana@uni.edu", "E"])
    proc(2, ["Clean Code", "Robert Martin", 3])
    
    hoy = datetime.datetime(2024, 5, 1)
    pid = proc(3, None, u_id=1, l_id=1, dt=hoy)
    
    # Si da -1, es por el bug de indentación del código original
    assert pid == 1 
    assert libros_db[0]["disp"] == 2

# ==========================================
# PRUEBAS DE DEVOLUCIONES (t = 4)
# ==========================================

def test_devolucion_a_tiempo():
    # Setup manual para evadir el bug del paso 3 si es necesario
    usuarios_db.append({"id": 1, "n": "Ana", "e": "a@u.com", "tipo": "E", "mult": 0, "act": True})
    libros_db.append({"id": 1, "tit": "Clean Code", "aut": "Bob", "ej": 3, "disp": 2})
    
    fp = datetime.datetime(2024, 5, 1)
    fd_esp = datetime.datetime(2024, 5, 8) # 7 días para estudiante
    prestamos_db.append({"id": 1, "u": 1, "l": 1, "fp": fp, "fd_esp": fd_esp, "dev": None})
    
    # Devolución justo el día esperado
    res = proc(4, 1, dt2=datetime.datetime(2024, 5, 8))
    assert res == 1
    assert libros_db[0]["disp"] == 3
    assert usuarios_db[0]["mult"] == 0

def test_devolucion_con_multa():
    usuarios_db.append({"id": 1, "n": "Ana", "e": "a@u.com", "tipo": "E", "mult": 0, "act": True})
    libros_db.append({"id": 1, "tit": "Clean Code", "aut": "Bob", "ej": 3, "disp": 2})
    
    fp = datetime.datetime(2024, 5, 1)
    fd_esp = datetime.datetime(2024, 5, 8)
    prestamos_db.append({"id": 1, "u": 1, "l": 1, "fp": fp, "fd_esp": fd_esp, "dev": None})
    
    # 3 días de retraso -> $3000 de multa
    res = proc(4, 1, dt2=datetime.datetime(2024, 5, 11))
    assert res == 1
    assert usuarios_db[0]["mult"] == 3000

# ==========================================
# PRUEBAS DE REPORTES (t = 5)
# ==========================================

def test_reporte_usuario_existente():
    usuarios_db.append({"id": 1, "n": "Ana", "e": "a@u.com", "tipo": "E", "mult": 0, "act": True})
    res = proc(5, None, u_id=1)
    assert res == 1

def test_reporte_usuario_no_existente():
    res = proc(5, None, u_id=999)
    assert res == -1