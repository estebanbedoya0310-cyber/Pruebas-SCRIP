from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

# Importa tu script original
try:
    import imagentrace
except:
    imagentrace = None

class TracerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.label = Label(text='SI.ESPEJO - ImageTrace\nListo para trabajar', halign='center')
        btn = Button(text='EJECUTAR ANALISIS', size_hint=(1, 0.3))
        btn.bind(on_press=self.ejecutar)
        self.layout.add_widget(self.label)
        self.layout.add_widget(btn)
        return self.layout

    def ejecutar(self, x):
        if imagentrace and hasattr(imagentrace, 'main'):
            try:
                res = imagentrace.main()
                self.label.text = str(res)[:500]
            except Exception as e:
                self.label.text = f"Error en imagentrace:\n{e}"
        else:
            self.label.text = "imagentrace.py cargado\n(Funcion main no encontrada)"

TracerApp().run()
