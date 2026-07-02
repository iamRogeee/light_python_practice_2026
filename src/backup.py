"""
Модуль для сравнения с резервной копией
Сравнение по размеру, дате и ХЭШУ (содержимому)
"""

from pathlib import Path
from scanner import scan_folder
from duplicates import calculate_hash, get_file_mtime
from utils import format_size


def scan_folder_with_hashes(folder_path):
    """
    Сканирование папки с вычислением хэшей для каждого файла
    """
    files_info, _ = scan_folder(folder_path)
    root_path = Path(folder_path)

    result = {}
    for info in files_info:
        file_path = info['path']
        rel_path = str(Path(file_path).relative_to(root_path))

        # Получаем хэш файла
        file_hash = calculate_hash(file_path)
        if file_hash is None:
            continue

        result[rel_path] = {
            'path': file_path,
            'size': info['size'],
            'modified': info['modified'],
            'hash': file_hash
        }

    return result


def compare_folders(source_path, backup_path):
    """
    Сравнение папок с использованием хэшей

    Сравнивает:
    1. Отсутствующие файлы (в бэкапе нет)
    2. Изменённые файлы (размер/дата/хэш не совпадают)
    3. Лишние файлы (в бэкапе есть, в исходной нет)
    4. Перемещённые файлы (одинаковое содержимое, другое имя/путь)
    """
    # Сканируем обе папки с хэшами
    source_data = scan_folder_with_hashes(source_path)
    backup_data = scan_folder_with_hashes(backup_path)

    result = {
        'missing': [],      # нет в бэкапе
        'changed': [],      # есть, но хэш отличается
        'extra': [],        # лишние в бэкапе
        'moved': []         # одинаковое содержимое, но разные пути
    }

    # --- 1. Сравниваем по относительным путям ---
    for rel_path, source_info in source_data.items():
        if rel_path not in backup_data:
            result['missing'].append(source_info)
        else:
            backup_info = backup_data[rel_path]

            # Сравниваем по хэшу (содержимому)
            if source_info['hash'] != backup_info['hash']:
                result['changed'].append({
                    'path': source_info['path'],
                    'size': source_info['size'],
                    'modified': source_info['modified'],
                    'hash': source_info['hash'],
                    'backup_path': backup_info['path'],
                    'backup_hash': backup_info['hash'],
                    'backup_size': backup_info['size'],
                    'backup_modified': backup_info['modified']
                })

    # --- 2. Проверяем лишние файлы в бэкапе ---
    for rel_path, backup_info in backup_data.items():
        if rel_path not in source_data:
            result['extra'].append(backup_info)

    # --- 3. Ищем перемещённые файлы (по хэшу) ---
    # Создаём словарь: хэш -> путь для исходной папки
    source_by_hash = {}
    for rel_path, info in source_data.items():
        file_hash = info['hash']
        if file_hash not in source_by_hash:
            source_by_hash[file_hash] = []
        source_by_hash[file_hash].append(rel_path)

    # Создаём словарь: хэш -> путь для бэкапа
    backup_by_hash = {}
    for rel_path, info in backup_data.items():
        file_hash = info['hash']
        if file_hash not in backup_by_hash:
            backup_by_hash[file_hash] = []
        backup_by_hash[file_hash].append(rel_path)

    # Находим файлы с одинаковыми хэшами, но разными путями
    for file_hash, source_paths in source_by_hash.items():
        if file_hash in backup_by_hash:
            backup_paths = backup_by_hash[file_hash]
            # Проверяем, есть ли совпадения по путям
            common_paths = set(source_paths) & set(backup_paths)
            # Если есть файлы с одинаковым содержимым, но разными путями
            if len(source_paths) != len(common_paths) or len(backup_paths) != len(common_paths):
                # Находим файлы, которые не совпадают по путям
                source_only = set(source_paths) - set(backup_paths)
                backup_only = set(backup_paths) - set(source_paths)

                if source_only and backup_only:
                    # Это перемещённые/переименованные файлы
                    for src_path in source_only:
                        src_info = source_data[src_path]
                        for bkp_path in backup_only:
                            bkp_info = backup_data[bkp_path]
                            result['moved'].append({
                                'source_path': src_info['path'],
                                'backup_path': bkp_info['path'],
                                'hash': file_hash,
                                'size': src_info['size']
                            })
                            break  # берём первое совпадение

    return result


def print_backup_comparison(result):
    """
    Вывод результатов сравнения в консоль
    """
    print("\n" + "=" * 80)
    print("📦 СРАВНЕНИЕ С РЕЗЕРВНОЙ КОПИЕЙ (по хэшам)")
    print("=" * 80)

    total = (len(result['missing']) + len(result['changed']) +
             len(result['extra']) + len(result['moved']))

    if total == 0:
        print("\n✅ Резервная копия актуальна. Различий нет!")
        return

    print(f"\n📊 Найдено различий: {total}")

    # --- Отсутствующие в бэкапе ---
    if result['missing']:
        print(f"\n❌ ОТСУТСТВУЮТ В БЭКАПЕ ({len(result['missing'])}):")
        for info in result['missing'][:10]:
            size_str = format_size(info['size'])
            print(f"  📄 {info['path']} ({size_str})")
        if len(result['missing']) > 10:
            print(f"  ... и еще {len(result['missing']) - 10}")

    # --- Изменённые (разные хэши) ---
    if result['changed']:
        print(f"\n🔄 ИЗМЕНЕНЫ (разное содержимое) ({len(result['changed'])}):")
        for info in result['changed'][:10]:
            size_str = format_size(info['size'])
            backup_size_str = format_size(info['backup_size'])
            print(f"  📄 {info['path']}")
            print(f"      Размер: {size_str} (было {backup_size_str})")
            print(f"      Хэш:   {info['hash'][:16]}... (был {info['backup_hash'][:16]}...)")
        if len(result['changed']) > 10:
            print(f"  ... и еще {len(result['changed']) - 10}")

    # --- Лишние в бэкапе ---
    if result['extra']:
        print(f"\n➕ ЛИШНИЕ В БЭКАПЕ ({len(result['extra'])}):")
        for info in result['extra'][:10]:
            size_str = format_size(info['size'])
            print(f"  📄 {info['path']} ({size_str})")
        if len(result['extra']) > 10:
            print(f"  ... и еще {len(result['extra']) - 10}")

    # --- Перемещённые файлы ---
    if result['moved']:
        print(f"\n🚚 ПЕРЕМЕЩЕНЫ/ПЕРЕИМЕНОВАНЫ (одинаковое содержимое) ({len(result['moved'])}):")
        for info in result['moved'][:10]:
            size_str = format_size(info['size'])
            print(f"  📄 {info['source_path']}")
            print(f"      → {info['backup_path']} ({size_str})")
        if len(result['moved']) > 10:
            print(f"  ... и еще {len(result['moved']) - 10}")