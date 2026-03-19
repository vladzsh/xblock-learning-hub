"""
VladX Learning Hub -- обучающий XBlock, демонстрирующий ВСЕ возможности XBlock API.

XBlock -- это компонентная архитектура для образовательных платформ Open edX.
Каждый XBlock -- это мини-веб-приложение: у него есть хранилище данных (поля),
представления (views), обработчики AJAX-запросов (handlers), и он может
содержать дочерние блоки (children).

Этот файл демонстрирует:
  1. Все типы полей (String, Integer, Boolean, Float, List, Dict, DateTime, Any)
  2. Все области видимости (Scope.content, settings, user_state, user_state_summary,
     preferences, user_info)
  3. Представления (student_view, studio_view, author_view, fallback_view)
  4. Обработчики (@XBlock.json_handler, @XBlock.handler)
  5. Fragment API (HTML + CSS + JS)
  6. Дочерние блоки (has_children)
  7. Сервисы (@XBlock.needs, @XBlock.wants)
  8. Оценивание (has_score, runtime.publish grade)
  9. Валидация (validate)
  10. Сериализация XML/OLX (parse_xml, add_xml_to_node)
  11. Поисковая индексация (index_dictionary)
  12. Интеграция с edX (icon_class, workbench_scenarios)
"""

# ============================================================================
# ИМПОРТЫ
# ============================================================================
# json -- для работы с JSON в сыром обработчике (raw handler)
import json
# logging -- стандартное логирование Python
import logging
# datetime -- для работы с полем DateTime
from datetime import datetime

# webob.Response -- объект HTTP-ответа, требуется для @XBlock.handler (raw handler)
from webob import Response

# Fragment -- объект, содержащий HTML + CSS + JS для отрисовки блока на странице.
# Каждое представление (view) возвращает Fragment.
# Начиная с xblock 4.0, Fragment -- это pass-through к web_fragments.fragment.
from web_fragments.fragment import Fragment

# importlib.resources -- современный способ загрузки файлов из пакета (с xblock 5.0+).
# Заменяет устаревший pkg_resources.resource_string().
from importlib.resources import files

# XBlock -- базовый класс для всех XBlock-ов.
# Наследование от XBlock даёт доступ к полям, представлениям, обработчикам,
# сервисам и системе плагинов.
from xblock.core import XBlock

# Поля (Fields) -- хранят состояние блока.
# Каждое поле имеет тип данных и область видимости (Scope).
from xblock.fields import (
    String,     # Строковое поле
    Integer,    # Целое число
    Boolean,    # Логическое значение (True/False)
    Float,      # Число с плавающей точкой
    List,       # Список (Python list, хранится как JSON array)
    Dict,       # Словарь (Python dict, хранится как JSON object)
    DateTime,   # Дата и время (ISO-формат строки)
    Any,        # Произвольный тип (любой JSON-сериализуемый объект)
    Scope,      # Области видимости полей
)

# Логгер для этого модуля.
# Используйте log.info(), log.warning(), log.error() для отладки.
log = logging.getLogger(__name__)


