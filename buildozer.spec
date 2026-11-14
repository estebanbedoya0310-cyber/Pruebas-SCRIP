[app]
title = Imagen Tracer SI.ESPEJO
package.name = imagentracesiespejo
package.domain = org.siespejo
source.include_exts = py,png,jpg,json
source.dir = .
version = 1.0
requirements = python3,kivy,pillow
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.minapi = 21
android.sdk = 30
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
