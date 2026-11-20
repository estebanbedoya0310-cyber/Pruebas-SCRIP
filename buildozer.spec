[app]
title = Imagen Tracer SI.ESPEJO
package.name = imagentracesiespejo
package.domain = org.siespejo
source.dir = .
source.include_exts = py,png,jpg,jpeg,json
version = 1.0
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,pillow
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools_version = 33.0.2
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
