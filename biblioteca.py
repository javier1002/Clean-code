"""
biblioteca.py — Versión autocontenida
======================================
Toda la lógica vive en este único archivo.
Expone la API legacy (proc, usuarios_db, libros_db, prestamos_db)
que espera la suite de pruebas, implementada con código limpio internamente.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
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

_TIPO_STR: dict[str, TipoUsuario] = {
    "E": TipoUsuario.ESTUDIANTE,
    "P": TipoUsuario.PROFESOR,
    "A": TipoUsuario.ADMINISTRATIVO,
}


# ---------------------------------------------------------------------------
# Excepciones de dominio
# ---------------------------------------------------------------------------

class ErrorBiblioteca(Exception):
    pass

class UsuarioNoEncontrado(ErrorBiblioteca):
    pass

class LibroNoEncontrado(ErrorBiblioteca):
    pass

class PrestamoNoEncontrado(ErrorBiblioteca):
    pass

class UsuarioInactivo(ErrorBiblioteca):
    pass

class UsuarioConMultas(ErrorBiblioteca):
    pass

class LimitePrestamosAlcanzado(ErrorBiblioteca):
    pass

class SinEjemplaresDisponibles(ErrorBiblioteca):
    pass

class PrestamoYaDevuelto(ErrorBiblioteca):
    pass


# ---------------------------------------------------------------------------
# Entidades
# ---------------------------------------------------------------------------

@dataclass
class _Usuario:
    id:     int
    nombre: str
    email:  str
    tipo:   TipoUsuario
    multas: int  = 0
    activo: bool = True


@dataclass
class _Libro:
    id:          int
    titulo:      str
    autor:       str
    ejemplares:  int
    disponibles: int


@dataclass
class _Prestamo:
    id:               int
    usuario_id:       int
    libro_id:         int
    fecha_prestamo:   datetime.datetime
    fecha_esperada:   datetime.datetime
    fecha_devolucion: datetime.datetime | None = None


# ---------------------------------------------------------------------------
# Estado interno (listas de objetos, nunca expuestas directamente)
# ---------------------------------------------------------------------------

_usuarios:  list[_Usuario]  = []
_libros:    list[_Libro]    = []
_prestamos: list[_Prestamo] = []


# ---------------------------------------------------------------------------
# Listas legacy que los tests leen/limpian directamente
# Cada operación las mantiene sincronizadas con el estado interno.
# ---------------------------------------------------------------------------

usuarios_db: list[dict] = []
libros_db:   list[dict] = []
prestamos_db: list[dict] = []


def _sync_legacy() -> None:
    """Vuelca el estado interno hacia las listas legacy que leen los tests."""
    usuarios_db.clear()
    for u in _usuarios:
        usuarios_db.append({
            "id": u.id, "n": u.nombre, "e": u.email,
            "tipo": u.tipo.value, "mult": u.multas, "act": u.activo,
        })
    libros_db.clear()
    for l in _libros:
        libros_db.append({
            "id": l.id, "tit": l.titulo, "aut": l.autor,
            "ej": l.ejemplares, "disp": l.disponibles,
        })
    prestamos_db.clear()
    for p in _prestamos:
        prestamos_db.append({
            "id": p.id, "u": p.usuario_id, "l": p.libro_id,
            "fp": p.fecha_prestamo, "fd_esp": p.fecha_esperada, "dev": p.fecha_devolucion,
        })


def _load_from_legacy() -> None:
    """Reconstruye el estado interno desde las listas legacy.

    Necesario porque el fixture de pytest llama .clear() directamente
    sobre usuarios_db/libros_db/prestamos_db sin pasar por esta capa.
    """
    _usuarios.clear()
    for u in usuarios_db:
        _usuarios.append(_Usuario(
            id=u["id"], nombre=u["n"], email=u["e"],
            tipo=TipoUsuario(u["tipo"]), multas=u["mult"], activo=u["act"],
        ))
    _libros.clear()
    for l in libros_db:
        _libros.append(_Libro(
            id=l["id"], titulo=l["tit"], autor=l["aut"],
            ejemplares=l["ej"], disponibles=l["disp"],
        ))
    _prestamos.clear()
    for p in prestamos_db:
        _prestamos.append(_Prestamo(
            id=p["id"], usuario_id=p["u"], libro_id=p["l"],
            fecha_prestamo=p["fp"], fecha_esperada=p["fd_esp"],
            fecha_devolucion=p["dev"],
        ))


# ---------------------------------------------------------------------------
# Búsquedas (DRY: un único lugar por entidad)
# ---------------------------------------------------------------------------

def _buscar_usuario(usuario_id: int) -> _Usuario:
    for u in _usuarios:
        if u.id == usuario_id:
            return u
    raise UsuarioNoEncontrado(f"No existe el usuario {usuario_id}")


def _buscar_libro(libro_id: int) -> _Libro:
    for l in _libros:
        if l.id == libro_id:
            return l
    raise LibroNoEncontrado(f"No existe el libro {libro_id}")


def _buscar_prestamo(prestamo_id: int) -> _Prestamo:
    for p in _prestamos:
        if p.id == prestamo_id:
            return p
    raise PrestamoNoEncontrado(f"No existe el préstamo {prestamo_id}")


# ---------------------------------------------------------------------------
# Operaciones de negocio
# ---------------------------------------------------------------------------

def _registrar_usuario(nombre: str, email: str, tipo_str: str) -> int:
    if not nombre or not email or "@" not in email:
        return -1
    if tipo_str not in _TIPO_STR:
        return -1
    nuevo_id = len(_usuarios) + 1
    _usuarios.append(_Usuario(
        id=nuevo_id, nombre=nombre, email=email, tipo=_TIPO_STR[tipo_str],
    ))
    print(f"Usuario registrado: {nombre}")
    _sync_legacy()
    return nuevo_id


def _registrar_libro(titulo: str, autor: str, ejemplares: int) -> int:
    if not titulo or not autor or ejemplares <= 0:
        return -1
    nuevo_id = len(_libros) + 1
    _libros.append(_Libro(
        id=nuevo_id, titulo=titulo, autor=autor,
        ejemplares=ejemplares, disponibles=ejemplares,
    ))
    print(f"Libro registrado: {titulo}")
    _sync_legacy()
    return nuevo_id


def _validar_usuario_para_prestamo(usuario: _Usuario) -> None:
    if not usuario.activo:
        raise UsuarioInactivo()
    if usuario.multas > 0:
        raise UsuarioConMultas()
    activos = sum(
        1 for p in _prestamos
        if p.usuario_id == usuario.id and p.fecha_devolucion is None
    )
    if activos >= LIMITE_PRESTAMOS[usuario.tipo]:
        raise LimitePrestamosAlcanzado()


def _registrar_prestamo(
    usuario_id: int, libro_id: int, fecha: datetime.datetime
) -> int:
    try:
        usuario = _buscar_usuario(usuario_id)
        _validar_usuario_para_prestamo(usuario)
        libro = _buscar_libro(libro_id)
        if libro.disponibles <= 0:
            raise SinEjemplaresDisponibles()
        fecha_esperada = fecha + datetime.timedelta(days=DIAS_PRESTAMO[usuario.tipo])
        nuevo_id = len(_prestamos) + 1
        _prestamos.append(_Prestamo(
            id=nuevo_id, usuario_id=usuario_id, libro_id=libro_id,
            fecha_prestamo=fecha, fecha_esperada=fecha_esperada,
        ))
        libro.disponibles -= 1
        print("Préstamo registrado")
        _sync_legacy()
        return nuevo_id
    except ErrorBiblioteca as exc:
        print(f"Error: {exc}")
        return -1


def _calcular_multa(prestamo: _Prestamo, fecha_devolucion: datetime.datetime) -> int:
    if fecha_devolucion <= prestamo.fecha_esperada:
        return 0
    dias = (fecha_devolucion - prestamo.fecha_esperada).days
    return min(dias * MULTA_POR_DIA, MULTA_MAXIMA)


def _devolver_libro(prestamo_id: int, fecha: datetime.datetime) -> int:
    try:
        prestamo = _buscar_prestamo(prestamo_id)
        if prestamo.fecha_devolucion is not None:
            raise PrestamoYaDevuelto()
        prestamo.fecha_devolucion = fecha
        _buscar_libro(prestamo.libro_id).disponibles += 1
        multa = _calcular_multa(prestamo, fecha)
        if multa > 0:
            _buscar_usuario(prestamo.usuario_id).multas += multa
            print(f"Devuelto con multa: ${multa}")
        else:
            print("Devuelto a tiempo")
        _sync_legacy()
        return 1
    except (PrestamoNoEncontrado, PrestamoYaDevuelto) as exc:
        print(f"Error: {exc}")
        return -1


def _reporte_usuario(usuario_id: int) -> int:
    try:
        usuario = _buscar_usuario(usuario_id)
    except UsuarioNoEncontrado:
        return -1
    prestamos_usuario = [p for p in _prestamos if p.usuario_id == usuario_id]
    if not prestamos_usuario:
        return -1
    print("=== Reporte ===")
    print(f"Nombre: {usuario.nombre}")
    print(f"Email:  {usuario.email}")
    print(f"Tipo:   {usuario.tipo.name.capitalize()}")
    print(f"Multas: ${usuario.multas}")
    for prestamo in prestamos_usuario:
        libro  = _buscar_libro(prestamo.libro_id)
        estado = "Activo" if prestamo.fecha_devolucion is None else "Devuelto"
        print(f"  - {libro.titulo} [{estado}]")
    return 1


# ---------------------------------------------------------------------------
# API legacy — fachada que mantiene compatibilidad con los tests
# ---------------------------------------------------------------------------

def proc(t, d, u_id=None, l_id=None, dt=None, dt2=None):  # noqa: C901
    """Fachada legacy: delega en las funciones limpias de negocio."""
    _load_from_legacy()

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