"""
Модуль инициализации пакета vladx.

Файл __init__.py делает директорию vladx/ Python-пакетом.
Импорт VladXBlock здесь позволяет использовать короткий путь:
    from vladx import VladXBlock
вместо:
    from vladx.vladx import VladXBlock

Это также необходимо для entry_points в setup.py:
    'vladx = vladx:VladXBlock'
             ^^^^^  ^^^^^^^^^
             пакет  класс (ищется в __init__.py)
"""
from .vladx import VladXBlock
