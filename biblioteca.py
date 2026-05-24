import datetime
from dataclasses import dataclass
from enum import Enum


# =========================================================
# Constantes
# =========================================================

MULTA_POR_DIA = 1000
MULTA_MAXIMA = 30000


class TipoUsuario(str, Enum):
    ESTUDIANTE = "E"
    PROFESOR = "P"
    ADMINISTRATIVO = "A"


LIMITE_PRESTAMOS = {
    TipoUsuario.ESTUDIANTE: 3,
    TipoUsuario.PROFESOR: 5,
    TipoUsuario.ADMINISTRATIVO: 2,
}

DIAS_PRESTAMO = {
    TipoUsuario.ESTUDIANTE: 7,
    TipoUsuario.PROFESOR: 14,
    TipoUsuario.ADMINISTRATIVO: 5,
}


# =========================================================
# Entidades
# =========================================================

@dataclass
class Usuario:
    id: int
    nombre: str
    email: str
    tipo: TipoUsuario
    mult: int = 0
    activo: bool = True

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class Libro:
    id: int
    tit: str
    aut: str
    ej: int
    disp: int

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class Prestamo:
    id: int
    u: int
    l: int
    fp: datetime.datetime
    fd_esp: datetime.datetime
    dev: datetime.datetime | None = None

    def __getitem__(self, key):
        return getattr(self, key)


# =========================================================
# Estado global
# =========================================================

usuarios_db = []
libros_db = []
prestamos_db = []


# =========================================================
# Helpers
# =========================================================

def _buscar(lista, item_id):
    for item in lista:
        if item.id == item_id:
            return item
    return None


def _usuario(uid):
    return _buscar(usuarios_db, uid)


def _libro(lid):
    return _buscar(libros_db, lid)


def _prestamo(pid):
    return _buscar(prestamos_db, pid)


def _prestamos_activos(uid):
    return sum(
        1 for p in prestamos_db
        if p.u == uid and p.dev is None
    )


def _multa(prestamo, fecha):
    if fecha <= prestamo.fd_esp:
        return 0

    dias = (fecha - prestamo.fd_esp).days

    return min(
        dias * MULTA_POR_DIA,
        MULTA_MAXIMA
    )


# =========================================================
# Operaciones
# =========================================================

def _registrar_usuario(nombre, email, tipo_str):

    if not nombre or "@" not in email:
        return -1

    try:
        tipo = TipoUsuario(tipo_str)
    except ValueError:
        return -1

    usuario = Usuario(
        len(usuarios_db) + 1,
        nombre,
        email,
        tipo
    )

    usuarios_db.append(usuario)

    print(f"Usuario registrado: {nombre}")

    return usuario.id


def _registrar_libro(titulo, autor, ejemplares):

    if not titulo or not autor or ejemplares <= 0:
        return -1

    libro = Libro(
        len(libros_db) + 1,
        titulo,
        autor,
        ejemplares,
        ejemplares
    )

    libros_db.append(libro)

    print(f"Libro registrado: {titulo}")

    return libro.id


def _registrar_prestamo(usuario_id, libro_id, fecha):

    usuario = _usuario(usuario_id)
    libro = _libro(libro_id)

    if usuario is None or libro is None:
        return -1

    if not usuario.activo:
        return -1

    if usuario.mult > 0:
        return -1

    if libro.disp <= 0:
        return -1

    if _prestamos_activos(usuario.id) >= LIMITE_PRESTAMOS[usuario.tipo]:
        return -1

    prestamo = Prestamo(
        len(prestamos_db) + 1,
        usuario.id,
        libro.id,
        fecha,
        fecha + datetime.timedelta(
            days=DIAS_PRESTAMO[usuario.tipo]
        )
    )

    prestamos_db.append(prestamo)

    libro.disp -= 1

    print("Préstamo registrado")

    return prestamo.id


def _devolver_libro(prestamo_id, fecha):

    prestamo = _prestamo(prestamo_id)

    if prestamo is None:
        return -1

    if prestamo.dev is not None:
        print("Error: ya fue devuelto")
        return -1

    prestamo.dev = fecha

    libro = _libro(prestamo.l)
    usuario = _usuario(prestamo.u)

    libro.disp += 1

    multa = _multa(prestamo, fecha)

    if multa > 0:
        usuario.mult += multa
        print(f"Devuelto con multa: ${multa}")
    else:
        print("Devuelto a tiempo")

    return 1


def _reporte_usuario(usuario_id):

    usuario = _usuario(usuario_id)

    if usuario is None:
        return -1

    prestamos = [
        p for p in prestamos_db
        if p.u == usuario.id
    ]

    if not prestamos:
        return -1

    print("=== Reporte ===")
    print(f"Nombre: {usuario.nombre}")
    print(f"Email:  {usuario.email}")
    print(f"Tipo:   {usuario.tipo.name.capitalize()}")
    print(f"Multas: ${usuario.mult}")

    for prestamo in prestamos:

        libro = _libro(prestamo.l)

        estado = (
            "Activo"
            if prestamo.dev is None
            else "Devuelto"
        )

        print(f"  - {libro.tit} [{estado}]")

    return 1


# =========================================================
# API legacy
# =========================================================

def proc(t, d, u_id=None, l_id=None, dt=None, dt2=None):

    if t == 1:
        return _registrar_usuario(
            d[0],
            d[1],
            d[2]
        )

    if t == 2:
        return _registrar_libro(
            d[0],
            d[1],
            d[2]
        )

    if t == 3:
        return _registrar_prestamo(
            u_id,
            l_id,
            dt
        )

    if t == 4:
        return _devolver_libro(
            d,
            dt2
        )

    if t == 5:
        return _reporte_usuario(
            u_id
        )

    return -1


# =========================================================
# Smoke test
# =========================================================

if __name__ == "__main__":

    hoy = datetime.datetime(2024, 5, 1)

    proc(1, ["Ana García", "ana@uni.edu", "E"])
    proc(1, ["Dr. López", "lopez@uni.edu", "P"])

    proc(2, ["Clean Code", "Robert Martin", 3])
    proc(2, ["Refactoring", "Martin Fowler", 2])

    proc(3, None, 1, 1, hoy)
    proc(3, None, 2, 2, hoy)

    proc(
        4,
        1,
        None,
        None,
        None,
        datetime.datetime(2024, 5, 15)
    )

    proc(5, None, 1)
    proc(5, None, 2)