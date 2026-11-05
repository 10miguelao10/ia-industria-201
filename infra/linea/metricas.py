"""Métricas en formato Prometheus con la biblioteca estándar (sin paquetes nuevos en la imagen)."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Metricas:
    """Guarda contadores y valores, y los sirve en http://<contenedor>:<puerto>/metrics."""

    def __init__(self) -> None:
        self._valores: dict[str, float] = {}
        self._ayuda: dict[str, tuple[str, str]] = {}
        self._cerrojo = threading.Lock()

    def definir(self, nombre: str, tipo: str, ayuda: str) -> None:
        # tipo: "counter" (solo sube) o "gauge" (sube y baja)
        self._ayuda[nombre] = (tipo, ayuda)
        self._valores.setdefault(nombre, 0.0)

    def sumar(self, nombre: str, cantidad: float = 1.0) -> None:
        with self._cerrojo:
            self._valores[nombre] += cantidad

    def poner(self, nombre: str, valor: float) -> None:
        with self._cerrojo:
            self._valores[nombre] = float(valor)

    def texto(self) -> str:
        lineas = []
        with self._cerrojo:
            for nombre, valor in self._valores.items():
                tipo, ayuda = self._ayuda[nombre]
                lineas += [f"# HELP {nombre} {ayuda}", f"# TYPE {nombre} {tipo}", f"{nombre} {valor}"]
        return "\n".join(lineas) + "\n"

    def servir(self, puerto: int) -> None:
        metricas = self

        class Manejador(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/metrics":
                    self.send_error(404)
                    return
                cuerpo = metricas.texto().encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.end_headers()
                self.wfile.write(cuerpo)

            def log_message(self, *_):  # sin una línea de log por cada consulta de Prometheus
                pass

        servidor = ThreadingHTTPServer(("0.0.0.0", puerto), Manejador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
