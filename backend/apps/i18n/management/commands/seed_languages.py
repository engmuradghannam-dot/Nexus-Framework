"""Seed a comprehensive list of world languages (idempotent)."""
from django.core.management.base import BaseCommand

from apps.i18n.models import Language

RTL = {"ar", "fa", "ur", "he", "ps"}

# (code, English name, native name, flag)
LANGUAGES = [
    ("en", "English", "English", "🇬🇧"), ("ar", "Arabic", "العربية", "🇸🇦"),
    ("fr", "French", "Français", "🇫🇷"), ("de", "German", "Deutsch", "🇩🇪"),
    ("es", "Spanish", "Español", "🇪🇸"), ("zh", "Chinese", "中文", "🇨🇳"),
    ("hi", "Hindi", "हिन्दी", "🇮🇳"), ("pt", "Portuguese", "Português", "🇵🇹"),
    ("ru", "Russian", "Русский", "🇷🇺"), ("ja", "Japanese", "日本語", "🇯🇵"),
    ("ko", "Korean", "한국어", "🇰🇷"), ("it", "Italian", "Italiano", "🇮🇹"),
    ("tr", "Turkish", "Türkçe", "🇹🇷"), ("fa", "Persian", "فارسی", "🇮🇷"),
    ("ur", "Urdu", "اردو", "🇵🇰"), ("he", "Hebrew", "עברית", "🇮🇱"),
    ("nl", "Dutch", "Nederlands", "🇳🇱"), ("pl", "Polish", "Polski", "🇵🇱"),
    ("uk", "Ukrainian", "Українська", "🇺🇦"), ("ro", "Romanian", "Română", "🇷🇴"),
    ("el", "Greek", "Ελληνικά", "🇬🇷"), ("cs", "Czech", "Čeština", "🇨🇿"),
    ("sv", "Swedish", "Svenska", "🇸🇪"), ("hu", "Hungarian", "Magyar", "🇭🇺"),
    ("da", "Danish", "Dansk", "🇩🇰"), ("fi", "Finnish", "Suomi", "🇫🇮"),
    ("no", "Norwegian", "Norsk", "🇳🇴"), ("sk", "Slovak", "Slovenčina", "🇸🇰"),
    ("bg", "Bulgarian", "Български", "🇧🇬"), ("hr", "Croatian", "Hrvatski", "🇭🇷"),
    ("sr", "Serbian", "Српски", "🇷🇸"), ("lt", "Lithuanian", "Lietuvių", "🇱🇹"),
    ("sl", "Slovenian", "Slovenščina", "🇸🇮"), ("et", "Estonian", "Eesti", "🇪🇪"),
    ("lv", "Latvian", "Latviešu", "🇱🇻"), ("th", "Thai", "ไทย", "🇹🇭"),
    ("vi", "Vietnamese", "Tiếng Việt", "🇻🇳"), ("id", "Indonesian", "Bahasa Indonesia", "🇮🇩"),
    ("ms", "Malay", "Bahasa Melayu", "🇲🇾"), ("tl", "Filipino", "Filipino", "🇵🇭"),
    ("bn", "Bengali", "বাংলা", "🇧🇩"), ("ta", "Tamil", "தமிழ்", "🇮🇳"),
    ("te", "Telugu", "తెలుగు", "🇮🇳"), ("mr", "Marathi", "मराठी", "🇮🇳"),
    ("gu", "Gujarati", "ગુજરાતી", "🇮🇳"), ("kn", "Kannada", "ಕನ್ನಡ", "🇮🇳"),
    ("ml", "Malayalam", "മലയാളം", "🇮🇳"), ("pa", "Punjabi", "ਪੰਜਾਬੀ", "🇮🇳"),
    ("sw", "Swahili", "Kiswahili", "🇰🇪"), ("am", "Amharic", "አማርኛ", "🇪🇹"),
    ("ha", "Hausa", "Hausa", "🇳🇬"), ("yo", "Yoruba", "Yorùbá", "🇳🇬"),
    ("ig", "Igbo", "Igbo", "🇳🇬"), ("zu", "Zulu", "isiZulu", "🇿🇦"),
    ("af", "Afrikaans", "Afrikaans", "🇿🇦"), ("sq", "Albanian", "Shqip", "🇦🇱"),
    ("az", "Azerbaijani", "Azərbaycan", "🇦🇿"), ("hy", "Armenian", "Հայերեն", "🇦🇲"),
    ("ka", "Georgian", "ქართული", "🇬🇪"), ("kk", "Kazakh", "Қазақ", "🇰🇿"),
    ("uz", "Uzbek", "Oʻzbek", "🇺🇿"), ("mn", "Mongolian", "Монгол", "🇲🇳"),
    ("ne", "Nepali", "नेपाली", "🇳🇵"), ("si", "Sinhala", "සිංහල", "🇱🇰"),
    ("km", "Khmer", "ខ្មែរ", "🇰🇭"), ("lo", "Lao", "ລາວ", "🇱🇦"),
    ("my", "Burmese", "မြန်မာ", "🇲🇲"), ("ps", "Pashto", "پښتو", "🇦🇫"),
    ("ca", "Catalan", "Català", "🇪🇸"), ("eu", "Basque", "Euskara", "🇪🇸"),
    ("gl", "Galician", "Galego", "🇪🇸"), ("is", "Icelandic", "Íslenska", "🇮🇸"),
    ("ga", "Irish", "Gaeilge", "🇮🇪"), ("mt", "Maltese", "Malti", "🇲🇹"),
    ("mk", "Macedonian", "Македонски", "🇲🇰"), ("be", "Belarusian", "Беларуская", "🇧🇾"),
]


class Command(BaseCommand):
    help = "Seed a comprehensive list of world languages (idempotent)."

    def handle(self, *args, **options):
        created = 0
        for code, name, native, flag in LANGUAGES:
            _, was_created = Language.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "name_local": native,
                    "direction": "rtl" if code in RTL else "ltr",
                    "flag_emoji": flag,
                    "is_default": code == "en",
                    "decimal_separator": "." if code != "de" else ",",
                    "thousands_separator": "," if code != "de" else ".",
                },
            )
            created += 1 if was_created else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"Languages ensured: {Language.objects.count()} total "
                f"({created} newly added)"
            )
        )
