# tree_generator.py
# Standard Library
from pathlib import Path

# --- KONFİGÜRASYON ---
# Script'in çalıştırıldığı dizini başlangıç noktası olarak al
START_PATH = Path(".")

# Dosya türlerine göre renkli ikonlar
FILE_ICONS = {
    # Python dosyaları
    ".py": "🐍",
    ".pyi": "🐍",
    ".pyx": "🐍",
    # Web dosyaları
    ".html": "🌐",
    ".htm": "🌐",
    ".css": "🎨",
    ".js": "📜",
    ".ts": "📘",
    ".jsx": "⚛️",
    ".tsx": "⚛️",
    ".json": "📋",
    ".xml": "📄",
    # Veri dosyaları
    ".csv": "📊",
    ".xlsx": "📈",
    ".xls": "📈",
    ".sql": "🗃️",
    ".db": "🗃️",
    ".sqlite": "🗃️",
    ".sqlite3": "🗃️",
    # Döküman dosyaları
    ".md": "📝",
    ".txt": "📄",
    ".pdf": "📕",
    ".doc": "📘",
    ".docx": "📘",
    ".rtf": "📄",
    # Görsel dosyalar
    ".png": "🖼️",
    ".jpg": "🖼️",
    ".jpeg": "🖼️",
    ".gif": "🖼️",
    ".svg": "🎨",
    ".ico": "🎯",
    # Arşiv dosyaları
    ".zip": "📦",
    ".rar": "📦",
    ".7z": "📦",
    ".tar": "📦",
    ".gz": "📦",
    # Yapılandırma dosyaları
    ".yaml": "⚙️",
    ".yml": "⚙️",
    ".toml": "⚙️",
    ".ini": "⚙️",
    ".cfg": "⚙️",
    ".conf": "⚙️",
    ".env": "🔐",
    # Kod dosyaları
    ".c": "💾",
    ".cpp": "💾",
    ".h": "💾",
    ".java": "☕",
    ".cs": "🔷",
    ".php": "🐘",
    ".rb": "💎",
    ".go": "🐹",
    ".rs": "🦀",
    ".swift": "🦉",
    ".kt": "🎯",
    # Diğer
    ".log": "📋",
    ".lock": "🔒",
    ".bin": "⚙️",
    ".exe": "⚡",
    ".msi": "⚡",
    ".bat": "⚡",
    ".ps1": "💙",
    ".sh": "🐚",
}

# Klasör ikonu
FOLDER_ICON = "📁"

# Varsayılan dosya ikonu
DEFAULT_FILE_ICON = "📄"

# Görmezden gelinecek klasörlerin isimleri
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".vscode",
    ".idea",
    "kariyer-asistani-env",  # Sanal ortam klasörünüzün adı
    "build",
    "dist",
    "__MACOSX",
    "logs",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",  # Node.js modülleri
    ".next",
    ".nuxt",
    "coverage",
    ".coverage",
    ".tox",
    ".env",  # .env dosyasını da dışarıda bırakalım
    "tmp",
    "temp",
    ".tmp",
    ".temp",
}

# Görmezden gelinecek dosya uzantıları
EXCLUDE_EXTENSIONS = {".pyc", ".log", ".DS_Store", ".db", ".cache", ".pid", ".lock"}

# Görmezden gelinecek spesifik dosyalar
EXCLUDE_FILES = {
    "tree_generator.py",  # Script'in kendisini listelememesi için
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    "desktop.ini",
    "Thumbs.db",
    ".gitkeep",
    "package-lock.json",  # package-lock çok büyük olabiliyor
}

# --- SCRIPT MANTIĞI ---


def _get_file_icon(file_path: Path) -> str:
    """Dosya uzantısına göre ikon döner"""
    return FILE_ICONS.get(file_path.suffix.lower(), DEFAULT_FILE_ICON)


def _sort_directory_contents(directory: Path) -> list:
    """Dizin içeriğini klasörler önce olmak üzere sıralar"""
    files = []
    dirs = []
    for item in directory.iterdir():
        if item.is_dir():
            dirs.append(item)
        else:
            files.append(item)
    return sorted(dirs) + sorted(files)


def _filter_items(items: list) -> list:
    """Exclude listesindeki öğeleri filtreler"""
    filtered_items = []
    for item in items:
        if item.is_dir() and item.name in EXCLUDE_DIRS:
            continue
        if item.is_file() and (item.suffix in EXCLUDE_EXTENSIONS or item.name in EXCLUDE_FILES):
            continue
        filtered_items.append(item)
    return filtered_items


def _print_tree_level(items: list, prefix: str, output_file=None):
    """Bir seviyedeki öğeleri yazdırır ve alt seviyeye geçer"""
    pointers = ["├── "] * (len(items) - 1) + ["└── "]
    for pointer, path in zip(pointers, items):
        icon = FOLDER_ICON if path.is_dir() else _get_file_icon(path)

        line = f"{prefix}{pointer}{icon} {path.name}"
        print(line)
        if output_file:
            output_file.write(line + "\n")

        if path.is_dir():
            # Bir sonraki seviye için prefix'i ayarla
            extension = "│   " if pointer == "├── " else "    "
            generate_tree(path, prefix=prefix + extension, output_file=output_file)


def generate_tree(directory: Path, prefix: str = "", output_file=None):
    """
    Belirtilen dizin için ağaç yapısını oluşturan ve yazdıran
    özyinelemeli (recursive) bir fonksiyon.
    """
    try:
        items = _sort_directory_contents(directory)
        filtered_items = _filter_items(items)
        _print_tree_level(filtered_items, prefix, output_file)

    except PermissionError:
        error_line = f"{prefix}└── [Erişim Engellendi]"
        print(error_line)
        if output_file:
            output_file.write(error_line + "\n")
    except Exception as e:
        error_line = f"{prefix}└── [Hata: {e}]"
        print(error_line)
        if output_file:
            output_file.write(error_line + "\n")


def main():
    """Ana fonksiyon - komut satırı argümanlarını işler ve çıktıyı dosyaya yazar"""
    # Standard Library
    import argparse

    parser = argparse.ArgumentParser(description="Renkli ikonlu proje ağaç yapısı oluşturucu")
    parser.add_argument(
        "-p",
        "--path",
        help="Başlangıç dizini (varsayılan: mevcut dizin)",
        type=str,
        default=".",
    )

    args = parser.parse_args()

    start_path = Path(args.path)
    if not start_path.exists():
        print(f"❌ Hata: '{start_path}' dizini bulunamadı!")
        return

    # Başlık
    title = f"{FOLDER_ICON} {start_path.resolve().name}"
    print(title)

    output_filename = "project_tree.txt"

    # Dosyaya kaydetme
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(title + "\n")
            generate_tree(start_path, output_file=f)
        print(f"\n✅ Ağaç yapısı '{output_filename}' dosyasına kaydedildi!")
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")


if __name__ == "__main__":
    main()
