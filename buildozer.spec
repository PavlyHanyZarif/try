[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
version = 1.0.0
version.filename = main.py
version.regex = __version__ = ['"](.*)['"]

[buildozer]
log_level = 2

[requirements]
python3, kivy

[android]
# Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Build options
android.api = 31
android.ndk = 23b
android.arch = arm64-v8a, armeabi-v7a
android.minapi = 21

# Fixes common issues with SDL2
android.requirements = python3, kivy, sdl2_ttf, sdl2_image, sdl2_mixer, sdl2_net
android.ndk_path = /home/user/android-ndk-r23b

# App icon (replace with your icon path)
icon.filename = icon.png
