import datetime
from dataclasses import dataclass, field
from enum import Enum

# =========================================================
# Constantes
# =========================================================

MULTA_POR_DIA    = 1_000
MULTA_MAXIMA     = 30_000
DIAS_RENOVACION  = 7      # HU-01: días que extiende una renovación

class TipoUsuario(str, Enum):
    ESTUDIANTE     = "E"
    PROFESOR       = "P"
    ADMINISTRATIVO = "A"

LIMITE_PRESTAMOS = {
    TipoUsuario.ESTUDIANTE: 3, TipoUsuario.PROFESOR: 5, TipoUsuario.ADMINISTRATIVO: 2,
}
DIAS_PRESTAMO = {
    TipoUsuario.ESTUDIANTE: 7, TipoUsuario.PROFESOR: 14, TipoUsuario.ADMINISTRATIVO: 5,
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
    def __getitem__(self, key): return getattr(self, key)


@dataclass
class Libro:
    id: int
    tit: str
    aut: str
    ej: int
    disp: int
    def __getitem__(self, key): return getattr(self, key)


@dataclass
class Prestamo:
    id: int
    u: int
    l: int
    fp: datetime.datetime
    fd_esp: datetime.datetime
    dev: datetime.datetime | None = None
    renovado: bool = False          # HU-01: máximo una renovación por préstamo
    def __getitem__(self, key): return getattr(self, key)


# =========================================================
# Estado global
# =========================================================

usuarios_db:  list[Usuario]  = []
libros_db:    list[Libro]    = []
prestamos_db: list[Prestamo] = []

# =========================================================
# Helpers
# =========================================================

def _buscar(lista, item_id):
    for item in lista:
        if item.id == item_id:
            return item
    return None

def _usuario(uid):  return _buscar(usuarios_db, uid)
def _libro(lid):    return _buscar(libros_db, lid)
def _prestamo(pid): return _buscar(prestamos_db, pid)

def _prestamos_activos(uid):
    return sum(1 for p in prestamos_db if p.u == uid and p.dev is None)

def _multa(prestamo, fecha):
    if fecha <= prestamo.fd_esp:
        return 0
    return min((fecha - prestamo.fd_esp).days * MULTA_POR_DIA, MULTA_MAXIMA)

# =========================================================
# Operaciones — Sprint 1 (sin cambios)
# =========================================================

def _registrar_usuario(nombre, email, tipo_str):
    if not nombre or "@" not in email:
        return -1
    try:
        tipo = TipoUsuario(tipo_str)
    except ValueError:
        return -1
    usuario = Usuario(len(usuarios_db) + 1, nombre, email, tipo)
    usuarios_db.append(usuario)
    print(f"Usuario registrado: {nombre}")
    return usuario.id


def _registrar_libro(titulo, autor, ejemplares):
    if not titulo or not autor or ejemplares <= 0:
        return -1
    libro = Libro(len(libros_db) + 1, titulo, autor, ejemplares, ejemplares)
    libros_db.append(libro)
    print(f"Libro registrado: {titulo}")
    return libro.id


def _registrar_prestamo(usuario_id, libro_id, fecha):
    usuario = _usuario(usuario_id)
    libro   = _libro(libro_id)
    if usuario is None or libro is None:
        return -1
    if not usuario.activo or usuario.mult > 0:
        return -1
    if libro.disp <= 0:
        return -1
    if _prestamos_activos(usuario.id) >= LIMITE_PRESTAMOS[usuario.tipo]:
        return -1
    prestamo = Prestamo(
        len(prestamos_db) + 1, usuario.id, libro.id, fecha,
        fecha + datetime.timedelta(days=DIAS_PRESTAMO[usuario.tipo]),
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
    _libro(prestamo.l).disp += 1
    multa = _multa(prestamo, fecha)
    if multa > 0:
        _usuario(prestamo.u).mult += multa
        print(f"Devuelto con multa: ${multa}")
    else:
        print("Devuelto a tiempo")
    return 1


def _reporte_usuario(usuario_id):
    usuario = _usuario(usuario_id)
    if usuario is None:
        return -1
    prestamos = [p for p in prestamos_db if p.u == usuario.id]
    if not prestamos:
        return -1
    print("=== Reporte ===")
    print(f"Nombre: {usuario.nombre}")
    print(f"Email:  {usuario.email}")
    print(f"Tipo:   {usuario.tipo.name.capitalize()}")
    print(f"Multas: ${usuario.mult}")
    for p in prestamos:
        estado = "Activo" if p.dev is None else "Devuelto"
        ren    = " [renovado]" if p.renovado else ""
        print(f"  - {_libro(p.l).tit} [{estado}]{ren}")
    return 1


# =========================================================
# HU-01: Renovación de préstamo
# =========================================================

def _renovar_prestamo(prestamo_id):
    """Extiende la fecha de devolución de un préstamo activo en DIAS_RENOVACION días.

    Restricciones:
      - El préstamo debe existir y estar activo (no devuelto).
      - Solo se permite una renovación por préstamo.
      - No debe haber reservas pendientes del libro.
        (En este Sprint no existe el concepto de reserva; la condición
        siempre se cumple y queda documentada para cuando se implemente.)
    """
    prestamo = _prestamo(prestamo_id)

    if prestamo is None:
        print("Error: préstamo no existe")
        return -1

    if prestamo.dev is not None:
        print("Error: el préstamo ya fue devuelto")
        return -1

    if prestamo.renovado:
        print("Error: el préstamo ya fue renovado una vez")
        return -1

    # Condición de reservas: sin reservas implementadas siempre es True.
    # Cuando se implemente HU-Reservas, agregar aquí:
    # if _hay_reservas_pendientes(prestamo.l):
    #     print("Error: hay reservas pendientes para este libro")
    #     return -1

    prestamo.fd_esp   += datetime.timedelta(days=DIAS_RENOVACION)
    prestamo.renovado  = True
    print(f"Préstamo renovado. Nueva fecha límite: {prestamo.fd_esp.date()}")
    return 1


# =========================================================
# HU-02: Reporte de libros más prestados por rango de fechas
# =========================================================

def _reporte_libros_mas_prestados(fecha_inicio, fecha_fin, top=10):
    """Imprime un ranking de los libros más solicitados en el rango dado.

    Cuenta cada préstamo cuya fecha de inicio (fp) esté dentro del rango,
    independientemente de si fue devuelto o sigue activo.
    """
    prestamos_en_rango = [
        p for p in prestamos_db
        if fecha_inicio <= p.fp <= fecha_fin
    ]

    if not prestamos_en_rango:
        print("Sin préstamos en el rango indicado.")
        return 0

    conteo: dict[int, int] = {}
    for p in prestamos_en_rango:
        conteo[p.l] = conteo.get(p.l, 0) + 1

    ranking = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    print(f"=== Libros más prestados: {fecha_inicio.date()} → {fecha_fin.date()} ===")
    for posicion, (libro_id, total) in enumerate(ranking[:top], start=1):
        libro = _libro(libro_id)
        nombre = libro.tit if libro else f"(libro {libro_id})"
        print(f"  {posicion:>2}. {nombre} — {total} préstamo(s)")

    return len(ranking)


# =========================================================
# API legacy
# =========================================================

def proc(t, d, u_id=None, l_id=None, dt=None, dt2=None):
    if t == 1: return _registrar_usuario(d[0], d[1], d[2])
    if t == 2: return _registrar_libro(d[0], d[1], d[2])
    if t == 3: return _registrar_prestamo(u_id, l_id, dt)
    if t == 4: return _devolver_libro(d, dt2)
    if t == 5: return _reporte_usuario(u_id)
    if t == 6: return _renovar_prestamo(d)                       # HU-01
    if t == 7: return _reporte_libros_mas_prestados(dt, dt2, d)  # HU-02
    return -1


# =========================================================
# Smoke test (cubre las dos HU nuevas)
# =========================================================

if __name__ == "__main__":
    hoy = datetime.datetime(2024, 5, 1)

    proc(1, ["Ana García",  "ana@uni.edu",   "E"])
    proc(1, ["Dr. López",   "lopez@uni.edu", "P"])
    proc(2, ["Clean Code",  "Robert Martin", 3])
    proc(2, ["Refactoring", "Martin Fowler", 2])

    proc(3, None, 1, 1, hoy)
    proc(3, None, 2, 2, hoy)
    proc(3, None, 1, 1, hoy)   # segundo préstamo de Ana (mismo libro, otra copia)

    print("\n--- HU-01: Renovaciones ---")
    proc(6, 1)   # renueva préstamo 1 → OK
    proc(6, 1)   # intento de segunda renovación → Error
    proc(6, 99)  # préstamo inexistente → Error

    print("\n--- HU-02: Reporte de libros más prestados ---")
    inicio = datetime.datetime(2024, 4, 1)
    fin    = datetime.datetime(2024, 5, 31)
    proc(7, 10, None, None, inicio, fin)  # top 10 en rango

    print("\n--- Reporte de usuario con renovación visible ---")
    proc(5, None, 1)