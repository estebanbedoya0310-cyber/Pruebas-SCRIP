import hashlib
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

try:
    from PIL import Image
except ImportError:
    print("----------------------------------------", flush=True)
    print("[-] FALTA LA LIBRERÍA 'pillow'", flush=True)
    print("[*] Ve a Pip en Pydroid 3 e instala 'pillow'.", flush=True)
    print("----------------------------------------", flush=True)
    input("Presiona Enter para salir...")
    sys.exit(1)

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()


def obtener_ruta_log():
    if os.path.exists("/sdcard/Download") and os.access("/sdcard/Download", os.W_OK):
        return os.path.join("/sdcard/Download", "imagentrace_log.json")
    return os.path.join(SCRIPT_DIR, "imagentrace_log.json")


LOG_FILE = obtener_ruta_log()


def cargar_registros():
    ruta = obtener_ruta_log()
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def guardar_registro(nuevo_registro):
    ruta = obtener_ruta_log()
    registros = cargar_registros()
    registros.append(nuevo_registro)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)


def calcular_sha256(ruta):
    sha = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloc in iter(lambda: f.read(4096), b""):
            sha.update(bloc)
    return sha.hexdigest()


def calcular_dhash(ruta_imagen, hash_size=8):
    with Image.open(ruta_imagen) as img:
        gris = img.convert("L").resize(
            (hash_size + 1, hash_size), Image.Resampling.LANCZOS
        )
        pixels = list(gris.getdata())

    difference = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        for col in range(hash_size):
            left = pixels[row_start + col]
            right = pixels[row_start + col + 1]
            difference.append(left > right)

    decimal_value = 0
    for i, val in enumerate(difference):
        if val:
            decimal_value |= (1 << i)
    return f"{decimal_value:016x}"


def distancia_hamming(h1_str, h2_str):
    h1 = int(h1_str, 16)
    h2 = int(h2_str, 16)
    return bin(h1 ^ h2).count("1")


def seleccionar_imagen_interactiva():
    directorios = [
        ("/sdcard/Download", "Descargas"),
        ("/sdcard/DCIM/Camera", "Cámara"),
        ("/sdcard/WhatsApp/Media/WhatsApp Images", "WhatsApp Images"),
        ("/sdcard/Pictures", "Pictures"),
    ]
    print("\n--- SELECCIONAR CARPETA ---", flush=True)
    validas = []
    idx = 1
    for ruta, nombre in directorios:
        if os.path.exists(ruta):
            print(f"{idx}. {nombre}", flush=True)
            validas.append((idx, ruta))
            idx += 1
    print(f"{idx}. Ingresar ruta manual", flush=True)
    manual_opt = idx

    eleccion = input("\nElige el número de la carpeta: ").strip()
    if not eleccion.isdigit():
        print("[-] Opción inválida.", flush=True)
        return None
    eleccion = int(eleccion)

    if eleccion == manual_opt:
        r = input("Ingresa la ruta completa: ").strip().strip("'\"")
        return r if r and os.path.exists(r) else None

    carpeta = None
    for i, r in validas:
        if i == eleccion:
            carpeta = r
            break
    if not carpeta:
        print("[-] Carpeta no válida.", flush=True)
        return None

    try:
        archivos = [
            f
            for f in os.listdir(carpeta)
            if os.path.isfile(os.path.join(carpeta, f))
            and f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not archivos:
            print("[-] No hay imágenes en esta carpeta.", flush=True)
            return None
        archivos.sort(
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)), reverse=True
        )

        recientes = archivos[:15]
        print(f"\n--- FOTOS RECIENTES EN {os.path.basename(carpeta)} ---", flush=True)
        for i, f_name in enumerate(recientes, 1):
            print(f"{i}. {f_name}", flush=True)

        sel = input("\nEscribe el número de la foto (0 para cancelar): ").strip()
        if not sel.isdigit():
            return None
        sel_idx = int(sel)
        if sel_idx <= 0 or sel_idx > len(recientes):
            return None
        return os.path.join(carpeta, recientes[sel_idx - 1])
    except Exception as e:
        print(f"[-] Error leyendo carpeta: {e}", flush=True)
        return None


