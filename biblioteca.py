"""
biblioteca.py
=============
Sistema de gestión de préstamos de biblioteca.

Estado único: un solo conjunto de listas (usuarios_db, libros_db, prestamos_db)
con objetos que soportan tanto acceso por atributo (.disp) como por clave (["disp"]),
eliminando la doble representación dict/objeto de la versión anterior.
"""

import datetime
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Constantes de dominio
# ---------------------------------------------------------------------------

MULTA_POR_DIA = 1_000
MULTA_MAXIMA  = 30_000


class TipoUsuario(str, Enum):
    ESTUDIANTE     = "E"
    PROFESOR       = "P"
    ADMINISTRATIVO = "A"


LIMITE_PRESTAMOS: dict[TipoUsuario, int] = {
    TipoUsuario.ESTUDIANTE:     3,
    TipoUsuario.PROFESOR:       5,
    TipoUsuario.ADMINISTRATIVO: 2,
}

DIAS_PRESTAMO: dict[TipoUsuario, int] = {
    TipoUsuario.ESTUDIANTE:     7,
    TipoUsuario.PROFESOR:      14,
    TipoUsuario.ADMINISTRATIVO: 5,
}


# ---------------------------------------------------------------------------
# Excepciones — solo las que tienen un caller que las distingue
# ---------------------------------------------------------------------------

class ErrorBiblioteca(Exception):
    pass

class UsuarioNoEncontrado(ErrorBiblioteca):
    pass

class LibroNoEncontrado(ErrorBiblioteca):
    pass

class PrestamoNoEncontrado(ErrorBiblioteca):
    pass

class PrestamoYaDevuelto(ErrorBiblioteca):
    pass


# ---------------------------------------------------------------------------
# Entidades
#
# __getitem__ permite que los tests usen obj["disp"] / obj["mult"]
# sin necesidad de mantener una lista paralela de dicts.
# ---------------------------------------------------------------------------

@dataclass
class Usuario:
    id:     int
    nombre: str
    email:  str
    tipo:   TipoUsuario
    mult:   int  = 0
    activo: bool = True

    def __getitem__(self, key: str):
        return getattr(self, key)


@dataclass
class Libro:
    id:   int
    tit:  str
    aut:  str
    ej:   int
    disp: int

    def __getitem__(self, key: str):
        return getattr(self, key)


@dataclass
class Prestamo:
    id:     int
    u:      int
    l:      int
    fp:     datetime.datetime
    fd_esp: datetime.datetime
    dev:    datetime.datetime | None = None

    def __getitem__(self, key: str):
        return getattr(self, key)


# ---------------------------------------------------------------------------
# Estado global — único, sin espejo
# ---------------------------------------------------------------------------

usuarios_db:  list[Usuario]  = []
libros_db:    list[Libro]    = []
prestamos_db: list[Prestamo] = []


# ---------------------------------------------------------------------------
# Búsquedas (DRY)
# ---------------------------------------------------------------------------

def _buscar_usuario(usuario_id: int) -> Usuario:
    for u in usuarios_db:
        if u.id == usuario_id:
            return u
    raise UsuarioNoEncontrado(f"No existe el usuario {usuario_id}")


def _buscar_libro(libro_id: int) -> Libro:
    for l in libros_db:
        if l.id == libro_id:
            return l
    raise LibroNoEncontrado(f"No existe el libro {libro_id}")


def _buscar_prestamo(prestamo_id: int) -> Prestamo:
    for p in prestamos_db:
        if p.id == prestamo_id:
            return p
    raise PrestamoNoEncontrado(f"No existe el préstamo {prestamo_id}")


# ---------------------------------------------------------------------------
# Operaciones de negocio
# ---------------------------------------------------------------------------

def _registrar_usuario(nombre: str, email: str, tipo_str: str) -> int:
    if not nombre or not email or "@" not in email:
        return -1
    try:
        tipo = TipoUsuario(tipo_str)
    except ValueError:
        return -1
    nuevo_id = len(usuarios_db) + 1
    usuarios_db.append(Usuario(id=nuevo_id, nombre=nombre, email=email, tipo=tipo))
    print(f"Usuario registrado: {nombre}")
    return nuevo_id


def _registrar_libro(titulo: str, autor: str, ejemplares: int) -> int:
    if not titulo or not autor or ejemplares <= 0:
        return -1
    nuevo_id = len(libros_db) + 1
    libros_db.append(Libro(id=nuevo_id, tit=titulo, aut=autor, ej=ejemplares, disp=ejemplares))
    print(f"Libro registrado: {titulo}")
    return nuevo_id


