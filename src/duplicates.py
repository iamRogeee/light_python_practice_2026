"""
Модуль для поиска дубликатов с кешированием хэшей
"""

import hashlib
import json
import os
from datetime import datetime

# Файл для кеша хэшей
CACHE_FILE = "hash_cache.json"


def load_hash_cache():
    """
    Загрузка кеша хэшей из файла
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_hash_cache(cache):
    """
    Сохранение кеша хэшей в файл
    """
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


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


def get_file_mtime(file_path):
    """
    Получение даты изменения файла
    """
    try:
        return os.path.getmtime(file_path)
    except OSError:
        return None


def find_duplicates(files_info, use_cache=True):
    """
    Поиск дубликатов с использованием кеша хэшей
    """
    # Загружаем кеш
    cache = load_hash_cache() if use_cache else {}
    hash_map = {}
    cache_hits = 0
    cache_misses = 0

    # Сначала собираем информацию о файлах
    files_data = {}
    for info in files_info:
        path = info['path']
        mtime = get_file_mtime(path)
        files_data[path] = {
            'mtime': mtime,
            'size': info['size']
        }

    # Обрабатываем каждый файл
    for file_info in files_info:
        file_path = file_info['path']
        file_hash = None

        # Проверяем кеш
        if use_cache and file_path in cache:
            cached_data = cache[file_path]
            # Проверяем, не изменился ли файл
            if isinstance(cached_data, dict):
                cached_hash = cached_data.get('hash')
                cached_mtime = cached_data.get('mtime')
                current_mtime = files_data[file_path]['mtime']

                # Если дата изменения совпадает — используем кеш
                if cached_mtime == current_mtime and cached_hash:
                    file_hash = cached_hash
                    cache_hits += 1
            else:
                # Старый формат кеша (только хэш)
                file_hash = cached_data
                cache_hits += 1

        # Если в кеше нет — вычисляем
        if file_hash is None:
            file_hash = calculate_hash(file_path)
            cache_misses += 1

            # Сохраняем в кеш
            if use_cache and file_hash is not None:
                cache[file_path] = {
                    'hash': file_hash,
                    'mtime': files_data[file_path]['mtime']
                }

        if file_hash is None:
            continue

        # Группируем по хэшу
        if file_hash not in hash_map:
            hash_map[file_hash] = []
        hash_map[file_hash].append(file_path)

    # Сохраняем кеш
    if use_cache:
        save_hash_cache(cache)

    # Выводим статистику кеша
    total = cache_hits + cache_misses
    if total > 0:
        print(f"\n📊 Кеш хэшей: {cache_hits} загружено, {cache_misses} вычислено")

    # Оставляем только дубликаты (>= 2 файлов)
    return {h: paths for h, paths in hash_map.items() if len(paths) >= 2}


def print_duplicates(duplicates):
    """
    Вывод дубликатов в консоль
    """
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
        for path in paths[:10]:  # Показываем первые 10 файлов группы
            print(f"  📄 {path}")
        if len(paths) > 10:
            print(f"  ... и еще {len(paths) - 10} файлов")