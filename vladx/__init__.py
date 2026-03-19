"""
Модуль ініціалізації пакета vladx.

Файл __init__.py робить директорію vladx/ Python-пакетом.
Імпорт VladXBlock тут дозволяє використовувати короткий шлях:
    from vladx import VladXBlock
замість:
    from vladx.vladx import VladXBlock

Це також необхідно для entry_points у setup.py:
    'vladx = vladx:VladXBlock'
             ^^^^^  ^^^^^^^^^
             пакет  клас (шукається в __init__.py)
"""
from .vladx import VladXBlock
