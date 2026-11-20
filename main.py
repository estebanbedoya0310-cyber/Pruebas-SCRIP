import hashlib
import json
import os
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform

from PIL import Image

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

UMBRAL_TOLERANCIA = 15

CARPETAS = [
    ("Descargas", "/sdcard/Download"),
    ("Camara", "/sdcard/DCIM/Camera"),
    ("WhatsApp", "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images"),
    ("Pictures", "/sdcard/Pictures"),
]


# ---------------- Logica de hashes ----------------
def calcular_sha256(ruta):
    sha = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloc in iter(lambda: f.read(4096), b""):
            sha.update(bloc)
    return sha.hexdigest()


def calcular_dhash(ruta, hash_size=8):
    with Image.open(ruta) as img:
        gris = img.convert("L").resize((hash_size + 1, hash_size), RESAMPLE)
        pixels = list(gris.getdata())
    valor = 0
    bit = 0
    for row in range(hash_size):
        inicio = row * (hash_size + 1)
        for col in range(hash_size):
            if pixels[inicio + col] > pixels[inicio + col + 1]:
                valor |= 1 << bit
            bit += 1
    return f"{valor:016x}"


def distancia_hamming(h1, h2):
    return bin(int(h1, 16) ^ int(h2, 16)).count("1")


# ---------------- Interfaz ----------------
class ImagenTracerApp(App):
    title = "Imagen Tracer | SI.ESPEJO"

    def build(self):
        Window.clearcolor = (0.08, 0.09, 0.11, 1)
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        root.add_widget(
            Label(
                text="IMAGEN TRACER | SI.ESPEJO",
                size_hint_y=None,
                height=dp(40),
                bold=True,
                font_size="18sp",
            )
        )

        for texto, fn in [
            ("1. Proteger imagen antes de enviar", self.accion_proteger),
            ("2. Auditar imagen (detectar anomalias)", self.accion_auditar),
            ("3. Ver bitacora de custodia", self.accion_bitacora),
        ]:
            b = Button(text=texto, size_hint_y=None, height=dp(52))
            b.bind(on_release=lambda _, f=fn: f())
            root.add_widget(b)

        scroll = ScrollView()
        self.salida = Label(
            text="Listo.",
            size_hint_y=None,
            halign="left",
            valign="top",
            markup=False,
        )
        self.salida.bind(
            width=lambda i, w: setattr(i, "text_size", (w, None)),
            texture_size=lambda i, s: setattr(i, "height", s[1]),
        )
        scroll.add_widget(self.salida)
        root.add_widget(scroll)
        return root

    def on_start(self):
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions

                perms = [
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ]
                for nombre in ("READ_MEDIA_IMAGES",):
                    if hasattr(Permission, nombre):
                        perms.append(getattr(Permission, nombre))
                    else:
                        perms.append("android.permission." + nombre)
                request_permissions(perms)
            except Exception as e:
                self.mostrar(f"[-] No se pudieron pedir permisos: {e}")

    # ---------- utilidades ----------
    def mostrar(self, texto):
        self.salida.text = texto

    def ruta_log(self):
        return os.path.join(self.user_data_dir, "imagentrace_log.json")

    def cargar_registros(self):
        ruta = self.ruta_log()
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception:
                return []
        return []

    def guardar_registro(self, reg):
        registros = self.cargar_registros()
        registros.append(reg)
        with open(self.ruta_log(), "w", encoding="utf-8") as f:
            json.dump(registros, f, indent=4, ensure_ascii=False)

    # ---------- selector de imagen ----------
    def seleccionar_imagen(self, callback):
        inicio = next((r for _, r in CARPETAS if os.path.exists(r)), self.user_data_dir)
        filtros = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
        chooser = FileChooserListView(path=inicio, filters=filtros)

        contenido = BoxLayout(orientation="vertical", spacing=dp(6))
        fila = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
        for nombre, ruta in CARPETAS:
            b = Button(text=nombre, font_size="12sp")
            b.bind(
                on_release=lambda _, r=ruta: setattr(chooser, "path", r)
                if os.path.exists(r)
                else None
            )
            fila.add_widget(b)
        contenido.add_widget(fila)
        contenido.add_widget(chooser)

        botones = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        b_cancel = Button(text="Cancelar")
        b_ok = Button(text="Elegir")
        botones.add_widget(b_cancel)
        botones.add_widget(b_ok)
        contenido.add_widget(botones)

        popup = Popup(title="Selecciona una imagen", content=contenido, size_hint=(0.95, 0.9))

        def elegir(_):
            if chooser.selection:
                ruta = chooser.selection[0]
                popup.dismiss()
                callback(ruta)

        b_ok.bind(on_release=elegir)
        b_cancel.bind(on_release=lambda _: popup.dismiss())
        popup.open()

    # ---------- 1. Proteger ----------
    def accion_proteger(self):
        self.seleccionar_imagen(self.pedir_datos_proteccion)

    def pedir_datos_proteccion(self, ruta):
        contenido = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        t_dest = TextInput(hint_text="Destinatario autorizado", multiline=False, size_hint_y=None, height=dp(44))
        t_ubic = TextInput(hint_text="Coordenadas o direccion de envio", multiline=False, size_hint_y=None, height=dp(44))
        contenido.add_widget(Label(text=os.path.basename(ruta), size_hint_y=None, height=dp(30)))
        contenido.add_widget(t_dest)
        contenido.add_widget(t_ubic)
        botones = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        b_cancel = Button(text="Cancelar")
        b_ok = Button(text="Registrar")
        botones.add_widget(b_cancel)
        botones.add_widget(b_ok)
        contenido.add_widget(botones)

        popup = Popup(title="Datos de custodia", content=contenido, size_hint=(0.92, 0.55))

        def registrar(_):
            dest = t_dest.text.strip()
            if not dest:
                t_dest.hint_text = "El destinatario es obligatorio"
                return
            ubic = t_ubic.text.strip() or "No especificada"
            popup.dismiss()
            try:
                sha = calcular_sha256(ruta)
                dh = calcular_dhash(ruta)
                self.guardar_registro(
                    {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "archivo_original": os.path.basename(ruta),
                        "destinatario": dest,
                        "ubicacion_envio": ubic,
                        "sha256": sha,
                        "dhash": dh,
                    }
                )
                self.mostrar(
                    "IMAGEN REGISTRADA Y CUSTODIADA\n\n"
                    f"Destinatario: {dest}\nUbicacion: {ubic}\n"
                    f"dHash: {dh}\nBitacora: {self.ruta_log()}"
                )
            except Exception as e:
                self.mostrar(f"[-] Error protegiendo imagen: {e}")

        b_ok.bind(on_release=registrar)
        b_cancel.bind(on_release=lambda _: popup.dismiss())
        popup.open()

    # ---------- 2. Auditar ----------
    def accion_auditar(self):
        if not self.cargar_registros():
            self.mostrar("[-] La bitacora esta vacia. Registra imagenes primero en la opcion 1.")
            return
        self.seleccionar_imagen(self.auditar)

    def auditar(self, ruta):
        try:
            sha_actual = calcular_sha256(ruta)
            dh_actual = calcular_dhash(ruta)
            mejor, menor = None, 999
            for reg in self.cargar_registros():
                h = reg.get("dhash")
                if not h:
                    continue
                d = distancia_hamming(dh_actual, h)
                if d < menor:
                    menor, mejor = d, reg

            if mejor is not None and menor <= UMBRAL_TOLERANCIA:
                sim = max(0, int(100 - (menor / 64.0) * 100))
                texto = (
                    "ANOMALIA DETECTADA: REENVIO NO AUTORIZADO\n"
                    "----------------------------------------\n"
                    f"Destinatario original: {mejor['destinatario']}\n"
                    f"Ubicacion de envio: {mejor.get('ubicacion_envio', 'No registrada')}\n"
                    f"Fecha de registro: {mejor['fecha']}\n"
                    f"Archivo original: {mejor['archivo_original']}\n"
                    f"Similitud visual: {sim}% (distancia dHash: {menor})\n"
                )
                texto += "\n" + self.exportar_reporte(mejor, ruta, sha_actual, menor, sim)
            else:
                texto = (
                    "SIN ANOMALIAS DETECTADAS\n"
                    "----------------------------------------\n"
                    f"Menor distancia hallada: {menor} bits (umbral max: {UMBRAL_TOLERANCIA})\n"
                    "No se encontraron coincidencias con copias registradas."
                )
            self.mostrar(texto)
        except Exception as e:
            self.mostrar(f"[-] Error en la auditoria: {e}")

    def exportar_reporte(self, reg, ruta_dub, sha_dub, distancia, similitud):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"Informe_Forense_Anomalia_{ts}.txt"
        contenido = f"""==================================================
        INFORME TECNICO DE AUDITORIA FORENSE
               IMAGEN TRACER | SI.ESPEJO
==================================================
Fecha y hora de auditoria: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Estado del dictamen: ANOMALIA DETECTADA (REENVIO NO AUTORIZADO)

1. EVIDENCIA ORIGINAL (CUSTODIADA)
- Destinatario autorizado: {reg['destinatario']}
- Ubicacion de envio: {reg.get('ubicacion_envio', 'No registrada')}
- Fecha de registro: {reg['fecha']}
- Archivo original: {reg['archivo_original']}
- SHA-256 original: {reg['sha256']}

2. IMAGEN DUBITADA (INTERCEPTADA)
- Ruta analizada: {ruta_dub}
- SHA-256 actual: {sha_dub}

3. METRICAS DE CORRELACION PERCEPTUAL
- Algoritmo: dHash
- Distancia de Hamming: {distancia} bits
- Similitud visual: {similitud}%

4. CONCLUSION TECNICA
La imagen analizada guarda correspondencia estructural directa
con la copia digital entregada al destinatario indicado,
superando los umbrales de tolerancia ante compresion de redes sociales.
==================================================
"""
        for carpeta in ("/sdcard/Download", self.user_data_dir):
            try:
                if not os.path.isdir(carpeta):
                    continue
                destino = os.path.join(carpeta, nombre)
                with open(destino, "w", encoding="utf-8") as f:
                    f.write(contenido)
                return f"Informe exportado en:\n{destino}"
            except Exception:
                continue
        return "[-] No se pudo exportar el informe."

    # ---------- 3. Bitacora ----------
    def accion_bitacora(self):
        registros = self.cargar_registros()
        if not registros:
            self.mostrar("No hay registros guardados todavia.")
            return
        partes = [f"BITACORA ({len(registros)} registros)\n{self.ruta_log()}\n"]
        for i, r in enumerate(registros, 1):
            partes.append(
                f"{i}. Destinatario: {r['destinatario']}\n"
                f"   Ubicacion: {r.get('ubicacion_envio', 'N/A')}\n"
                f"   Fecha: {r['fecha']}\n"
                f"   Archivo: {r['archivo_original']}\n"
            )
        self.mostrar("\n".join(partes))


if __name__ == "__main__":
    ImagenTracerApp().run()
