# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for KPI Tracker standalone Windows app (pywebview window).
Build with:  pyinstaller kpi_tracker.spec
Output:      dist\KPITracker\KPITracker.exe
"""

from pathlib import Path

SRC  = Path('kpi_tracker')
VENV = SRC / 'venv' / 'Lib' / 'site-packages'
WEBVIEW_LIB = VENV / 'webview' / 'lib'

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------
datas = [
    # App templates + migrations
    (str(SRC / 'tasks' / 'templates'),    'tasks/templates'),
    (str(SRC / 'tasks' / 'migrations'),   'tasks/migrations'),
    (str(SRC / 'tasks' / 'templatetags'), 'tasks/templatetags'),

    # Collected static assets
    (str(SRC / 'staticfiles'), 'staticfiles'),

    # Django built-in templates
    (str(VENV / 'django' / 'contrib' / 'admin' / 'templates'),
     'django/contrib/admin/templates'),
    (str(VENV / 'django' / 'contrib' / 'auth' / 'templates'),
     'django/contrib/auth/templates'),

    # Third-party templates
    (str(VENV / 'crispy_bootstrap5' / 'templates'),    'crispy_bootstrap5/templates'),
    (str(VENV / 'crispy_forms'      / 'templatetags'), 'crispy_forms/templatetags'),
    (str(VENV / 'widget_tweaks'     / 'templatetags'), 'widget_tweaks/templatetags'),

    # Django locale files
    (str(VENV / 'django' / 'contrib' / 'admin' / 'locale'),
     'django/contrib/admin/locale'),
    (str(VENV / 'django' / 'contrib' / 'auth' / 'locale'),
     'django/contrib/auth/locale'),

    # pywebview — WebView2 DLLs and .NET assemblies
    (str(WEBVIEW_LIB), 'webview/lib'),
]

# ---------------------------------------------------------------------------
# Hidden imports
# ---------------------------------------------------------------------------
hiddenimports = [
    # Django
    'django.template.loaders.app_directories',
    'django.template.loaders.filesystem',
    'django.template.context_processors',
    'django.contrib.admin',
    'django.contrib.admin.apps',
    'django.contrib.auth',
    'django.contrib.auth.backends',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sessions.backends.db',
    'django.contrib.messages',
    'django.contrib.messages.storage.fallback',
    'django.contrib.staticfiles',
    'django.db.backends.sqlite3',
    'django.middleware.security',
    'django.middleware.clickjacking',

    # Third-party Django
    'crispy_forms',
    'crispy_forms.templatetags.crispy_forms_tags',
    'crispy_forms.templatetags.crispy_forms_field',
    'crispy_bootstrap5',
    'widget_tweaks',
    'widget_tweaks.templatetags.widget_tweaks',

    # pywebview + its dependencies
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr',
    'clr_loader',
    'pythonnet',

    # App
    'tasks',
    'tasks.apps',
    'tasks.models',
    'tasks.views',
    'tasks.urls',
    'tasks.forms',
    'tasks.admin',
    'tasks.context_processors',
    'tasks.middleware',
    'tasks.templatetags.custom_filters',
    'tasks.templatetags.form_tags',

    # stdlib
    'sqlparse',
    'colorama',
    '_sqlite3',
    'encodings',
    'encodings.utf_8',
    'encodings.ascii',
    'encodings.latin_1',
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(SRC / 'launcher.py')],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'google',
        'grpc',
        'PIL',
        'numpy',
        'pandas',
        'matplotlib',
        'scipy',
        'tkinter',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KPITracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,           # Temporarily on to diagnose crash
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='KPITracker',
)
