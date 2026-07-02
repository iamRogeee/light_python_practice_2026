"""
Модуль для сканирования файловой системы с РУЧНЫМ рекурсивным обходом
БЕЗ использования os.walk, rglob, scandir и других автоматических обходчиков
"""

import os
from pathlib import Path
from utils import format_size, format_time


# ===== НАСТРОЙКИ ФИЛЬТРАЦИИ =====

# Папки, которые нужно пропускать
IGNORED_FOLDERS = {
    'System Volume Information',
    '$Recycle.Bin',
    'Windows',
    'Program Files',
    'Program Files (x86)',
    'node_modules',
    '.git',
    '.venv',
    '__pycache__',
    'venv',
    '.idea',
    '.vscode',
    'AppData'
}

# Расширения, которые нужно пропускать
IGNORED_EXTENSIONS = {
    '.tmp', '.temp', '.log', '.cache', '.pyc',
    '.pyo', '.so', '.dll', '.exe',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.msi', '.cab', '.iso'
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 МБ


def should_ignore_path(path, root_path):
    """Проверка, нужно ли игнорировать файл/папку"""
    try:
        rel_path = path.relative_to(root_path)

        for part in rel_path.parts:
            if part in IGNORED_FOLDERS:
                return True
            if part.startswith('.') and len(part) > 1:
                return True

        if path.suffix.lower() in IGNORED_EXTENSIONS:
            return True

        if path.name.startswith('.') and len(path.name) > 1:
            return True

    except ValueError:
        pass

    return False


# ФИЛЬТРАЦИЯ

def manual_extension_filter(filepath, extensions):
    """Фильтрация по расширениям"""
    if not extensions:
        return True

    _, ext = os.path.splitext(filepath)
    ext = ext.lower().lstrip('.')
    return ext in extensions


def manual_pattern_filter(filepath, pattern):
    """фильтрация по шаблону"""
    if not pattern:
        return True

    filename = os.path.basename(filepath)

    # Проверка шаблона с *
    parts = pattern.split('*')

    if len(parts) == 1:
        return filename == pattern

    if parts[0] and not filename.startswith(parts[0]):
        return False

    if parts[-1] and not filename.endswith(parts[-1]):
        return False

    pos = len(parts[0])
    for part in parts[1:-1]:
        if part:
            pos = filename.find(part, pos)
            if pos == -1:
                return False
            pos += len(part)

    return True


# РУЧНОЙ РЕКУРСИВНЫЙ ОБХОД

def scan_recursive(directory, root_directory=None, verbose=False, _depth=0):
    """
    РУЧНОЙ РЕКУРСИВНЫЙ ОБХОД.

    Функция обходит папку:
    """
    if root_directory is None:
        root_directory = directory

    result = []

    # ШАГ 1: Получение списка файлов и папок
    try:
        entries = os.listdir(directory)
    except PermissionError:
        if verbose:
            print("  " * _depth + f"[ЗАКРЫТ] {directory}")
        return result

    if verbose:
        print("  " * _depth + f"[ПАПКА] {directory}")

    # ШАГ 2: Обход каждого элемента
    for entry in entries:
        full_path = os.path.join(directory, entry)

        # ШАГ 3: Проверка: это папка или файл
        if os.path.isdir(full_path):
            # ШАГ 4: РУЧНАЯ РЕКУРСИЯ
            sub_result = scan_recursive(full_path, root_directory, verbose, _depth + 1)
            result.extend(sub_result)
        else:
            # ШАГ 5: Обработка файла
            try:
                stat = os.stat(full_path)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                size = 0
                mtime = 0

            rel_path = os.path.relpath(full_path, root_directory)

            if verbose:
                print("  " * (_depth + 1) + f"  [ФАЙЛ] {entry} ({size} байт)")

            result.append({
                'path': full_path,
                'rel_path': rel_path,
                'filename': entry,
                'size': size,
                'modified': mtime
            })

    return result


# ОСНОВНАЯ ФУНКЦИЯ

def scan_folder(folder_path, filter_enabled=True, ext_filters=None, name_filter=None, verbose=False):
    """
    Сканирование папки с ручной рекурсией и фильтрацией.
    """
    root_path = Path(folder_path)

    # ЗАПУСК РУЧНОЙ РЕКУРСИИ
    all_files = scan_recursive(folder_path, verbose=verbose)

    files_info = []
    total_files = 0
    total_folders = 0
    total_size = 0
    filtered_count = 0
    error_count = 0
    skipped_large = 0
    rejected_by_ext = 0
    rejected_by_name = 0

    # ФИЛЬТРАЦИЯ КАЖДОГО ФАЙЛА
    for item in all_files:
        try:
            # 1. Системная фильтрация
            if filter_enabled and should_ignore_path(Path(item['path']), root_path):
                filtered_count += 1
                continue

            # 2. Фильтрация по расширениям
            if ext_filters and not manual_extension_filter(item['rel_path'], ext_filters):
                rejected_by_ext += 1
                continue

            # 3. Фильтрация по шаблону
            if name_filter and not manual_pattern_filter(item['rel_path'], name_filter):
                rejected_by_name += 1
                continue

            # 4. Проверка размера
            if item['size'] > MAX_FILE_SIZE:
                skipped_large += 1
                continue

            total_files += 1
            total_size += item['size']
            files_info.append({
                'path': item['path'],
                'size': item['size'],
                'modified': item['modified']
            })

        except (OSError, PermissionError):
            error_count += 1
            continue

    stats = {
        'total_files': total_files,
        'total_folders': total_folders,
        'total_size': total_size,
        'filtered_count': filtered_count,
        'error_count': error_count,
        'skipped_large': skipped_large,
        'rejected_by_ext': rejected_by_ext,
        'rejected_by_name': rejected_by_name
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

    if stats.get('filtered_count', 0) > 0:
        print(f"🚫 Исключено по системному фильтру: {stats['filtered_count']}")
    if stats.get('rejected_by_ext', 0) > 0:
        print(f"🚫 Отсеяно по расширению: {stats['rejected_by_ext']}")
    if stats.get('rejected_by_name', 0) > 0:
        print(f"🚫 Отсеяно по шаблону имени: {stats['rejected_by_name']}")
    if stats.get('skipped_large', 0) > 0:
        print(f"📏 Пропущено больших файлов: {stats['skipped_large']}")
    if stats.get('error_count', 0) > 0:
        print(f"⚠️  Ошибок доступа: {stats['error_count']}")

    print("\n" + "=" * 80)
    print("📋 СПИСОК ФАЙЛОВ (первые 20)")
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