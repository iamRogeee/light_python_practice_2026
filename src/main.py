#!/usr/bin/env python3
"""
Консольный индексатор папок с фильтрацией и кешированием
"""

import sys
import os

from scanner import scan_folder, print_files_info
from duplicates import find_duplicates, print_duplicates
from backup import compare_folders, print_backup_comparison


if len(sys.argv) == 1:
    sys.argv = [
        'main.py',
        'C:/Users/Егор/Documents',
        '--backup',
        'D:/backup'
    ]

def print_usage():
    """Вывод справки"""
    print("=" * 80)
    print("🔍 КОНСОЛЬНЫЙ ИНДЕКСАТОР ПАПОК (упрощенная версия)")
    print("=" * 80)
    print("\n📖 Использование:")
    print("  python main.py <путь_к_папке> [--backup <путь_к_бэкапу>]")
    print("  python main.py <путь_к_папке> --no-filter")
    print("  python main.py <путь_к_папке> --no-cache")
    print("\n📌 Примеры:")
    print("  python main.py C:/Users/Егор/Documents")
    print("  python main.py C:/Users/Егор/Documents --backup D:/Backup")
    print("  python main.py C:/Users/Егор/Documents --no-filter --no-cache")
    print("\n⚙️  Опции:")
    print("  --backup     Путь к папке с резервной копией")
    print("  --no-filter  Отключить фильтрацию")
    print("  --no-cache   Не использовать кеш хэшей")
    print("=" * 80)


def parse_args():
    """Разбор аргументов командной строки"""
    folder_path = None
    backup_path = None
    filter_enabled = True
    cache_enabled = True

    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--backup' and i + 1 < len(sys.argv[1:]):
            backup_path = sys.argv[i + 2]
        elif arg == '--no-filter':
            filter_enabled = False
        elif arg == '--no-cache':
            cache_enabled = False
        elif not arg.startswith('--') and folder_path is None:
            folder_path = arg

    return folder_path, backup_path, filter_enabled, cache_enabled


def main():
    """Точка входа"""
    folder_path, backup_path, filter_enabled, cache_enabled = parse_args()

    if folder_path is None:
        print_usage()
        sys.exit(1)

    if not os.path.exists(folder_path):
        print(f"❌ Ошибка: Папка '{folder_path}' не существует")
        sys.exit(1)

    if not os.path.isdir(folder_path):
        print(f"❌ Ошибка: '{folder_path}' не является папкой")
        sys.exit(1)

    print(f"\n🔍 СКАНИРОВАНИЕ ПАПКИ: {folder_path}")
    print("=" * 80)
    print(f"🔧 Фильтрация: {'ВКЛЮЧЕНА' if filter_enabled else 'ОТКЛЮЧЕНА'}")
    print(f"💾 Кеш хэшей: {'ВКЛЮЧЕН' if cache_enabled else 'ОТКЛЮЧЕН'}")
    print("=" * 80)

    # 1. Сканирование
    files_info, stats = scan_folder(folder_path, filter_enabled)
    print_files_info(files_info, stats)

    # 2. Дубликаты
    duplicates = find_duplicates(files_info, use_cache=cache_enabled)
    print_duplicates(duplicates)

    # 3. Сравнение с бэкапом
    if backup_path:
        if not os.path.exists(backup_path):
            print(f"\n⚠️  Предупреждение: Папка бэкапа '{backup_path}' не существует")
        elif not os.path.isdir(backup_path):
            print(f"\n⚠️  Предупреждение: '{backup_path}' не является папкой")
        else:
            result = compare_folders(folder_path, backup_path)
            print_backup_comparison(result)

    print("\n" + "=" * 80)
    print("✅ РАБОТА ЗАВЕРШЕНА УСПЕШНО")
    print("=" * 80)


if __name__ == "__main__":
    main()