import hashlib


def calculate_hash(file_path, chunk_size=8192):
    """
    Вычисление SHA-256 хэша файла
    """
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, PermissionError, IOError):
        return None


def find_duplicates(files_info):
    """
    Поиск дубликатов по содержимому
    """
    hash_map = {}

    for file_info in files_info:
        file_path = file_info['path']
        file_hash = calculate_hash(file_path)

        if file_hash is None:
            continue

        if file_hash not in hash_map:
            hash_map[file_hash] = []
        hash_map[file_hash].append(file_path)

    # Оставляем только группы с >= 2 файлами
    return {h: paths for h, paths in hash_map.items() if len(paths) >= 2}


def print_duplicates(duplicates):
    """Вывод дубликатов"""
    if not duplicates:
        print("\n✅ Дубликаты не найдены")
        return

    total_files = sum(len(paths) for paths in duplicates.values())

    print("\n" + "=" * 80)
    print("🔍 НАЙДЕНЫ ДУБЛИКАТЫ")
    print("=" * 80)
    print(f"Групп: {len(duplicates)}")
    print(f"Всего файлов-дубликатов: {total_files}")
    print("-" * 80)

    for i, (file_hash, paths) in enumerate(duplicates.items(), 1):
        print(f"\nГруппа {i} (хэш: {file_hash[:16]}...):")
        for path in paths:
            print(f"  📄 {path}")