# ============================================================================
# ДЕКОРАТОРЫ СЕРВИСОВ (на уровне класса)
# ============================================================================
# @XBlock.needs('service_name') -- ОБЯЗАТЕЛЬНЫЙ сервис. Если runtime не предоставит
#     этот сервис, при обращении к нему будет выброшено исключение NoSuchServiceError.
#
# @XBlock.wants('service_name') -- НЕОБЯЗАТЕЛЬНЫЙ сервис. Если runtime его не предоставит,
#     self.runtime.service(self, 'service_name') вернёт None, и код не упадёт.
#
# Доступ к сервису: self.runtime.service(self, 'имя_сервиса')
#
# Стандартные сервисы:
#   'i18n'     -- интернационализация (gettext, переводы)
#   'settings' -- серверные настройки для типа блока
#   'user'     -- информация о текущем пользователе
#   'fs'       -- файловая система (django-pyfs) для хранения файлов
# ============================================================================
@XBlock.needs('i18n')       # Сервис интернационализации -- обязателен
@XBlock.wants('settings')   # Сервис серверных настроек -- необязателен
@XBlock.wants('user')       # Сервис пользователя -- необязателен
class VladXBlock(XBlock):
    """
    VladX Learning Hub -- обучающий XBlock.

    Функциональность:
    - Преподаватель задаёт вопрос и правильный ответ через Studio
    - Студент вводит ответ, получает оценку
    - Студент может голосовать (thumbs up/down) за вопрос
    - Переключение компактного/полного режима отображения
    - Поддержка дочерних блоков

    ВАЖНО: Не переопределяйте __init__() в XBlock-ах!
    XBlock-и создаются runtime-ом, и __init__ может вызываться
    в разных контекстах. Используйте поля с default-значениями.
    """

    # ========================================================================
    # АТРИБУТЫ КЛАССА
    # ========================================================================

    # has_children = True разрешает этому блоку содержать дочерние блоки.
    # Дочерние блоки определяются в OLX:
    #   <vladx>
    #       <html_demo><p>Дочерний контент</p></html_demo>
    #   </vladx>
    # Доступ: self.children (список usage_id дочерних блоков)
    has_children = True

    # has_score = True сообщает платформе, что этот блок выставляет оценки.
    # Для выставления оценки нужно вызвать:
    #   self.runtime.publish(self, 'grade', {'value': X, 'max_value': Y})
    has_score = True

    # icon_class определяет иконку блока в LMS на навигационной панели.
    # Допустимые значения: 'problem' (задача), 'video' (видео), 'other' (другое)
    icon_class = 'problem'

    # ========================================================================
    # ПОЛЯ (FIELDS) -- ХРАНИЛИЩЕ СОСТОЯНИЯ БЛОКА
    # ========================================================================
    #
    # Каждое поле -- это дескриптор Python, объявленный на уровне класса.
    # При обращении через self.field_name, runtime автоматически загружает
    # и сохраняет значение в хранилище (БД, файл и т.д.).
    #
    # Параметры поля:
    #   help         -- описание поля (для документации и UI Studio)
    #   display_name -- отображаемое имя в интерфейсе Studio
    #   default      -- значение по умолчанию
    #   scope        -- область видимости (кто видит эти данные)
    #   values       -- допустимые значения (для валидации в UI)
    #   enforce_type -- принудительная проверка типа при записи
    #   xml_node     -- сериализовать как дочерний XML-узел (а не атрибут)
    #   force_export -- экспортировать в XML, даже если значение по умолчанию
    #
    # ОБЛАСТИ ВИДИМОСТИ (Scope) определяют, КТО видит данные и К ЧЕМУ они привязаны:
    #
    # Scope = UserScope + BlockScope
    #
    # UserScope (кто видит):
    #   NONE -- данные не привязаны к пользователю (все видят одно и то же)
    #   ONE  -- данные привязаны к конкретному пользователю
    #   ALL  -- данные агрегированы по всем пользователям
    #
    # BlockScope (к чему привязаны):
    #   DEFINITION -- к определению блока (может использоваться в нескольких местах)
    #   USAGE      -- к конкретному использованию блока в курсе
    #   TYPE       -- ко всем блокам данного типа (Python-класса)
    #   ALL        -- ко всем блокам всех типов
    # ========================================================================

    # ========================================================================
    # ПОЛЯ Scope.content  (BlockScope.DEFINITION + UserScope.NONE)
    # ========================================================================
    # Данные, общие для всех студентов, привязанные к ОПРЕДЕЛЕНИЮ блока.
    # Одно определение может использоваться в нескольких курсах.
    # Типичное использование: текст вопроса, правильный ответ, контент.
    # В OLX эти поля сериализуются как атрибуты XML-тега.
    # ========================================================================

    question_text = String(
        display_name="Текст вопроса",
        help=(
            "Вопрос, который видят все студенты. "
            "Scope.content = BlockScope.DEFINITION + UserScope.NONE -- "
            "данные общие для всех пользователей и привязаны к определению блока. "
            "Если один и тот же блок используется в нескольких курсах, "
            "все они будут видеть один и тот же текст вопроса."
        ),
        default="Какой метод XBlock вызывается для отображения студенческого представления?",
        scope=Scope.content,
    )

    correct_answer = String(
        display_name="Правильный ответ",
        help=(
            "Правильный ответ на вопрос. "
            "Scope.content -- общий для всех, привязан к определению блока."
        ),
        default="student_view",
        scope=Scope.content,
    )

    explanation = String(
        display_name="Пояснение",
        help=(
            "Текст пояснения, показываемый после правильного ответа. "
            "Scope.content -- общий для всех."
        ),
        default=(
            "Метод student_view() -- это основное представление XBlock, "
            "которое вызывается LMS для показа блока студентам. "
            "Он обязан возвращать объект Fragment с HTML, CSS и JavaScript."
        ),
        scope=Scope.content,
        # xml_node=True означает, что при сериализации в OLX это поле
        # будет дочерним XML-узлом, а не атрибутом:
        #   <vladx><explanation>текст</explanation></vladx>
        # а не <vladx explanation="текст" />
        xml_node=True,
    )

    # ========================================================================
    # ПОЛЯ Scope.settings  (BlockScope.USAGE + UserScope.NONE)
    # ========================================================================
    # Данные, общие для всех студентов, привязанные к ИСПОЛЬЗОВАНИЮ блока.
    # Каждое использование блока в курсе может иметь свои настройки.
    # Типичное использование: название, максимум попыток, вес оценки, дедлайн.
    # ========================================================================

    display_name = String(
        display_name="Название компонента",
        help=(
            "Название, отображаемое в заголовке блока и в навигации курса. "
            "Scope.settings = BlockScope.USAGE + UserScope.NONE -- "
            "данные общие для всех пользователей, но привязаны к конкретному "
            "использованию блока (каждый экземпляр в курсе может иметь своё название)."
        ),
        default="VladX Learning Hub",
        scope=Scope.settings,
    )

    max_attempts = Integer(
        display_name="Максимум попыток",
        help=(
            "Сколько раз студент может отправить ответ. "
            "Тип Integer хранит целые числа. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default=3,
        scope=Scope.settings,
    )

    weight = Float(
        display_name="Вес задания",
        help=(
            "Вес задания в итоговой оценке (максимальный балл). "
            "Тип Float хранит числа с плавающей точкой. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default=1.0,
        scope=Scope.settings,
    )

    due_date = DateTime(
        display_name="Срок сдачи",
        help=(
            "Дата и время, до которых нужно отправить ответ. "
            "Тип DateTime хранит дату в ISO-формате (например, '2025-12-31T23:59:59'). "
            "Значение None означает, что срок не установлен. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default=None,
        scope=Scope.settings,
    )

    hints = List(
        display_name="Подсказки",
        help=(
            "Список текстовых подсказок для студента. "
            "Тип List хранит Python-список, сериализуемый в JSON-массив. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default=["Это название метода Python", "Начинается на 'student_'"],
        scope=Scope.settings,
    )

    options = Dict(
        display_name="Дополнительные параметры",
        help=(
            "Словарь дополнительных параметров конфигурации. "
            "Тип Dict хранит Python-словарь, сериализуемый в JSON-объект. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default={"show_explanation": True, "shuffle_hints": False},
        scope=Scope.settings,
    )

    allow_reset = Boolean(
        display_name="Разрешить сброс",
        help=(
            "Может ли студент сбросить свой ответ и начать заново. "
            "Тип Boolean хранит True/False. "
            "Scope.settings -- настройка конкретного использования блока."
        ),
        default=True,
        scope=Scope.settings,
    )

    # ========================================================================
    # ПОЛЯ Scope.user_state  (BlockScope.USAGE + UserScope.ONE)
    # ========================================================================
    # Данные конкретного студента для конкретного использования блока.
    # У каждого студента -- свои значения этих полей.
    # Типичное использование: ответ студента, количество попыток, полученный балл.
    # ========================================================================

    student_answer = String(
        help=(
            "Ответ, введённый студентом. "
            "Scope.user_state = BlockScope.USAGE + UserScope.ONE -- "
            "данные привязаны к конкретному студенту И конкретному использованию блока. "
            "Каждый студент видит только свой ответ."
        ),
        default="",
        scope=Scope.user_state,
    )

    attempts_used = Integer(
        help=(
            "Сколько попыток студент уже использовал. "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=0,
        scope=Scope.user_state,
    )

    is_submitted = Boolean(
        help=(
            "Отправлен ли ответ (хотя бы раз). "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=False,
        scope=Scope.user_state,
    )

    score_earned = Float(
        help=(
            "Баллы, полученные студентом за это задание. "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=0.0,
        scope=Scope.user_state,
    )

    student_data = Any(
        help=(
            "Произвольные данные студента. "
            "Тип Any может хранить ЛЮБОЙ JSON-сериализуемый Python-объект: "
            "dict, list, str, int, None и их комбинации. "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=None,
        scope=Scope.user_state,
    )

    voted = Boolean(
        help=(
            "Голосовал ли этот студент за/против вопроса. "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=False,
        scope=Scope.user_state,
    )

    hint_index = Integer(
        help=(
            "Индекс последней показанной подсказки для этого студента. "
            "Scope.user_state -- индивидуально для каждого студента."
        ),
        default=0,
        scope=Scope.user_state,
    )

    # ========================================================================
    # ПОЛЯ Scope.user_state_summary  (BlockScope.USAGE + UserScope.ALL)
    # ========================================================================
    # Данные, агрегированные по ВСЕМ студентам для конкретного использования блока.
    # Все студенты видят одни и те же значения, и каждый может их изменять.
    # Типичное использование: общий счётчик ответов, голоса, гистограммы.
    # ВНИМАНИЕ: при конкурентной записи возможны гонки (race conditions).
    # ========================================================================

    total_submissions = Integer(
        help=(
            "Общее количество отправок ответов всеми студентами. "
            "Scope.user_state_summary = BlockScope.USAGE + UserScope.ALL -- "
            "агрегированные данные, видимые всем и изменяемые всеми."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    upvotes = Integer(
        help=(
            "Общее количество голосов 'за' от всех студентов. "
            "Scope.user_state_summary -- агрегированные данные."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    downvotes = Integer(
        help=(
            "Общее количество голосов 'против' от всех студентов. "
            "Scope.user_state_summary -- агрегированные данные."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    # ========================================================================
    # ПОЛЯ Scope.preferences  (BlockScope.TYPE + UserScope.ONE)
    # ========================================================================
    # Предпочтения конкретного студента для ВСЕХ блоков данного типа (VladXBlock).
    # Если студент переключит режим отображения в одном VladXBlock,
    # это значение будет общим для ВСЕХ VladXBlock-ов этого студента.
    # Типичное использование: скорость видеоплеера, язык субтитров, тема оформления.
    # ========================================================================

    display_mode = String(
        help=(
            "Предпочитаемый режим отображения: 'full' (полный) или 'compact' (компактный). "
            "Scope.preferences = BlockScope.TYPE + UserScope.ONE -- "
            "данные привязаны к конкретному студенту, но применяются ко ВСЕМ блокам "
            "типа VladXBlock на всей платформе."
        ),
        default="full",
        scope=Scope.preferences,
        values=["compact", "full"],
    )

    # ========================================================================
    # ПОЛЯ Scope.user_info  (BlockScope.ALL + UserScope.ONE)
    # ========================================================================
    # Информация о конкретном студенте, глобальная для ВСЕХ блоков ВСЕХ типов.
    # Типичное использование: часовой пояс пользователя, язык интерфейса.
    # ВНИМАНИЕ: разные типы блоков делят одно пространство имён полей --
    # два поля с одинаковым именем в разных блоках будут ссылаться на одни данные!
    # ========================================================================

    user_language = String(
        help=(
            "Предпочитаемый язык пользователя. "
            "Scope.user_info = BlockScope.ALL + UserScope.ONE -- "
            "данные привязаны к конкретному студенту, но глобальны для ВСЕХ блоков. "
            "ОСТОРОЖНО: поля с одинаковыми именами в разных XBlock-ах будут конфликтовать!"
        ),
        default="ru",
        scope=Scope.user_info,
    )

    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================================================

    def resource_string(self, path):
        """
        Загрузка текстового ресурса из пакета.

        Использует importlib.resources (Python 3.9+, xblock 5.0+).
        files(__package__) возвращает путь к текущему пакету (vladx/),
        joinpath(path) добавляет относительный путь к файлу,
        read_text() читает содержимое как строку.

        Устаревший способ (до xblock 5.0):
            import pkg_resources
            pkg_resources.resource_string(__name__, path).decode('utf-8')
        """
        return files(__package__).joinpath(path).read_text(encoding="utf-8")

    # ========================================================================
    # ПРЕДСТАВЛЕНИЯ (VIEWS)
    # ========================================================================
    #
    # Представление -- это метод, возвращающий объект Fragment.
    # Fragment содержит HTML, CSS и JavaScript для отображения блока.
    #
    # Runtime вызывает представление по имени:
    #   runtime.render(block, 'student_view', context)
    #
    # Стандартные имена представлений:
    #   'student_view'  -- основное представление для студентов (ОБЯЗАТЕЛЬНО для LMS)
    #   'studio_view'   -- представление редактирования в Studio
    #   'author_view'   -- предпросмотр в Studio (если нет -- используется student_view)
    #
    # Любой метод может стать представлением -- главное, чтобы runtime знал его имя.
    # В LMS используются student_view и studio_view.
    # В Workbench по умолчанию используется student_view.
    # ========================================================================

    @XBlock.supports('multi_device')
    def student_view(self, context=None):
        """
        Основное представление для студентов (student_view).

        Это ОБЯЗАТЕЛЬНЫЙ метод для работы в LMS Open edX.
        Вызывается, когда студент открывает страницу с этим блоком.

        Декоратор @XBlock.supports('multi_device') сообщает платформе,
        что это представление корректно отображается на мобильных устройствах.
        Платформа использует эту информацию для фильтрации блоков.

        Параметры:
            context (dict или None) -- контекст отрисовки, переданный runtime-ом.
                Может содержать информацию о родительском блоке, режиме просмотра и т.д.
                Передаётся во все вложенные вызовы render_child().

        Возвращает:
            Fragment -- объект, содержащий HTML, CSS и JavaScript блока.
        """
        # --- Шаг 1: Загрузка и форматирование HTML-шаблона ---
        # resource_string() загружает файл из пакета vladx/static/html/vladx.html
        # .format(self=self) подставляет значения полей: {self.field_name} -> значение
        html = self.resource_string("static/html/vladx.html")
        frag = Fragment(html.format(self=self))

        # --- Шаг 2: Добавление CSS ---
        # frag.add_css() встраивает CSS прямо в страницу (inline <style>).
        # Альтернатива: frag.add_css_url('url') -- подключение внешнего CSS-файла.
        frag.add_css(self.resource_string("static/css/vladx.css"))

        # --- Шаг 3: Добавление JavaScript ---
        # frag.add_javascript() встраивает JS прямо в страницу.
        # Альтернатива: frag.add_javascript_url('url') -- подключение внешнего JS-файла.
        frag.add_javascript(self.resource_string("static/js/src/vladx.js"))

        # --- Шаг 4: Рендеринг дочерних блоков ---
        # self.children -- список usage_id дочерних блоков (доступен при has_children=True).
        # self.runtime.get_block(child_id) -- создаёт экземпляр дочернего блока.
        # self.runtime.render_child(child, view_name, context) -- рендерит дочерний блок,
        #   возвращая Fragment.
        # frag.add_frag_resources(child_frag) -- добавляет CSS/JS дочернего блока в родительский.
        # child_frag.content -- HTML-содержимое дочернего блока.
        if self.children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                child_frag = self.runtime.render_child(child, 'student_view', context)
                # add_frag_resources копирует CSS и JS из дочернего Fragment
                # в родительский, чтобы стили и скрипты дочерних блоков работали.
                frag.add_fragment_resources(child_frag)
                # Добавляем HTML-содержимое дочернего блока в конец родительского.
                frag.add_content(child_frag.content)

        # --- Шаг 5: Инициализация JavaScript ---
        # frag.initialize_js('FunctionName') указывает runtime-у, какую JS-функцию
        # вызвать при инициализации блока. Имя функции должно совпадать
        # с функцией в JS-файле: function VladXBlock(runtime, element) { ... }
        #
        # Runtime автоматически найдёт DOM-элемент блока и передаст его как element.
        frag.initialize_js('VladXBlock')

        return frag

    def studio_view(self, context=None):
        """
        Представление для редактирования в Studio (studio_view).

        Вызывается, когда преподаватель нажимает "Редактировать" (Edit)
        на компоненте в Studio.

        Studio отображает этот Fragment в модальном окне.
        JavaScript внутри должен:
        1. Собрать данные из формы
        2. Отправить их на сервер через обработчик save_settings
        3. Вызвать runtime.notify('save', {state: 'end'}) для закрытия окна

        Параметры:
            context (dict или None) -- контекст от Studio.

        Возвращает:
            Fragment -- форма редактирования.
        """
        html = self.resource_string("static/html/vladx_studio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/vladx.css"))
        frag.add_javascript(self.resource_string("static/js/src/vladx_studio.js"))
        # Имя JS-функции для Studio -- отдельное от student_view
        frag.initialize_js('VladXStudio')
        return frag

    def author_view(self, context=None):
        """
        Представление для предпросмотра автором (author_view).

        Показывается в Studio в режиме предпросмотра (не редактирования).
        Если этот метод не определён, Studio использует student_view.

        author_view должен быть максимально похож на student_view,
        но может содержать дополнительные элементы для автора
        (например, бейдж режима, скрытые данные и т.д.).
        """
        # Повторно используем student_view
        frag = self.student_view(context)
        # Добавляем бейдж "Режим автора" -- виден только в Studio
        frag.add_content(
            '<div class="vladx-author-badge">Режим автора (author_view)</div>'
        )
        return frag

    def fallback_view(self, view_name, context=None):
        """
        Обработчик для неопределённых представлений (fallback_view).

        Если runtime запрашивает представление с именем, которое не определено
        как метод (например, 'some_custom_view'), XBlock вызывает fallback_view.

        Это полезно для:
        - Обработки нестандартных имён представлений
        - Отладки (какое представление запрошено)
        - Предоставления информативного сообщения вместо ошибки

        Параметры:
            view_name (str) -- имя запрошенного представления, которое не найдено.
            context (dict или None) -- контекст от runtime.

        Возвращает:
            Fragment -- HTML-сообщение о том, что представление не определено.
        """
        return Fragment(
            '<div class="vladx-fallback">'
            '<p><strong>VladX:</strong> Представление '
            '<code>{}</code> не определено.</p>'
            '<p>Используется fallback_view. Определённые представления: '
            'student_view, studio_view, author_view.</p>'
            '</div>'.format(view_name)
        )

    # ========================================================================
    # ОБРАБОТЧИКИ (HANDLERS)
    # ========================================================================
    #
    # Обработчик -- это метод, вызываемый из JavaScript через AJAX.
    # JavaScript получает URL обработчика через: runtime.handlerUrl(element, 'имя')
    #
    # Два типа обработчиков:
    #
    # @XBlock.json_handler -- упрощённый:
    #   - Автоматически парсит JSON из тела POST-запроса -> аргумент `data` (dict)
    #   - Автоматически сериализует возвращаемый dict/list в JSON-ответ
    #   - Возвращает 405, если метод не POST
    #   - Возвращает 400, если тело не валидный JSON
    #
    # @XBlock.handler -- сырой:
    #   - Получает webob.Request как аргумент
    #   - Должен вернуть webob.Response
    #   - Полный контроль над HTTP-ответом (заголовки, код, тип контента)
    #
    # Параметр suffix -- всё, что идёт после имени обработчика в URL:
    #   /handler/usage/submit_answer/extra/path  ->  suffix='extra/path'
    # ========================================================================

    @XBlock.json_handler
    def submit_answer(self, data, suffix=''):
        """
        Обработчик отправки ответа студентом.

        @XBlock.json_handler автоматически:
        1. Проверяет, что запрос -- POST (иначе 405 Method Not Allowed)
        2. Парсит JSON из тела запроса -> аргумент data (dict)
        3. Сериализует возвращаемый dict в JSON-ответ с Content-Type: application/json

        Параметры:
            data (dict)  -- десериализованные JSON-данные из тела запроса.
                            Ожидается: {"answer": "текст_ответа"}
            suffix (str) -- дополнительный путь после имени обработчика (обычно пуст).

        Возвращает:
            dict -- JSON-ответ с результатом проверки.
        """
        # --- Проверяем, не исчерпаны ли попытки ---
        if self.attempts_used >= self.max_attempts:
            return {
                "success": False,
                "error": "Исчерпаны все попытки ({}/{})".format(
                    self.attempts_used, self.max_attempts
                ),
            }

        # --- Сохраняем ответ студента ---
        # Присвоение self.student_answer автоматически сохраняет значение
        # в хранилище (runtime вызывает FieldData.set() при изменении поля).
        self.student_answer = data.get("answer", "")
        self.attempts_used += 1
        self.is_submitted = True

        # --- Увеличиваем общий счётчик ответов ---
        # Это поле Scope.user_state_summary -- оно общее для всех студентов.
        self.total_submissions += 1

        # --- Проверяем правильность ответа ---
        is_correct = (
            self.student_answer.strip().lower()
            == self.correct_answer.strip().lower()
        )

        # --- Рассчитываем и сохраняем оценку ---
        earned = self.weight if is_correct else 0.0
        self.score_earned = earned

        # --- Публикуем событие оценки (GRADE EVENT) ---
        # self.runtime.publish() отправляет событие в систему событий платформы.
        #
        # Для оценивания используется тип события 'grade':
        #   'value'     -- полученный балл
        #   'max_value' -- максимально возможный балл
        #
        # Платформа автоматически обновляет журнал оценок студента.
        # Для работы оценивания ОБЯЗАТЕЛЬНО: has_score = True на уровне класса.
        self.runtime.publish(self, 'grade', {
            'value': earned,
            'max_value': self.weight,
        })

        # --- Публикуем пользовательское аналитическое событие ---
        # Кроме стандартного 'grade', можно публиковать любые события
        # для аналитики, отладки и отслеживания поведения студентов.
        # Тип события -- произвольная строка, данные -- произвольный dict.
        self.runtime.publish(self, 'xblock.vladx.answer_submitted', {
            'answer': self.student_answer,
            'is_correct': is_correct,
            'attempt': self.attempts_used,
        })

        # --- Сохраняем произвольные данные (демонстрация поля Any) ---
        # Поле типа Any может хранить любой JSON-сериализуемый объект.
        self.student_data = {
            "last_answer": self.student_answer,
            "timestamp": str(datetime.utcnow()),
            "is_correct": is_correct,
        }

        return {
            "success": True,
            "is_correct": is_correct,
            "attempts_used": self.attempts_used,
            "max_attempts": self.max_attempts,
            "score": earned,
            "total_submissions": self.total_submissions,
            "explanation": self.explanation if is_correct else "",
        }

    @XBlock.json_handler
    def vote(self, data, suffix=''):
        """
        Обработчик голосования (thumbs up / thumbs down).

        Демонстрирует работу с полями Scope.user_state_summary
        (upvotes, downvotes -- агрегированные данные всех студентов)
        и Scope.user_state (voted -- индивидуальный флаг студента).

        Параметры:
            data (dict) -- ожидается {"vote_type": "up"} или {"vote_type": "down"}
        """
        if self.voted:
            return {
                "success": True,
                "upvotes": self.upvotes,
                "downvotes": self.downvotes,
            }

        vote_type = data.get("vote_type")
        if vote_type not in ("up", "down"):
            return {"success": False, "error": "Неверный тип голоса: {}".format(vote_type)}

        # Изменяем агрегированные счётчики (видны всем студентам)
        if vote_type == "up":
            self.upvotes += 1
        else:
            self.downvotes += 1

        # Устанавливаем индивидуальный флаг студента
        self.voted = True

        # Публикуем аналитическое событие
        self.runtime.publish(self, 'xblock.vladx.voted', {
            'vote_type': vote_type,
        })

        return {
            "success": True,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
        }

    @XBlock.json_handler
    def save_settings(self, data, suffix=''):
        """
        Обработчик сохранения настроек из Studio.

        Вызывается из JavaScript studio_view при нажатии "Сохранить".
        Обновляет поля Scope.content и Scope.settings.

        Параметры:
            data (dict) -- значения полей из формы Studio.
        """
        # Обновляем поля Scope.settings
        self.display_name = data.get("display_name", self.display_name)
        self.max_attempts = int(data.get("max_attempts", self.max_attempts))
        self.weight = float(data.get("weight", self.weight))
        self.allow_reset = bool(data.get("allow_reset", self.allow_reset))

        # Обновляем поля Scope.content
        self.question_text = data.get("question_text", self.question_text)
        self.correct_answer = data.get("correct_answer", self.correct_answer)
        self.explanation = data.get("explanation", self.explanation)

        return {"success": True}

    @XBlock.json_handler
    def get_state(self, data, suffix=''):
        """
        Обработчик получения текущего состояния блока.

        Вызывается из JavaScript при загрузке страницы для инициализации UI.
        Возвращает значения полей из РАЗНЫХ областей видимости.

        Обратите внимание: каждое поле автоматически возвращает значение
        для текущего пользователя и текущего блока в соответствии с его Scope.
        """
        return {
            # Scope.user_state -- данные текущего студента
            "student_answer": self.student_answer,
            "attempts_used": self.attempts_used,
            "is_submitted": self.is_submitted,
            "score_earned": self.score_earned,
            "voted": self.voted,
            # Scope.settings -- общие настройки блока
            "max_attempts": self.max_attempts,
            # Scope.user_state_summary -- агрегированные данные
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "total_submissions": self.total_submissions,
            # Scope.preferences -- предпочтения студента (для всех VladXBlock)
            "display_mode": self.display_mode,
        }

    @XBlock.json_handler
    def toggle_display_mode(self, data, suffix=''):
        """
        Обработчик переключения режима отображения.

        Демонстрирует работу с Scope.preferences:
        значение привязано к ТИПУ блока и КОНКРЕТНОМУ студенту.
        Если студент переключит режим в одном VladXBlock,
        ВСЕ его VladXBlock-и будут отображаться в новом режиме.
        """
        # Переключаем между "compact" и "full"
        self.display_mode = "compact" if self.display_mode == "full" else "full"
        return {"display_mode": self.display_mode}

    @XBlock.json_handler
    def reset_answer(self, data, suffix=''):
        """
        Обработчик сброса ответа студента.

        Сбрасывает поля Scope.user_state для текущего студента.
        Поля Scope.user_state_summary (total_submissions, upvotes, downvotes)
        НЕ сбрасываются, т.к. они общие для всех студентов.
        """
        if not self.allow_reset:
            return {"success": False, "error": "Сброс не разрешён преподавателем"}

        # Сбрасываем индивидуальные данные студента
        self.student_answer = ""
        self.is_submitted = False
        self.score_earned = 0.0
        self.attempts_used = 0
        self.student_data = None
        self.hint_index = 0

        return {"success": True}

    @XBlock.json_handler
    def show_hint(self, data, suffix=''):
        """
        Обработчик показа подсказки.

        Демонстрирует работу с полем типа List (hints) в Scope.settings
        и полем hint_index в Scope.user_state.
        """
        if not self.hints:
            return {"hint": None, "message": "Подсказки не заданы"}

        # hint_index -- индивидуальный для каждого студента
        if self.hint_index >= len(self.hints):
            return {"hint": None, "message": "Все подсказки уже показаны"}

        hint = self.hints[self.hint_index]
        self.hint_index += 1

        return {
            "hint": hint,
            "hints_remaining": len(self.hints) - self.hint_index,
        }

    @XBlock.handler
    def raw_data_handler(self, request, suffix=''):
        """
        Сырой обработчик (raw handler), возвращающий webob.Response.

        @XBlock.handler (БЕЗ json_) -- это низкоуровневый декоратор:
        - Получает webob.Request (полный HTTP-запрос)
        - Должен вернуть webob.Response (полный HTTP-ответ)
        - Нет автоматической JSON-сериализации
        - Полный контроль: код ответа, заголовки, Content-Type, тело

        Когда использовать raw handler вместо json_handler:
        - Нужно вернуть не-JSON данные (HTML, CSV, бинарные файлы)
        - Нужно обработать GET-запросы (json_handler требует POST)
        - Нужен контроль над HTTP-заголовками ответа
        - Нужно вернуть потоковый ответ (streaming)

        Параметры:
            request (webob.Request) -- полный HTTP-запрос.
                request.method  -- HTTP-метод ('GET', 'POST', ...)
                request.body    -- тело запроса (bytes)
                request.params  -- параметры запроса (query string + form data)
            suffix (str) -- дополнительный путь после имени обработчика.
        """
        # Формируем JSON-ответ вручную
        response_data = json.dumps({
            "raw_handler": True,
            "block_type": "vladx",
            "usage_id": str(self.scope_ids.usage_id),
            "http_method": request.method,
            "suffix": suffix,
        })

        # Создаём webob.Response с полным контролем
        return Response(
            body=response_data,
            content_type="application/json",
            charset="utf-8",
        )

    # ========================================================================
    # ВАЛИДАЦИЯ
    # ========================================================================

    def validate(self):
        """
        Валидация настроек блока.

        Метод validate() вызывается платформой (Studio) для проверки
        корректности настроек блока. Возвращает объект Validation
        с сообщениями об ошибках и предупреждениях.

        Типы сообщений:
        - ValidationMessage.ERROR   -- ошибка, блок может работать некорректно
        - ValidationMessage.WARNING -- предупреждение, блок будет работать

        ВАЖНО: всегда вызывайте super().validate() для наследования
        валидации из базового класса.
        """
        validation = super().validate()

        if not self.question_text:
            validation.add(
                ValidationMessage(
                    ValidationMessage.ERROR,
                    "Текст вопроса не может быть пустым."
                )
            )
        if self.max_attempts < 1:
            validation.add(
                ValidationMessage(
                    ValidationMessage.WARNING,
                    "Количество попыток должно быть не менее 1."
                )
            )
        if self.weight <= 0:
            validation.add(
                ValidationMessage(
                    ValidationMessage.WARNING,
                    "Вес задания должен быть положительным числом."
                )
            )

        return validation

    # ========================================================================
    # СЕРИАЛИЗАЦИЯ XML / OLX (Open Learning XML)
    # ========================================================================
    #
    # OLX -- это XML-формат, в котором Open edX хранит структуру курса.
    # XBlock-и автоматически сериализуются в OLX: поля -> атрибуты XML.
    #
    # Можно переопределить parse_xml() и add_xml_to_node() для:
    # - Кастомной обработки дочерних XML-элементов
    # - Хранения некоторых полей как дочерних узлов (а не атрибутов)
    # - Миграции данных при изменении формата
    #
    # Пример OLX для этого блока:
    #   <vladx display_name="Мой вопрос" max_attempts="5">
    #       <explanation>Текст пояснения</explanation>
    #       <html_demo><p>Дочерний контент</p></html_demo>
    #   </vladx>
    # ========================================================================

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Десериализация блока из XML/OLX.

        Переопределяем стандартный parse_xml, чтобы:
        1. Обработать дочерний узел <explanation> отдельно (не как дочерний блок)
        2. Остальные дочерние узлы добавить как дочерние XBlock-и

        Параметры:
            node (lxml.etree.Element) -- XML-узел этого блока.
            runtime (Runtime)         -- текущий runtime.
            keys (ScopeIds)           -- идентификаторы областей видимости.

        Возвращает:
            XBlock -- сконструированный экземпляр блока.
        """
        # construct_xblock_from_class создаёт экземпляр блока с правильными scope_ids
        block = runtime.construct_xblock_from_class(cls, keys)

        # Обрабатываем атрибуты XML-узла (display_name, max_attempts и т.д.)
        for name, value in node.items():
            if name == 'xblock-family':
                # Служебный атрибут, пропускаем
                continue
            # Устанавливаем значение поля, если оно существует
            if hasattr(block, name):
                field = block.fields.get(name)
                if field:
                    setattr(block, name, field.from_string(value))

        # Обрабатываем дочерние XML-узлы
        for child_node in node:
            if child_node.tag == "explanation":
                # <explanation> -- это НЕ дочерний блок, а поле с xml_node=True
                block.explanation = child_node.text or ""
            else:
                # Все остальные дочерние узлы -- это дочерние XBlock-и
                block.runtime.add_node_as_child(block, child_node)

        # Текст XML-узла может содержать текст вопроса (для краткой записи)
        if node.text and node.text.strip():
            block.question_text = node.text.strip()

        return block

    def add_xml_to_node(self, node):
        """
        Сериализация блока в XML/OLX.

        Переопределяем стандартный add_xml_to_node, чтобы:
        1. Сериализовать поле explanation как дочерний узел <explanation>
        2. Сериализовать дочерние блоки как дочерние XML-узлы

        Параметры:
            node (lxml.etree.Element) -- XML-узел, в который записывается блок.
        """
        # Устанавливаем имя XML-тега (обычно совпадает с именем entry_point)
        node.tag = self.xml_element_name()
        node.set('xblock-family', self.entry_point)

        # Сериализуем поля как атрибуты XML (кроме специальных)
        skip_fields = {'children', 'parent', 'explanation'}
        for field_name, field in self.fields.items():
            if field_name in skip_fields:
                continue
            if field.is_set_on(self):
                node.set(field_name, field.to_string(field.read_from(self)))

        # Поле explanation сериализуется как дочерний XML-узел
        if self.explanation:
            from lxml import etree
            expl_node = etree.SubElement(node, "explanation")
            expl_node.text = self.explanation

        # Добавляем дочерние блоки как дочерние XML-узлы
        if self.has_children:
            self.add_children_to_node(node)

    # ========================================================================
    # ПОИСКОВАЯ ИНДЕКСАЦИЯ
    # ========================================================================

    def index_dictionary(self):
        """
        Словарь для поисковой индексации содержимого блока.

        Вызывается платформой Open edX для индексации контента
        в поисковой системе (ElasticSearch/OpenSearch).
        Студенты и преподаватели могут находить блоки через поиск.

        Возвращает:
            dict -- словарь с полями для индексации.
        """
        xblock_body = super().index_dictionary()
        xblock_body.update({
            "content": {
                "display_name": self.display_name,
                "question_text": self.question_text,
            },
            "content_type": "VladX Learning Hub",
        })
        return xblock_body

    # ========================================================================
    # СЦЕНАРИИ ДЛЯ XBLOCK WORKBENCH
    # ========================================================================

    @staticmethod
    def workbench_scenarios():
        """
        Сценарии для XBlock Workbench.

        XBlock Workbench -- это среда разработки и тестирования XBlock-ов.
        Каждый сценарий -- это кортеж (название, XML-строка).

        XML-строка определяет, какие блоки создать и с какими настройками.
        Workbench парсит XML и создаёт блоки через parse_xml().

        Специальные теги Workbench:
        - <vertical_demo> -- контейнер, располагающий блоки вертикально
        - <html_demo>     -- простой HTML-блок для демонстрации дочерних элементов

        Возвращает:
            list[tuple[str, str]] -- список пар (название_сценария, xml_строка).
        """
        return [
            # --- Сценарий 1: Базовый блок с настройками по умолчанию ---
            ("VladX -- Базовый",
             """<vladx/>"""),

            # --- Сценарий 2: Блок с пользовательскими настройками ---
            # Атрибуты XML соответствуют полям Scope.content и Scope.settings
            ("VladX -- С настройками",
             """<vladx
                    display_name="Вопрос про обработчики"
                    question_text="Какой декоратор используется для JSON-обработчиков в XBlock?"
                    correct_answer="json_handler"
                    max_attempts="5"
                    weight="2.0"
                />"""),

            # --- Сценарий 3: Несколько блоков в вертикальном контейнере ---
            # vertical_demo -- встроенный блок Workbench для вертикальной компоновки
            ("VladX -- Несколько блоков",
             """<vertical_demo>
                    <vladx display_name="Вопрос 1"/>
                    <vladx display_name="Вопрос 2"
                           question_text="Какой scope хранит данные одного студента?"
                           correct_answer="user_state"/>
                    <vladx display_name="Вопрос 3"
                           question_text="Какой атрибут класса включает поддержку дочерних блоков?"
                           correct_answer="has_children"/>
                </vertical_demo>"""),

            # --- Сценарий 4: Блок с дочерними элементами ---
            # html_demo -- встроенный блок Workbench для отображения HTML
            # Дочерние блоки рендерятся через self.runtime.render_child()
            ("VladX -- С дочерними блоками",
             """<vladx display_name="Вопрос с подсказками">
                    <html_demo><div style="padding: 10px; background: #eef;">
                        <b>Подсказка:</b> Это название метода Python, который возвращает Fragment.
                    </div></html_demo>
                </vladx>"""),
        ]


# ============================================================================
# ПРИМЕЧАНИЕ: ИМПОРТ ValidationMessage
# ============================================================================
# ValidationMessage используется в методе validate().
# Импортируем здесь, т.к. в некоторых версиях xblock этот класс
# может находиться в разных модулях.
# ============================================================================
try:
    from xblock.validation import ValidationMessage
except ImportError:
    # Заглушка, если модуль валидации недоступен (старые версии xblock)
    class ValidationMessage:
        """Заглушка для ValidationMessage, если модуль недоступен."""
        ERROR = 'error'
        WARNING = 'warning'

        def __init__(self, message_type, message_text):
            self.type = message_type
            self.text = message_text
