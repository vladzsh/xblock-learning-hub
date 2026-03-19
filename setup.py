"""
Установочный файл (setup.py) для vladx XBlock.

Этот файл определяет, как Python-пакет устанавливается в систему.
Ключевой элемент -- entry_points: именно через них платформа Open edX
(или XBlock Workbench) находит и загружает XBlock-плагины.

Группа 'xblock.v1' -- стандартная точка входа для XBlock-плагинов версии 1.
Формат: 'имя_блока = модуль:Класс'
"""

import os

from setuptools import setup


def package_data(pkg, roots):
    """
    Рекурсивный поиск файлов ресурсов в указанных директориях.

    Все файлы внутри каждой из директорий `roots` будут объявлены
    как данные пакета `pkg`. Это необходимо, чтобы статические файлы
    (HTML, CSS, JS, переводы) попали в установленный пакет.
    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))
    return {pkg: data}


setup(
    # Имя пакета на PyPI (или для pip install)
    name='vladx-xblock',

    # Версия пакета (семантическое версионирование: major.minor.patch)
    version='0.2',

    # Краткое описание пакета
    description='VladX Learning Hub -- обучающий XBlock, демонстрирующий все возможности XBlock API',

    # Лицензия (AGPL v3 -- стандарт для Open edX)
    license='AGPL v3',

    # Список Python-пакетов, входящих в дистрибутив
    packages=[
        'vladx',
    ],

    # Зависимости, которые pip установит автоматически
    install_requires=[
        'XBlock',
    ],

    # ========================================================================
    # ENTRY POINTS -- ТОЧКИ ВХОДА
    # ========================================================================
    # Это САМЫЙ ВАЖНЫЙ раздел для XBlock-разработчика.
    #
    # Группа 'xblock.v1' сообщает платформе: "этот пакет содержит XBlock".
    # Формат записи: 'тег_блока = python_модуль:PythonКласс'
    #
    # 'vladx' -- это тег, который используется в OLX (Open Learning XML):
    #   <vladx display_name="Мой блок" />
    #
    # 'vladx:VladXBlock' -- путь импорта: из пакета vladx импортировать VladXBlock
    #
    # Существует также группа 'xblock.v1.overrides' для переопределения
    # существующих блоков (добавлена в xblock 5.1.0).
    # ========================================================================
    entry_points={
        'xblock.v1': [
            'vladx = vladx:VladXBlock',
        ],
    },

    # Статические файлы, которые нужно включить в пакет
    # (HTML-шаблоны, CSS, JavaScript, файлы переводов)
    package_data=package_data("vladx", ["static", "public", "translations"]),
)
