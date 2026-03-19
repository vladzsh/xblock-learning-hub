"""
Установочний файл (setup.py) для vladx XBlock.

Цей файл визначає, як Python-пакет встановлюється в систему.
Ключовий елемент -- entry_points: саме через них платформа Open edX
(або XBlock Workbench) знаходить та завантажує XBlock-плагіни.

Група 'xblock.v1' -- стандартна точка входу для XBlock-плагінів версії 1.
Формат: 'ім'я_блоку = модуль:Клас'
"""

import os

from setuptools import setup


def package_data(pkg, roots):
    """
    Рекурсивний пошук файлів ресурсів у вказаних директоріях.

    Усі файли всередині кожної з директорій `roots` будуть оголошені
    як дані пакета `pkg`. Це необхідно, щоб статичні файли
    (HTML, CSS, JS, переклади) потрапили до встановленого пакета.
    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))
    return {pkg: data}


setup(
    # Ім'я пакета на PyPI (або для pip install)
    name='vladx-xblock',

    # Версія пакета (семантичне версіонування: major.minor.patch)
    version='0.2',

    # Короткий опис пакета
    description='VladX Learning Hub -- навчальний XBlock, що демонструє всі можливості XBlock API',

    # Ліцензія (AGPL v3 -- стандарт для Open edX)
    license='AGPL v3',

    # Список Python-пакетів, що входять до дистрибутиву
    packages=[
        'vladx',
    ],

    # Залежності, які pip встановить автоматично
    install_requires=[
        'XBlock',
    ],

    # ========================================================================
    # ENTRY POINTS -- ТОЧКИ ВХОДУ
    # ========================================================================
    # Це НАЙВАЖЛИВІШИЙ розділ для XBlock-розробника.
    #
    # Група 'xblock.v1' повідомляє платформі: "цей пакет містить XBlock".
    # Формат запису: 'тег_блоку = python_модуль:PythonКлас'
    #
    # 'vladx' -- це тег, який використовується в OLX (Open Learning XML):
    #   <vladx display_name="Мій блок" />
    #
    # 'vladx:VladXBlock' -- шлях імпорту: з пакета vladx імпортувати VladXBlock
    #
    # Існує також група 'xblock.v1.overrides' для перевизначення
    # існуючих блоків (додана в xblock 5.1.0).
    # ========================================================================
    entry_points={
        'xblock.v1': [
            'vladx = vladx:VladXBlock',
        ],
    },

    # Статичні файли, які потрібно включити до пакета
    # (HTML-шаблони, CSS, JavaScript, файли перекладів)
    package_data=package_data("vladx", ["static", "public", "translations"]),
)