def _validar_usuario_para_prestamo(usuario: Usuario) -> str | None:
    """Devuelve un mensaje de error, o None si el usuario puede pedir prestado."""
    if not usuario.activo:
        return "usuario inactivo"
    if usuario.mult > 0:
        return "usuario tiene multas"
    activos = sum(1 for p in prestamos_db if p.u == usuario.id and p.dev is None)
    if activos >= LIMITE_PRESTAMOS[usuario.tipo]:
        return "límite de préstamos alcanzado"
    return None


def _registrar_prestamo(usuario_id: int, libro_id: int, fecha: datetime.datetime) -> int:
    try:
        usuario = _buscar_usuario(usuario_id)
    except UsuarioNoEncontrado:
        print("Error: usuario no existe")
        return -1

    error = _validar_usuario_para_prestamo(usuario)
    if error:
        print(f"Error: {error}")
        return -1

    try:
        libro = _buscar_libro(libro_id)
    except LibroNoEncontrado:
        print("Error: libro no existe")
        return -1

    if libro.disp <= 0:
        print("Error: no hay ejemplares disponibles")
        return -1

    fecha_esperada = fecha + datetime.timedelta(days=DIAS_PRESTAMO[usuario.tipo])
    nuevo_id = len(prestamos_db) + 1
    prestamos_db.append(Prestamo(
        id=nuevo_id, u=usuario_id, l=libro_id, fp=fecha, fd_esp=fecha_esperada,
    ))
    libro.disp -= 1
    print("Préstamo registrado")
    return nuevo_id


def _calcular_multa(prestamo: Prestamo, fecha_devolucion: datetime.datetime) -> int:
    if fecha_devolucion <= prestamo.fd_esp:
        return 0
    dias = (fecha_devolucion - prestamo.fd_esp).days
    return min(dias * MULTA_POR_DIA, MULTA_MAXIMA)


def _devolver_libro(prestamo_id: int, fecha: datetime.datetime) -> int:
    try:
        prestamo = _buscar_prestamo(prestamo_id)
    except PrestamoNoEncontrado:
        return -1

    if prestamo.dev is not None:
        print("Error: ya fue devuelto")
        return -1

    prestamo.dev = fecha
    _buscar_libro(prestamo.l).disp += 1

    multa = _calcular_multa(prestamo, fecha)
    if multa > 0:
        _buscar_usuario(prestamo.u).mult += multa
        print(f"Devuelto con multa: ${multa}")
    else:
        print("Devuelto a tiempo")
    return 1


def _reporte_usuario(usuario_id: int) -> int:
    try:
        usuario = _buscar_usuario(usuario_id)
    except UsuarioNoEncontrado:
        return -1

    prestamos_usuario = [p for p in prestamos_db if p.u == usuario_id]
    if not prestamos_usuario:
        return -1

    print("=== Reporte ===")
    print(f"Nombre: {usuario.nombre}")
    print(f"Email:  {usuario.email}")
    print(f"Tipo:   {usuario.tipo.name.capitalize()}")
    print(f"Multas: ${usuario.mult}")
    for prestamo in prestamos_usuario:
        titulo = _buscar_libro(prestamo.l).tit
        estado = "Activo" if prestamo.dev is None else "Devuelto"
        print(f"  - {titulo} [{estado}]")
    return 1


# ---------------------------------------------------------------------------
# API legacy
# ---------------------------------------------------------------------------

def proc(t, d, u_id=None, l_id=None, dt=None, dt2=None):
    """Punto de entrada requerido por la suite de pruebas."""
    if t == 1:
        return _registrar_usuario(d[0], d[1], d[2])
    if t == 2:
        return _registrar_libro(d[0], d[1], d[2])
    if t == 3:
        return _registrar_prestamo(u_id, l_id, dt)
    if t == 4:
        return _devolver_libro(d, dt2)
    if t == 5:
        return _reporte_usuario(u_id)
    return -1


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    hoy = datetime.datetime(2024, 5, 1)
    proc(1, ["Ana Garcia", "ana@uni.edu", "E"])
    proc(1, ["Dr. Lopez",  "lopez@uni.edu", "P"])
    proc(2, ["Clean Code",  "Robert Martin", 3])
    proc(2, ["Refactoring", "Martin Fowler", 2])
    proc(3, None, 1, 1, hoy)
    proc(3, None, 2, 2, hoy)
    proc(4, 1, None, None, None, datetime.datetime(2024, 5, 15))
    proc(5, None, 1)
    proc(5, None, 2)