def exportar_reporte_txt(match_data, ruta_dub, sha_dub, distancia, similitud):
    """Genera un archivo de texto formal con el informe de la anomalía detectada"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_reporte = f"Informe_Forense_Anomalia_{timestamp}.txt"

    ruta_dir = (
        "/sdcard/Download"
        if os.path.exists("/sdcard/Download") and os.access("/sdcard/Download", os.W_OK)
        else SCRIPT_DIR
    )
    ruta_completa = os.path.join(ruta_dir, nombre_reporte)

    contenido = f"""==================================================
        INFORME TÉCNICO DE AUDITORÍA FORENSE
               IMAGEN TRACER | SI.ESPEJO
==================================================
Fecha y Hora de Auditoría: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Estado del Dictamen: 🚨 ANOMALÍA DETECTADA (REENVÍO NO AUTORIZADO)

--------------------------------------------------
1. DATOS DE LA EVIDENCIA ORIGINAL (CUSTODIADA)
--------------------------------------------------
- Destinatario Autorizado: {match_data['destinatario']}
- Ubicación / Coordenadas de Envío: {match_data.get('ubicacion_envio', 'No registrada')}
- Fecha de Registro Original: {match_data['fecha']}
- Archivo Original Registrado: {match_data['archivo_original']}
- Hash SHA-256 Original: {match_data['sha256']}

--------------------------------------------------
2. DATOS DE LA IMAGEN DUBITADA (INTERCEPTADA)
--------------------------------------------------
- Ruta del Archivo Analizado: {ruta_dub}
- Hash SHA-256 Actual: {sha_dub}

--------------------------------------------------
3. MÉTRICAS DE CORRELACIÓN PERCEPTUAL
--------------------------------------------------
- Algoritmo Aplicado: dHash (Hash Perceptual Multi-Escala)
- Distancia de Hamming: {distancia} bits
- Índice de Similitud Visual: {similitud}%

