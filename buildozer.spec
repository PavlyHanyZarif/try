[app]
title = BavlyApp
package.name = bavly
package.domain = com.yourdomain
source.include_exts = py,png,jpg,kv,atlas
source.exclude_patterns = .git*,__pycache__*
source.include_patterns = Bavly.py
version = 1.0.0
requirements = python3,kivy,kivy_garden,qrcode,opencv-python,pyzbar,pandas
android.permissions = CAMERA, INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
fullscreen = 1
android.arch = arm64-v8a
