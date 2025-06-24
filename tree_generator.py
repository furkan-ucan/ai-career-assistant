# tree_generator.py
# Standard Library
from pathlib import Path

# --- KONFİGÜRASYON ---
# Script'in çalıştırıldığı dizini başlangıç noktası olarak al
START_PATH = Path(".")

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
}

# Görmezden gelinecek dosya uzantıları
EXCLUDE_EXTENSIONS = {".pyc", ".log", ".DS_Store", ".db"}

# Görmezden gelinecek spesifik dosyalar
EXCLUDE_FILES = {"tree_generator.py"}  # Script'in kendisini listelememesi için

# --- SCRIPT MANTIĞI ---


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
        if item.is_file() and (
            item.suffix in EXCLUDE_EXTENSIONS or item.name in EXCLUDE_FILES
        ):
            continue
        filtered_items.append(item)
    return filtered_items


def _print_tree_level(items: list, prefix: str):
    """Bir seviyedeki öğeleri yazdırır ve alt seviyeye geçer"""
    pointers = ["├── "] * (len(items) - 1) + ["└── "]
    for pointer, path in zip(pointers, items):
        print(f"{prefix}{pointer}{path.name}")

        if path.is_dir():
            # Bir sonraki seviye için prefix'i ayarla
            extension = "│   " if pointer == "├── " else "    "
            generate_tree(path, prefix=prefix + extension)


def generate_tree(directory: Path, prefix: str = ""):
    """
    Belirtilen dizin için ağaç yapısını oluşturan ve yazdıran
    özyinelemeli (recursive) bir fonksiyon.
    """
    try:
        items = _sort_directory_contents(directory)
        filtered_items = _filter_items(items)
        _print_tree_level(filtered_items, prefix)

    except PermissionError:
        print(f"{prefix}└── [Erişim Engellendi]")
    except Exception as e:
        print(f"{prefix}└── [Hata: {e}]")


if __name__ == "__main__":
    print(f"📁 {START_PATH.resolve().name}")
    generate_tree(START_PATH)
