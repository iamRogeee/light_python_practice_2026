"""
Модуль для сканирования файловой системы
"""

from pathlib import Path
from utils import format_size, format_time


def scan_folder(folder_path):
    """
    Обход папки и сбор метаданных файлов

    Returns:
        tuple: (files_info, stats)
    """
    files_info = []
    root_path = Path(folder_path)

    total_files = 0
    total_folders = 0
    total_size = 0
    error_count = 0

    for item in root_path.rglob('*'):
        try:
            stat = item.stat()

            if item.is_file():
                total_files += 1
                total_size += stat.st_size
                files_info.append({
                    'path': str(item.absolute()),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            else:
                total_folders += 1

        except (OSError, PermissionError):
            error_count += 1
            continue

    stats = {
        'total_files': total_files,
        'total_folders': total_folders,
        'total_size': total_size,
        'error_count': error_count
    }

    return files_info, stats


def print_files_info(files_info, stats):
    """Вывод информации о файлах"""
    if not files_info:
        print("\n⚠️  Файлы не найдены")
        return

    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА СКАНИРОВАНИЯ")
    print("=" * 80)
    print(f"📁 Папок: {stats['total_folders']}")
    print(f"📄 Файлов: {stats['total_files']}")
    print(f"💾 Размер: {format_size(stats['total_size'])}")

    if stats.get('error_count', 0) > 0:
        print(f"⚠️  Ошибок доступа: {stats['error_count']}")

    print("\n" + "=" * 80)
    print("📋 СПИСОК ФАЙЛОВ")
    print("=" * 80)

    max_display = 20
    display_count = min(max_display, len(files_info))

    print(f"{'№':<4} {'Размер':<12} {'Изменен':<20} {'Путь':<50}")
    print("-" * 86)

    for i, info in enumerate(files_info[:display_count], 1):
        path_str = info['path']
        if len(path_str) > 50:
            path_str = "..." + path_str[-47:]
        print(f"{i:<4} {format_size(info['size']):<12} "
              f"{format_time(info['modified']):<20} "
              f"{path_str:<50}")

    if len(files_info) > max_display:
        print(f"\n... и еще {len(files_info) - max_display} файлов")