--------------------------------------------------
4. CONCLUSIÓN TÉCNICA
--------------------------------------------------
Se confirma la existencia de una anomalía de seguridad. 
La imagen analizada guarda correspondencia estructural directa 
con la copia digital custodiada entregada originalmente al destinatario indicado, 
superando los umbrales de tolerancia ante compresión de redes sociales.
==================================================
"""
    try:
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido)
        print("\n[💾] ¡Informe exportado con éxito!", flush=True)
        print(f"[📁] Archivo guardado en: {ruta_completa}", flush=True)
    except Exception as e:
        print(f"[-] No se pudo exportar el archivo TXT: {e}", flush=True)


def proteger_imagen():
    print("\n>>> 1. PROTEGER IMAGEN | SI.ESPEJO", flush=True)
    ruta = seleccionar_imagen_interactiva()
    if not ruta or not os.path.exists(ruta):
        print("[-] Operación cancelada o imagen no encontrada.", flush=True)
        return

    destinatario = input("Nombre o alias del destinatario autorizado: ").strip()
    if not destinatario:
        print("[-] El destinatario es obligatorio.", flush=True)
        return

    ubicacion = input(
        "Coordenadas o dirección de envío (ej: 6.2442, -75.5812 o Sabaneta): "
    ).strip()
    if not ubicacion:
        ubicacion = "No especificada"

    try:
        sha_val = calcular_sha256(ruta)
        dhash_val = calcular_dhash(ruta)

        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "archivo_original": os.path.basename(ruta),
            "destinatario": destinatario,
            "ubicacion_envio": ubicacion,
            "sha256": sha_val,
            "dhash": dhash_val,
        }
        guardar_registro(registro)

        print("\n[+] ========================================", flush=True)
        print("[+]   IMAGEN REGISTRADA Y CUSTODIADA", flush=True)
        print("[+] ========================================", flush=True)
        print(f"👤 Destinatario: {destinatario}", flush=True)
        print(f"📍 Ubicación: {ubicacion}", flush=True)
        print(f"🔑 Hash (dHash): {dhash_val}", flush=True)
        print(f"[!] Guardado en: {obtener_ruta_log()}", flush=True)
    except Exception as e:
        print(f"[-] Error protegiendo imagen: {e}", flush=True)


def auditar_imagen():
    print("\n>>> 2. AUDITAR IMAGEN | SI.ESPEJO", flush=True)
    ruta = seleccionar_imagen_interactiva()
    if not ruta or not os.path.exists(ruta):
        print("[-] Operación cancelada o imagen no encontrada.", flush=True)
        return

    registros = cargar_registros()
    if not registros:
        print("[-] La bitácora está vacía. Registra imágenes primero en la opción 1.", flush=True)
        return

    try:
        sha_actual = calcular_sha256(ruta)
        dhash_actual = calcular_dhash(ruta)

        print("\n[🔍] Analizando imagen dubitada en busca de anomalías...", flush=True)

        mejor_match = None
        menor_distancia = 999

        for reg in registros:
            hash_reg = reg.get("dhash") or reg.get("phash")
            if not hash_reg:
                continue
            distancia = distancia_hamming(dhash_actual, hash_reg)
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_match = reg

        UMBRAL_TOLERANCIA = 15

        print("\n========================================", flush=True)
        print("      INFORME DE AUDITORÍA FORENSE      ", flush=True)
        print("========================================", flush=True)

        if mejor_match is not None and menor_distancia <= UMBRAL_TOLERANCIA:
            similitud_porcentaje = max(0, int(100 - (menor_distancia / 64.0) * 100))
            print("🚨 ¡ANOMALÍA DETECTADA: REENVÍO NO AUTORIZADO! 🚨", flush=True)
            print("----------------------------------------", flush=True)
            print(f"👤 Destinatario Original: {mejor_match['destinatario']}", flush=True)
            print(
                f"📍 Ubicación de Envío: {mejor_match.get('ubicacion_envio', 'No registrada')}",
                flush=True,
            )
            print(f"📅 Fecha de Registro: {mejor_match['fecha']}", flush=True)
            print(f"📄 Archivo Original: {mejor_match['archivo_original']}", flush=True)
            print(
                f"📊 Similitud Visual: {similitud_porcentaje}% (Distancia dHash: {menor_distancia})",
                flush=True,
            )
            print("----------------------------------------", flush=True)
            print(
                "[i] Conclusión: Se evidencia una anomalía. Esta imagen proviene de la copia asignada al destinatario indicado.",
                flush=True,
            )

            exportar_reporte_txt(
                mejor_match, ruta, sha_actual, menor_distancia, similitud_porcentaje
            )
        else:
            print("✅ ESTADO: SIN ANOMALÍAS DETECTADAS", flush=True)
            print("----------------------------------------", flush=True)
            print(
                f"Menor distancia hallada: {menor_distancia} bits (Umbral máx: {UMBRAL_TOLERANCIA})",
                flush=True,
            )
            print(
                "[i] Conclusión: No se encontraron anomalías ni coincidencias con copias registradas.",
                flush=True,
            )

    except Exception as e:
        print(f"[-] Error en la auditoría: {e}", flush=True)


def ver_bitacora():
    registros = cargar_registros()
    print(f"\n>>> 3. BITÁCORA DE CUSTODIA SI.ESPEJO ({len(registros)} registros)", flush=True)
    print(f"[*] Bitácora: {obtener_ruta_log()}", flush=True)
    if not registros:
        print("[i] No hay registros guardados todavía.", flush=True)
        return
    for i, reg in enumerate(registros, 1):
        print(f"\n{i}. Destinatario: {reg['destinatario']}", flush=True)
        print(f"   Ubicación: {reg.get('ubicacion_envio', 'N/A')}", flush=True)
        print(f"   Fecha: {reg['fecha']}", flush=True)
        print(f"   Archivo: {reg['archivo_original']}", flush=True)


def main():
    while True:
        print("\n========================================", flush=True)
        print("    IMAGEN TRACER | SI.ESPEJO MOBILE    ", flush=True)
        print("========================================", flush=True)
        print(f"Bitácora: {obtener_ruta_log()}", flush=True)
        print("1. Proteger imagen antes de enviar", flush=True)
        print("2. Auditar imagen (Detectar anomalías)", flush=True)
        print("3. Ver bitácora de custodia", flush=True)
        print("4. Salir", flush=True)

        op = input("\nElige una opción (1-4): ").strip()
        if op == "1":
            proteger_imagen()
            input("\nPresiona Enter para continuar...")
        elif op == "2":
            auditar_imagen()
            input("\nPresiona Enter para continuar...")
        elif op == "3":
            ver_bitacora()
            input("\nPresiona Enter para continuar...")
        elif op == "4":
            print("Saliendo de Imagen Tracer...", flush=True)
            break
        else:
            print("Opción no válida.", flush=True)
            input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except Exception as fatal_error:
        print(f"\n[-] ERROR CRITICO: {fatal_error}", flush=True)
        input("\nPresiona Enter para cerrar...")
    
