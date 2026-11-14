[app]
title = Imagen Tracer SI ESPEJO
package.name = imagentracer
package.domain = com.siespejo.tracer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.1
requirements = python3,kivy==2.3.0,Pillow
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:android]
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license_agreements = True
p4a.bootstrap = sdl2
