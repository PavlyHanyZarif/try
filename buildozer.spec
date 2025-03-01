[app]
version.regex = __version__ = ['"](.*)['"]
# اسم التطبيق
title = BavlyApp

# اسم الحزمة (يُفضل أن يكون بصيغة معكوسة للنطاق مثل com.example.bavlyapp)
package.name = bavlyapp
package.domain = org.example

# مسار الكود الرئيسي
source.dir = .

# ملف البداية الرئيسي
source.include_exts = py,png,jpg,kv,atlas

# الأيقونة (يمكنك تعديل المسار إلى أيقونة مخصصة)
icon.filename = icon.png

# المسموح لهم باستخدام التطبيق
orientation = portrait

# المكتبات المطلوبة
requirements = python3,kivy,kivy_garden,sqlite3,qrcode,opencv,pyzbar,pandas

# الصلاحيات المطلوبة
android.permissions = INTERNET, CAMERA

# إخفاء وحدة التحكم
fullscreen = 0

# اسم الـ APK النهائي
android.archs = arm64-v8a, armeabi-v7a
android.release = 0

[buildozer]
log_level = 2
warn_on_root = 1
