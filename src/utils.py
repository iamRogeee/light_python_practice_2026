"""
Вспомогательные функции для работы с файлами
"""

from datetime import datetime


def format_size(size_bytes):
    """Форматирование размера файла в человекочитаемый вид"""
    if size_bytes is None:
        return "Неизвестно"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_time(timestamp):
    """Форматирование времени изменения"""
    if timestamp is None:
        return "Неизвестно"
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")