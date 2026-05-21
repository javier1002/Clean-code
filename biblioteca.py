# Sistema de gestion de prestamos de biblioteca
# Version 0.3 - Funciona, no tocar - JP 2023
import datetime
usuarios_db = []
libros_db = []
prestamos_db = []
def proc(t, d, u_id=None, l_id=None, dt=None, dt2=None):
    # t: tipo operacion, d: datos, u_id: id usuario, l_id: id libro, dt: fecha, dt2: fecha2
    if t == 1:
        # Registrar usuario
        if d[0] != "" and d[1] != "" and "@" in d[1]:
            if d[2] == "E" or d[2] == "P" or d[2] == "A":
                # E=Estudiante, P=Profesor, A=Administrativo
                nid = len(usuarios_db) + 1
                usuarios_db.append({"id": nid, "n": d[0], "e": d[1], "tipo": d[2], "mult": 0,
"act": True})
                print("Usuario registrado: " + d[0])
                return nid
            else:
                return -1
        else:
            return -1
    elif t == 2:
        # Registrar libro
        if d[0] != "" and d[1] != "" and d[2] > 0:
            nid = len(libros_db) + 1
            libros_db.append({"id": nid, "tit": d[0], "aut": d[1], "ej": d[2], "disp": d[2]})
            print("Libro registrado: " + d[0])
            return nid
        else:
            return -1
    elif t == 3:
        # Hacer prestamo
        u = None
        for x in usuarios_db:
            if x["id"] == u_id:
                u = x
                break
            if u == None:
                print("Error: usuario no existe")
                return -1

            if u["act"] == False:
                print("Error: usuario inactivo")
                return -1
            if u["mult"] > 0:
                print("Error: usuario tiene multas")
                return -1
            c = 0
            for p in prestamos_db:
                if p["u"] == u_id and p["dev"] == None:
                    c = c + 1
            if u["tipo"] == "E" and c >= 3:
                print("Error: limite de prestamos alcanzado")
                return -1
            if u["tipo"] == "P" and c >= 5:
                print("Error: limite de prestamos alcanzado")
                return -1
            if u["tipo"] == "A" and c >= 2:
                print("Error: limite de prestamos alcanzado")
                return -1
            l = None
            for x in libros_db:
                if x["id"] == l_id:
                    l = x
                    break
            if l == None:
                print("Error: libro no existe")
                return -1
            if l["disp"] <= 0:
                print("Error: no hay ejemplares disponibles")
                return -1
            if u["tipo"] == "E":
                fd = dt + datetime.timedelta(days=7)
            elif u["tipo"] == "P":
                fd = dt + datetime.timedelta(days=14)
            else:
                fd = dt + datetime.timedelta(days=5)
            nid = len(prestamos_db) + 1
            prestamos_db.append({"id": nid, "u": u_id, "l": l_id, "fp": dt, "fd_esp": fd, "dev":
None})
            l["disp"] = l["disp"] - 1
            print("Prestamo registrado")
            return nid
    elif t == 4:
            # Devolver libro
            p = None
            for x in prestamos_db:
                if x["id"] == d:
                    p = x
                    break
            if p == None:
                return -1
            if p["dev"] != None:
                print("Error: ya fue devuelto")
                return -1
            p["dev"] = dt2
            for x in libros_db:

                if x["id"] == p["l"]:
                    x["disp"] = x["disp"] + 1
                    break
            if dt2 > p["fd_esp"]:
                dias = (dt2 - p["fd_esp"]).days
                m = dias * 1000
                if m > 30000:
                    m = 30000
                for x in usuarios_db:
                    if x["id"] == p["u"]:
                        x["mult"] = x["mult"] + m

                        break

                print("Devuelto con multa: " + str(m))
            else:
                print("Devuelto a tiempo")
            return 1
    elif t == 5:
        # Reporte de usuario
        u = None
        for x in usuarios_db:
            if x["id"] == u_id:
                u = x
                break
        if u == None:
            return -1
        print("=== Reporte ===")
        print("Nombre: " + u["n"])
        print("Email: " + u["e"])
        if u["tipo"] == "E":
            print("Tipo: Estudiante")
        elif u["tipo"] == "P":
            print("Tipo: Profesor")
        else:
            print("Tipo: Administrativo")
        print("Multas: $" + str(u["mult"]))
        for p in prestamos_db:
            if p["u"] == u_id:
                tit = ""
                for l in libros_db:
                    if l["id"] == p["l"]:
                        tit = l["tit"]
                        break

                est = "Activo" if p["dev"] == None else "Devuelto"
                print("- " + tit + " [" + est + "]")
                return 1
        else:
            return -1

    # Casos de prueba
if __name__ == "__main__":
        hoy = datetime.datetime(2024, 5, 1)
        proc(1, ["Ana Garcia", "ana@uni.edu", "E"])
        proc(1, ["Dr. Lopez", "lopez@uni.edu", "P"])
        proc(2, ["Clean Code", "Robert Martin", 3])
        proc(2, ["Refactoring", "Martin Fowler", 2])

        proc(3, None, 1, 1, hoy)
        proc(3, None, 2, 2, hoy)
        proc(4, 1, None, None, None, datetime.datetime(2024, 5, 15))
        proc(5, None, 1)
        proc(5, None, 2)