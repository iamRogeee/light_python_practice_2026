"""
Модуль для сравнения с резервной копией
"""

from pathlib import Path
from scanner import scan_folder


def compare_folders(source_path, backup_path):
    """
    Сравнение папки с резервной копией
     'missing': [],   # отсутствуют в бэкапе
     'changed': [],   # изменены
     'extra': []      # лишние в бэкапе
    """
    source_files, _ = scan_folder(source_path)
    backup_files, _ = scan_folder(backup_path)

    source_root = Path(source_path)
    backup_root = Path(backup_path)

    # Относительные пути
    source_rel = {
        str(Path(info['path']).relative_to(source_root)): info
        for info in source_files
    }

    backup_rel = {
        str(Path(info['path']).relative_to(backup_root)): info
        for info in backup_files
    }

    result = {
        'missing': [],
        'changed': [],
        'extra': []
    }

    # Проверяем файлы из исходной папки
    for rel_path, source_info in source_rel.items():
        if rel_path not in backup_rel:
            result['missing'].append(source_info)
        else:
            backup_info = backup_rel[rel_path]
            if (source_info['size'] != backup_info['size'] or
                    source_info['modified'] != backup_info['modified']):
                result['changed'].append({
                    'path': source_info['path'],
                    'size': source_info['size'],
                    'modified': source_info['modified'],
                    'backup_size': backup_info['size'],
                    'backup_modified': backup_info['modified']
                })

    # Проверяем лишние файлы в бэкапе
    for rel_path, backup_info in backup_rel.items():
        if rel_path not in source_rel:
            result['extra'].append(backup_info)

    return result


def print_backup_comparison(result):
    """Вывод результатов сравнения"""
    print("\n" + "=" * 80)
    print("📦 СРАВНЕНИЕ С РЕЗЕРВНОЙ КОПИЕЙ")
    print("=" * 80)

    total = len(result['missing']) + len(result['changed']) + len(result['extra'])

    if total == 0:
        print("\n✅ Резервная копия актуальна. Различий нет!")
        return

    print(f"\nНайдено различий: {total}")

    if result['missing']:
        print(f"\n❌ ОТСУТСТВУЮТ В БЭКАПЕ ({len(result['missing'])}):")
        for info in result['missing'][:10]:
            print(f"  📄 {info['path']}")
        if len(result['missing']) > 10:
            print(f"  ... и еще {len(result['missing']) - 10}")

    if result['changed']:
        print(f"\n🔄 ИЗМЕНЕНЫ ({len(result['changed'])}):")
        for info in result['changed'][:10]:
            print(f"  📄 {info['path']}")
        if len(result['changed']) > 10:
            print(f"  ... и еще {len(result['changed']) - 10}")

    if result['extra']:
        print(f"\n➕ ЛИШНИЕ В БЭКАПЕ ({len(result['extra'])}):")
        for info in result['extra'][:10]:
            print(f"  📄 {info['path']}")
        if len(result['extra']) > 10:
            print(f"  ... и еще {len(result['extra']) - 10}")