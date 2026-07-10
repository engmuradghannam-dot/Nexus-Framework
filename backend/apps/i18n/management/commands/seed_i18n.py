"""Seed 6 languages (EN, AR, FR, DE, ES, ZH) with 100+ translations."""
from django.core.management.base import BaseCommand

from apps.i18n.models import Language, Translation


class Command(BaseCommand):
    help = "Seed languages and translations for i18n"

    def handle(self, *args, **options):
        languages = [
            {
                "code": "en",
                "name": "English",
                "name_local": "English",
                "direction": "ltr",
                "is_default": True,
                "flag_emoji": "🇬🇧",
                "decimal_separator": ".",
                "thousands_separator": ",",
                "date_format": "YYYY-MM-DD",
                "time_format": "HH:mm",
                "first_day_of_week": 7,
            },
            {
                "code": "ar",
                "name": "Arabic",
                "name_local": "العربية",
                "direction": "rtl",
                "is_default": False,
                "flag_emoji": "🇸🇦",
                "decimal_separator": ".",
                "thousands_separator": ",",
                "date_format": "YYYY/MM/DD",
                "time_format": "HH:mm",
                "first_day_of_week": 6,
            },
            {
                "code": "fr",
                "name": "French",
                "name_local": "Français",
                "direction": "ltr",
                "is_default": False,
                "flag_emoji": "🇫🇷",
                "decimal_separator": ",",
                "thousands_separator": " ",
                "date_format": "DD/MM/YYYY",
                "time_format": "HH:mm",
                "first_day_of_week": 1,
            },
            {
                "code": "de",
                "name": "German",
                "name_local": "Deutsch",
                "direction": "ltr",
                "is_default": False,
                "flag_emoji": "🇩🇪",
                "decimal_separator": ",",
                "thousands_separator": ".",
                "date_format": "DD.MM.YYYY",
                "time_format": "HH:mm",
                "first_day_of_week": 1,
            },
            {
                "code": "es",
                "name": "Spanish",
                "name_local": "Español",
                "direction": "ltr",
                "is_default": False,
                "flag_emoji": "🇪🇸",
                "decimal_separator": ",",
                "thousands_separator": ".",
                "date_format": "DD/MM/YYYY",
                "time_format": "HH:mm",
                "first_day_of_week": 1,
            },
            {
                "code": "zh",
                "name": "Chinese",
                "name_local": "中文",
                "direction": "ltr",
                "is_default": False,
                "flag_emoji": "🇨🇳",
                "decimal_separator": ".",
                "thousands_separator": ",",
                "date_format": "YYYY-MM-DD",
                "time_format": "HH:mm",
                "first_day_of_week": 1,
            },
        ]

        created_count = 0
        for data in languages:
            lang, created = Language.objects.update_or_create(
                code=data["code"],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created language: {lang}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated language: {lang}"))

        # Seed translations
        translations_data = [
            # Core / Navigation
            ("en", "dashboard", "Dashboard", "navigation"),
            ("ar", "dashboard", "لوحة المعلومات", "navigation"),
            ("fr", "dashboard", "Tableau de bord", "navigation"),
            ("de", "dashboard", "Dashboard", "navigation"),
            ("es", "dashboard", "Panel de control", "navigation"),
            ("zh", "dashboard", "仪表板", "navigation"),

            ("en", "projects", "Projects", "navigation"),
            ("ar", "projects", "المشاريع", "navigation"),
            ("fr", "projects", "Projets", "navigation"),
            ("de", "projects", "Projekte", "navigation"),
            ("es", "projects", "Proyectos", "navigation"),
            ("zh", "projects", "项目", "navigation"),

            ("en", "inventory", "Inventory", "navigation"),
            ("ar", "inventory", "المخزون", "navigation"),
            ("fr", "inventory", "Inventaire", "navigation"),
            ("de", "inventory", "Bestand", "navigation"),
            ("es", "inventory", "Inventario", "navigation"),
            ("zh", "inventory", "库存", "navigation"),

            ("en", "users", "Users", "navigation"),
            ("ar", "users", "المستخدمين", "navigation"),
            ("fr", "users", "Utilisateurs", "navigation"),
            ("de", "users", "Benutzer", "navigation"),
            ("es", "users", "Usuarios", "navigation"),
            ("zh", "users", "用户", "navigation"),

            ("en", "settings", "Settings", "navigation"),
            ("ar", "settings", "الإعدادات", "navigation"),
            ("fr", "settings", "Paramètres", "navigation"),
            ("de", "settings", "Einstellungen", "navigation"),
            ("es", "settings", "Configuración", "navigation"),
            ("zh", "settings", "设置", "navigation"),

            ("en", "logout", "Logout", "navigation"),
            ("ar", "logout", "تسجيل الخروج", "navigation"),
            ("fr", "logout", "Déconnexion", "navigation"),
            ("de", "logout", "Abmelden", "navigation"),
            ("es", "logout", "Cerrar sesión", "navigation"),
            ("zh", "logout", "退出", "navigation"),

            # Common Actions
            ("en", "save", "Save", "actions"),
            ("ar", "save", "حفظ", "actions"),
            ("fr", "save", "Enregistrer", "actions"),
            ("de", "save", "Speichern", "actions"),
            ("es", "save", "Guardar", "actions"),
            ("zh", "save", "保存", "actions"),

            ("en", "cancel", "Cancel", "actions"),
            ("ar", "cancel", "إلغاء", "actions"),
            ("fr", "cancel", "Annuler", "actions"),
            ("de", "cancel", "Abbrechen", "actions"),
            ("es", "cancel", "Cancelar", "actions"),
            ("zh", "cancel", "取消", "actions"),

            ("en", "delete", "Delete", "actions"),
            ("ar", "delete", "حذف", "actions"),
            ("fr", "delete", "Supprimer", "actions"),
            ("de", "delete", "Löschen", "actions"),
            ("es", "delete", "Eliminar", "actions"),
            ("zh", "delete", "删除", "actions"),

            ("en", "edit", "Edit", "actions"),
            ("ar", "edit", "تعديل", "actions"),
            ("fr", "edit", "Modifier", "actions"),
            ("de", "edit", "Bearbeiten", "actions"),
            ("es", "edit", "Editar", "actions"),
            ("zh", "edit", "编辑", "actions"),

            ("en", "create", "Create", "actions"),
            ("ar", "create", "إنشاء", "actions"),
            ("fr", "create", "Créer", "actions"),
            ("de", "create", "Erstellen", "actions"),
            ("es", "create", "Crear", "actions"),
            ("zh", "create", "创建", "actions"),

            ("en", "search", "Search", "actions"),
            ("ar", "search", "بحث", "actions"),
            ("fr", "search", "Rechercher", "actions"),
            ("de", "search", "Suchen", "actions"),
            ("es", "search", "Buscar", "actions"),
            ("zh", "search", "搜索", "actions"),

            ("en", "filter", "Filter", "actions"),
            ("ar", "filter", "تصفية", "actions"),
            ("fr", "filter", "Filtrer", "actions"),
            ("de", "filter", "Filtern", "actions"),
            ("es", "filter", "Filtrar", "actions"),
            ("zh", "filter", "筛选", "actions"),

            ("en", "export", "Export", "actions"),
            ("ar", "export", "تصدير", "actions"),
            ("fr", "export", "Exporter", "actions"),
            ("de", "export", "Exportieren", "actions"),
            ("es", "export", "Exportar", "actions"),
            ("zh", "export", "导出", "actions"),

            ("en", "import", "Import", "actions"),
            ("ar", "import", "استيراد", "actions"),
            ("fr", "import", "Importer", "actions"),
            ("de", "import", "Importieren", "actions"),
            ("es", "import", "Importar", "actions"),
            ("zh", "import", "导入", "actions"),

            # Status
            ("en", "active", "Active", "status"),
            ("ar", "active", "نشط", "status"),
            ("fr", "active", "Actif", "status"),
            ("de", "active", "Aktiv", "status"),
            ("es", "active", "Activo", "status"),
            ("zh", "active", "活跃", "status"),

            ("en", "inactive", "Inactive", "status"),
            ("ar", "inactive", "غير نشط", "status"),
            ("fr", "inactive", "Inactif", "status"),
            ("de", "inactive", "Inaktiv", "status"),
            ("es", "inactive", "Inactivo", "status"),
            ("zh", "inactive", "不活跃", "status"),

            ("en", "pending", "Pending", "status"),
            ("ar", "pending", "معلق", "status"),
            ("fr", "pending", "En attente", "status"),
            ("de", "pending", "Ausstehend", "status"),
            ("es", "pending", "Pendiente", "status"),
            ("zh", "pending", "待定", "status"),

            ("en", "completed", "Completed", "status"),
            ("ar", "completed", "مكتمل", "status"),
            ("fr", "completed", "Terminé", "status"),
            ("de", "completed", "Abgeschlossen", "status"),
            ("es", "completed", "Completado", "status"),
            ("zh", "completed", "已完成", "status"),

            # Taxes
            ("en", "taxes", "Taxes", "taxes"),
            ("ar", "taxes", "الضرائب", "taxes"),
            ("fr", "taxes", "Taxes", "taxes"),
            ("de", "taxes", "Steuern", "taxes"),
            ("es", "taxes", "Impuestos", "taxes"),
            ("zh", "taxes", "税务", "taxes"),

            ("en", "vat", "VAT", "taxes"),
            ("ar", "vat", "ضريبة القيمة المضافة", "taxes"),
            ("fr", "vat", "TVA", "taxes"),
            ("de", "vat", "MwSt", "taxes"),
            ("es", "vat", "IVA", "taxes"),
            ("zh", "vat", "增值税", "taxes"),

            ("en", "tax_rate", "Tax Rate", "taxes"),
            ("ar", "tax_rate", "معدل الضريبة", "taxes"),
            ("fr", "tax_rate", "Taux d'imposition", "taxes"),
            ("de", "tax_rate", "Steuersatz", "taxes"),
            ("es", "tax_rate", "Tasa impositiva", "taxes"),
            ("zh", "tax_rate", "税率", "taxes"),

            ("en", "tax_calculator", "Tax Calculator", "taxes"),
            ("ar", "tax_calculator", "حاسبة الضريبة", "taxes"),
            ("fr", "tax_calculator", "Calculateur de taxe", "taxes"),
            ("de", "tax_calculator", "Steuerrechner", "taxes"),
            ("es", "tax_calculator", "Calculadora de impuestos", "taxes"),
            ("zh", "tax_calculator", "税务计算器", "taxes"),

            # i18n
            ("en", "i18n", "Localization", "i18n"),
            ("ar", "i18n", "التوطين", "i18n"),
            ("fr", "i18n", "Localisation", "i18n"),
            ("de", "i18n", "Lokalisierung", "i18n"),
            ("es", "i18n", "Localización", "i18n"),
            ("zh", "i18n", "本地化", "i18n"),

            ("en", "language", "Language", "i18n"),
            ("ar", "language", "اللغة", "i18n"),
            ("fr", "language", "Langue", "i18n"),
            ("de", "language", "Sprache", "i18n"),
            ("es", "language", "Idioma", "i18n"),
            ("zh", "language", "语言", "i18n"),

            ("en", "translation", "Translation", "i18n"),
            ("ar", "translation", "الترجمة", "i18n"),
            ("fr", "translation", "Traduction", "i18n"),
            ("de", "translation", "Übersetzung", "i18n"),
            ("es", "translation", "Traducción", "i18n"),
            ("zh", "translation", "翻译", "i18n"),

            ("en", "bulk_upload", "Bulk Upload", "i18n"),
            ("ar", "bulk_upload", "رفع جماعي", "i18n"),
            ("fr", "bulk_upload", "Téléchargement en masse", "i18n"),
            ("de", "bulk_upload", "Massenupload", "i18n"),
            ("es", "bulk_upload", "Carga masiva", "i18n"),
            ("zh", "bulk_upload", "批量上传", "i18n"),

            # Messages
            ("en", "success", "Success", "messages"),
            ("ar", "success", "نجاح", "messages"),
            ("fr", "success", "Succès", "messages"),
            ("de", "success", "Erfolg", "messages"),
            ("es", "success", "Éxito", "messages"),
            ("zh", "success", "成功", "messages"),

            ("en", "error", "Error", "messages"),
            ("ar", "error", "خطأ", "messages"),
            ("fr", "error", "Erreur", "messages"),
            ("de", "error", "Fehler", "messages"),
            ("es", "error", "Error", "messages"),
            ("zh", "error", "错误", "messages"),

            ("en", "warning", "Warning", "messages"),
            ("ar", "warning", "تحذير", "messages"),
            ("fr", "warning", "Avertissement", "messages"),
            ("de", "warning", "Warnung", "messages"),
            ("es", "warning", "Advertencia", "messages"),
            ("zh", "warning", "警告", "messages"),

            ("en", "info", "Info", "messages"),
            ("ar", "info", "معلومات", "messages"),
            ("fr", "info", "Info", "messages"),
            ("de", "info", "Info", "messages"),
            ("es", "info", "Información", "messages"),
            ("zh", "info", "信息", "messages"),

            # HR
            ("en", "employees", "Employees", "hr"),
            ("ar", "employees", "الموظفين", "hr"),
            ("fr", "employees", "Employés", "hr"),
            ("de", "employees", "Mitarbeiter", "hr"),
            ("es", "employees", "Empleados", "hr"),
            ("zh", "employees", "员工", "hr"),

            ("en", "departments", "Departments", "hr"),
            ("ar", "departments", "الأقسام", "hr"),
            ("fr", "departments", "Départements", "hr"),
            ("de", "departments", "Abteilungen", "hr"),
            ("es", "departments", "Departamentos", "hr"),
            ("zh", "departments", "部门", "hr"),

            # CRM
            ("en", "customers", "Customers", "crm"),
            ("ar", "customers", "العملاء", "crm"),
            ("fr", "customers", "Clients", "crm"),
            ("de", "customers", "Kunden", "crm"),
            ("es", "customers", "Clientes", "crm"),
            ("zh", "customers", "客户", "crm"),

            ("en", "leads", "Leads", "crm"),
            ("ar", "leads", "العملاء المحتملين", "crm"),
            ("fr", "leads", "Prospects", "crm"),
            ("de", "leads", "Leads", "crm"),
            ("es", "leads", "Oportunidades", "crm"),
            ("zh", "leads", "潜在客户", "crm"),

            # Inventory
            ("en", "items", "Items", "inventory"),
            ("ar", "items", "العناصر", "inventory"),
            ("fr", "items", "Articles", "inventory"),
            ("de", "items", "Artikel", "inventory"),
            ("es", "items", "Artículos", "inventory"),
            ("zh", "items", "物品", "inventory"),

            ("en", "warehouses", "Warehouses", "inventory"),
            ("ar", "warehouses", "المستودعات", "inventory"),
            ("fr", "warehouses", "Entrepôts", "inventory"),
            ("de", "warehouses", "Lager", "inventory"),
            ("es", "warehouses", "Almacenes", "inventory"),
            ("zh", "warehouses", "仓库", "inventory"),

            # AI
            ("en", "ai_engine", "AI Engine", "ai"),
            ("ar", "ai_engine", "محرك الذكاء الاصطناعي", "ai"),
            ("fr", "ai_engine", "Moteur IA", "ai"),
            ("de", "ai_engine", "KI-Engine", "ai"),
            ("es", "ai_engine", "Motor de IA", "ai"),
            ("zh", "ai_engine", "人工智能引擎", "ai"),

            ("en", "predictions", "Predictions", "ai"),
            ("ar", "predictions", "التنبؤات", "ai"),
            ("fr", "predictions", "Prédictions", "ai"),
            ("de", "predictions", "Vorhersagen", "ai"),
            ("es", "predictions", "Predicciones", "ai"),
            ("zh", "predictions", "预测", "ai"),

            # Auth
            ("en", "login", "Login", "auth"),
            ("ar", "login", "تسجيل الدخول", "auth"),
            ("fr", "login", "Connexion", "auth"),
            ("de", "login", "Anmelden", "auth"),
            ("es", "login", "Iniciar sesión", "auth"),
            ("zh", "login", "登录", "auth"),

            ("en", "password", "Password", "auth"),
            ("ar", "password", "كلمة المرور", "auth"),
            ("fr", "password", "Mot de passe", "auth"),
            ("de", "password", "Passwort", "auth"),
            ("es", "password", "Contraseña", "auth"),
            ("zh", "password", "密码", "auth"),

            ("en", "email", "Email", "auth"),
            ("ar", "email", "البريد الإلكتروني", "auth"),
            ("fr", "email", "Email", "auth"),
            ("de", "email", "E-Mail", "auth"),
            ("es", "email", "Correo electrónico", "auth"),
            ("zh", "email", "电子邮件", "auth"),

            ("en", "remember_me", "Remember me", "auth"),
            ("ar", "remember_me", "تذكرني", "auth"),
            ("fr", "remember_me", "Se souvenir de moi", "auth"),
            ("de", "remember_me", "Angemeldet bleiben", "auth"),
            ("es", "remember_me", "Recordarme", "auth"),
            ("zh", "remember_me", "记住我", "auth"),

            ("en", "forgot_password", "Forgot password?", "auth"),
            ("ar", "forgot_password", "نسيت كلمة المرور؟", "auth"),
            ("fr", "forgot_password", "Mot de passe oublié?", "auth"),
            ("de", "forgot_password", "Passwort vergessen?", "auth"),
            ("es", "forgot_password", "¿Olvidaste tu contraseña?", "auth"),
            ("zh", "forgot_password", "忘记密码？", "auth"),
        ]

        trans_created = 0
        for code, key, value, context in translations_data:
            try:
                lang = Language.objects.get(code=code)
            except Language.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Language {code} not found, skipping"))
                continue

            trans, created = Translation.objects.update_or_create(
                language=lang,
                key=key,
                context=context,
                defaults={"value": value},
            )
            if created:
                trans_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded {created_count} languages, {trans_created} translations."
        ))
