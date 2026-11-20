import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import platform

import imagentrace as core

Window.clearcolor = (0.08, 0.10, 0.13, 1)

if platform == "android":
    try:
        from android.permissions import Permission, request_permissions
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ])
    except Exception:
        pass


class ImagenTracerAPK(App):
    def build(self):
        self.title = "Imagen Tracer | SI.ESPEJO"
        self.ruta_img = ""

        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        header = Label(
            text="[b]IMAGEN TRACER | SI.ESPEJO[/b]\n[size=13sp][color=88aaff]Custodia y Auditoría Forense[/color][/size]",
            markup=True,
            size_hint=(1, 0.13),
        )
        root.add_widget(header)

        tabs = BoxLayout(size_hint=(1, 0.10), spacing=6)
        b1 = Button(text="Proteger", background_color=(0.15, 0.45, 0.85, 1), bold=True)
        b2 = Button(text="Auditar", background_color=(0.80, 0.25, 0.25, 1), bold=True)
        b3 = Button(text="Bitácora", background_color=(0.25, 0.55, 0.35, 1), bold=True)

        b1.bind(on_release=lambda x: self.vista_proteger())
        b2.bind(on_release=lambda x: self.vista_auditar())
        b3.bind(on_release=lambda x: self.vista_bitacora())

        tabs.add_widget(b1)
        tabs.add_widget(b2)
        tabs.add_widget(b3)
        root.add_widget(tabs)

        self.panel = BoxLayout(orientation="vertical", size_hint=(1, 0.77), spacing=8)
        root.add_widget(self.panel)

        self.vista_proteger()
        return root

    def elegir_imagen(self, on_done):
        box = BoxLayout(orientation="vertical", spacing=8, padding=8)
        inicio = "/sdcard/Download" if os.path.exists("/sdcard/Download") else os.path.expanduser("~")
        fc = FileChooserListView(
            path=inicio,
            filters=["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"],
        )
        box.add_widget(fc)

        btns = BoxLayout(size_hint=(1, 0.13), spacing=8)
        btn_cancel = Button(text="Cancelar")
        btn_ok = Button(text="Seleccionar", background_color=(0.15, 0.65, 0.35, 1), bold=True)
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_ok)
        box.add_widget(btns)

        pop = Popup(title="Seleccionar Imagen", content=box, size_hint=(0.95, 0.90))
        btn_cancel.bind(on_release=pop.dismiss)

        def confirmar(inst):
            if fc.selection:
                on_done(fc.selection[0])
                pop.dismiss()

        btn_ok.bind(on_release=confirmar)
        pop.open()

    def vista_proteger(self):
        self.panel.clear_widgets()
        self.ruta_img = ""

        self.lbl_sel_p = Label(text="Sin imagen seleccionada", size_hint=(1, 0.09))
        btn_sel = Button(text="Elegir Imagen", size_hint=(1, 0.12))
        btn_sel.bind(on_release=lambda x: self.elegir_imagen(self._set_p))

        self.txt_dest = TextInput(hint_text="Destinatario autorizado", multiline=False, size_hint=(1, 0.11))
        self.txt_ubic = TextInput(hint_text="Ubicación o coordenadas", multiline=False, size_hint=(1, 0.11))

        btn_save = Button(
            text="CUSTODIAR IMAGEN",
            size_hint=(1, 0.13),
            background_color=(0.15, 0.65, 0.35, 1),
            bold=True,
        )
        btn_save.bind(on_release=self._guardar_custodia)

        self.lbl_res_p = Label(text="", markup=True, size_hint=(1, 0.44), valign="top")
        self.lbl_res_p.bind(size=self.lbl_res_p.setter("text_size"))

        for w in [self.lbl_sel_p, btn_sel, self.txt_dest, self.txt_ubic, btn_save, self.lbl_res_p]:
            self.panel.add_widget(w)

    def _set_p(self, ruta):
        self.ruta_img = ruta
        self.lbl_sel_p.text = f"Archivo: {os.path.basename(ruta)}"

    def _guardar_custodia(self, inst):
        if not self.ruta_img or not os.path.exists(self.ruta_img):
            self.lbl_res_p.text = "[color=ff5555]Selecciona una imagen válida.[/color]"
            return
        dest = self.txt_dest.text.strip()
        if not dest:
            self.lbl_res_p.text = "[color=ff5555]Ingresa el destinatario.[/color]"
            return
        ubic = self.txt_ubic.text.strip() or "No especificada"

        try:
            sha_val = core.calcular_sha256(self.ruta_img)
            dhash_val = core.calcular_dhash(self.ruta_img)
            core.guardar_registro({
                "fecha": core.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo_original": os.path.basename(self.ruta_img),
                "destinatario": dest,
                "ubicacion_envio": ubic,
                "sha256": sha_val,
                "dhash": dhash_val,
            })
            self.lbl_res_p.text = (
                f"[color=55ff77]Custodiada con éxito[/color]\n"
                f"Destinatario: {dest}\n"
                f"dHash: {dhash_val}\n"
                f"Log: {core.obtener_ruta_log()}"
            )
            self.txt_dest.text = ""
            self.txt_ubic.text = ""
        except Exception as e:
            self.lbl_res_p.text = f"[color=ff5555]Error: {e}[/color]"

    def vista_auditar(self):
        self.panel.clear_widgets()
        self.ruta_img = ""

        self.lbl_sel_a = Label(text="Sin imagen dubitada seleccionada", size_hint=(1, 0.09))
        btn_sel = Button(text="Elegir Imagen a Auditar", size_hint=(1, 0.12))
        btn_sel.bind(on_release=lambda x: self.elegir_imagen(self._set_a))

        btn_run = Button(
            text="AUDITAR IMAGEN",
            size_hint=(1, 0.13),
            background_color=(0.85, 0.30, 0.20, 1),
            bold=True,
        )
        btn_run.bind(on_release=self._correr_auditoria)

        scroll = ScrollView(size_hint=(1, 0.66))
        self.lbl_res_a = Label(text="Listo para auditar.", markup=True, size_hint_y=None, valign="top")
        self.lbl_res_a.bind(texture_size=self.lbl_res_a.setter("size"))
        self.lbl_res_a.bind(size=self.lbl_res_a.setter("text_size"))
        scroll.add_widget(self.lbl_res_a)

        for w in [self.lbl_sel_a, btn_sel, btn_run, scroll]:
            self.panel.add_widget(w)

    def _set_a(self, ruta):
        self.ruta_img = ruta
        self.lbl_sel_a.text = f"Dubitada: {os.path.basename(ruta)}"

    def _correr_auditoria(self, inst):
        if not self.ruta_img or not os.path.exists(self.ruta_img):
            self.lbl_res_a.text = "[color=ff5555]Selecciona una imagen.[/color]"
            return
        regs = core.cargar_registros()
        if not regs:
            self.lbl_res_a.text = "[color=ffaa33]Bitácora vacía.[/color]"
            return

        try:
            sha_act = core.calcular_sha256(self.ruta_img)
            dhash_act = core.calcular_dhash(self.ruta_img)
            mejor = None
            menor_dist = 999

            for r in regs:
                h = r.get("dhash") or r.get("phash")
                if not h:
                    continue
                d = core.distancia_hamming(dhash_act, h)
                if d < menor_dist:
                    menor_dist = d
                    mejor = r

            umbral = 15
            if mejor is not None and menor_dist <= umbral:
                sim = max(0, int(100 - (menor_dist / 64.0) * 100))
                core.exportar_reporte_txt(mejor, self.ruta_img, sha_act, menor_dist, sim)
                self.lbl_res_a.text = (
                    f"[color=ff4444][b]COINCIDENCIA DETECTADA[/b][/color]\n"
                    f"Destinatario: {mejor['destinatario']}\n"
                    f"Ubicación: {mejor.get('ubicacion_envio', 'N/A')}\n"
                    f"Fecha: {mejor['fecha']}\n"
                    f"Similitud: {sim}% (Distancia: {menor_dist})"
                )
            else:
                self.lbl_res_a.text = (
                    f"[color=55ff77][b]SIN COINCIDENCIAS[/b][/color]\n"
                    f"Menor distancia: {menor_dist} bits (Umbral: {umbral})"
                )
        except Exception as e:
            self.lbl_res_a.text = f"[color=ff5555]Error: {e}[/color]"

    def vista_bitacora(self):
        self.panel.clear_widgets()
        regs = core.cargar_registros()
        lbl_t = Label(text=f"BITÁCORA ({len(regs)} registros)", size_hint=(1, 0.10))
        scroll = ScrollView(size_hint=(1, 0.90))

        txt = "\n".join(
            f"{i}. {r.get('destinatario')} | {r.get('archivo_original')} | {r.get('fecha')}"
            for i, r in enumerate(reversed(regs), 1)
        ) or "Sin registros."

        lbl_l = Label(text=txt, size_hint_y=None, valign="top")
        lbl_l.bind(texture_size=lbl_l.setter("size"))
        lbl_l.bind(size=lbl_l.setter("text_size"))
        scroll.add_widget(lbl_l)

        self.panel.add_widget(lbl_t)
        self.panel.add_widget(scroll)


if __name__ == "__main__":
    ImagenTracerAPK().run()
