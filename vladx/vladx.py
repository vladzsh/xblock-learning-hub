"""
VladX Learning Hub -- навчальний XBlock, що демонструє ВСІ можливості XBlock API.

XBlock -- це компонентна архітектура для освітніх платформ Open edX.
Кожний XBlock -- це міні-веб-застосунок: у нього є сховище даних (поля),
представлення (views), обробники AJAX-запитів (handlers), і він може
містити дочірні блоки (children).

Цей файл демонструє:
  1. Усі типи полів (String, Integer, Boolean, Float, List, Dict, DateTime, Any)
  2. Усі області видимості (Scope.content, settings, user_state, user_state_summary,
     preferences, user_info)
  3. Представлення (student_view, studio_view, author_view, fallback_view)
  4. Обробники (@XBlock.json_handler, @XBlock.handler)
  5. Fragment API (HTML + CSS + JS)
  6. Дочірні блоки (has_children)
  7. Сервіси (@XBlock.needs, @XBlock.wants)
  8. Оцінювання (has_score, runtime.publish grade)
  9. Валідація (validate)
  10. Серіалізація XML/OLX (parse_xml, add_xml_to_node)
  11. Пошукова індексація (index_dictionary)
  12. Інтеграція з edX (icon_class, workbench_scenarios)
"""

# ============================================================================
# ІМПОРТИ
# ============================================================================
# json -- для роботи з JSON у сирому обробнику (raw handler)
import json
# logging -- стандартне логування Python
import logging
# datetime -- для роботи з полем DateTime
from datetime import datetime

# webob.Response -- об'єкт HTTP-відповіді, потрібний для @XBlock.handler (raw handler)
from webob import Response

# Fragment -- об'єкт, що містить HTML + CSS + JS для відтворення блоку на сторінці.
# Кожне представлення (view) повертає Fragment.
# Починаючи з xblock 4.0, Fragment -- це pass-through до web_fragments.fragment.
from web_fragments.fragment import Fragment

# importlib.resources -- сучасний спосіб завантаження файлів з пакета (з xblock 5.0+).
# Замінює застарілий pkg_resources.resource_string().
from importlib.resources import files

# XBlock -- базовий клас для всіх XBlock-ів.
# Наслідування від XBlock дає доступ до полів, представлень, обробників,
# сервісів та системи плагінів.
from xblock.core import XBlock

# Поля (Fields) -- зберігають стан блоку.
# Кожне поле має тип даних та область видимості (Scope).
from xblock.fields import (
    String,     # Рядкове поле
    Integer,    # Ціле число
    Boolean,    # Логічне значення (True/False)
    Float,      # Число з плаваючою точкою
    List,       # Список (Python list, зберігається як JSON array)
    Dict,       # Словник (Python dict, зберігається як JSON object)
    DateTime,   # Дата і час (ISO-формат рядка)
    Any,        # Довільний тип (будь-який JSON-серіалізований об'єкт)
    Scope,      # Області видимості полів
)

# Логер для цього модуля.
# Використовуйте log.info(), log.warning(), log.error() для налагодження.
log = logging.getLogger(__name__)


# ============================================================================
# ДЕКОРАТОРИ СЕРВІСІВ (на рівні класу)
# ============================================================================
# @XBlock.needs('service_name') -- ОБОВ'ЯЗКОВИЙ сервіс. Якщо runtime не надасть
#     цей сервіс, при зверненні до нього буде викинуто виняток NoSuchServiceError.
#
# @XBlock.wants('service_name') -- НЕОБОВ'ЯЗКОВИЙ сервіс. Якщо runtime його не надасть,
#     self.runtime.service(self, 'service_name') поверне None, і код не впаде.
#
# Доступ до сервісу: self.runtime.service(self, 'ім'я_сервісу')
#
# Стандартні сервіси:
#   'i18n'     -- інтернаціоналізація (gettext, переклади)
#   'settings' -- серверні налаштування для типу блоку
#   'user'     -- інформація про поточного користувача
#   'fs'       -- файлова система (django-pyfs) для зберігання файлів
# ============================================================================
@XBlock.needs('i18n')       # Сервіс інтернаціоналізації -- обов'язковий
@XBlock.wants('settings')   # Сервіс серверних налаштувань -- необов'язковий
@XBlock.wants('user')       # Сервіс користувача -- необов'язковий
class VladXBlock(XBlock):
    """
    VladX Learning Hub -- навчальний XBlock.

    Функціональність:
    - Викладач задає питання та правильну відповідь через Studio
    - Студент вводить відповідь, отримує оцінку
    - Студент може голосувати (thumbs up/down) за питання
    - Перемикання компактного/повного режиму відображення
    - Підтримка дочірніх блоків

    ВАЖЛИВО: Не перевизначайте __init__() в XBlock-ах!
    XBlock-и створюються runtime-ом, і __init__ може викликатися
    в різних контекстах. Використовуйте поля з default-значеннями.
    """

    # ========================================================================
    # АТРИБУТИ КЛАСУ
    # ========================================================================

    # has_children = True дозволяє цьому блоку містити дочірні блоки.
    # Дочірні блоки визначаються в OLX:
    #   <vladx>
    #       <html_demo><p>Дочірній контент</p></html_demo>
    #   </vladx>
    # Доступ: self.children (список usage_id дочірніх блоків)
    has_children = True

    # has_score = True повідомляє платформі, що цей блок виставляє оцінки.
    # Для виставлення оцінки потрібно викликати:
    #   self.runtime.publish(self, 'grade', {'value': X, 'max_value': Y})
    has_score = True

    # icon_class визначає іконку блоку в LMS на навігаційній панелі.
    # Допустимі значення: 'problem' (задача), 'video' (відео), 'other' (інше)
    icon_class = 'problem'

    # ========================================================================
    # ПОЛЯ (FIELDS) -- СХОВИЩЕ СТАНУ БЛОКУ
    # ========================================================================
    #
    # Кожне поле -- це дескриптор Python, оголошений на рівні класу.
    # При зверненні через self.field_name, runtime автоматично завантажує
    # і зберігає значення у сховищі (БД, файл тощо).
    #
    # Параметри поля:
    #   help         -- опис поля (для документації та UI Studio)
    #   display_name -- відображуване ім'я в інтерфейсі Studio
    #   default      -- значення за замовчуванням
    #   scope        -- область видимості (хто бачить ці дані)
    #   values       -- допустимі значення (для валідації в UI)
    #   enforce_type -- примусова перевірка типу при записі
    #   xml_node     -- серіалізувати як дочірній XML-вузол (а не атрибут)
    #   force_export -- експортувати в XML, навіть якщо значення за замовчуванням
    #
    # ОБЛАСТІ ВИДИМОСТІ (Scope) визначають, ХТО бачить дані та ДО ЧОГО вони прив'язані:
    #
    # Scope = UserScope + BlockScope
    #
    # UserScope (хто бачить):
    #   NONE -- дані не прив'язані до користувача (всі бачать одне й те саме)
    #   ONE  -- дані прив'язані до конкретного користувача
    #   ALL  -- дані агреговані по всіх користувачах
    #
    # BlockScope (до чого прив'язані):
    #   DEFINITION -- до визначення блоку (може використовуватися в кількох місцях)
    #   USAGE      -- до конкретного використання блоку в курсі
    #   TYPE       -- до всіх блоків даного типу (Python-класу)
    #   ALL        -- до всіх блоків усіх типів
    # ========================================================================

    # ========================================================================
    # ПОЛЯ Scope.content  (BlockScope.DEFINITION + UserScope.NONE)
    # ========================================================================
    # Дані, спільні для всіх студентів, прив'язані до ВИЗНАЧЕННЯ блоку.
    # Одне визначення може використовуватися в кількох курсах.
    # Типове використання: текст питання, правильна відповідь, контент.
    # В OLX ці поля серіалізуються як атрибути XML-тега.
    # ========================================================================

    question_text = String(
        display_name="Текст питання",
        help=(
            "Питання, яке бачать усі студенти. "
            "Scope.content = BlockScope.DEFINITION + UserScope.NONE -- "
            "дані спільні для всіх користувачів і прив'язані до визначення блоку. "
            "Якщо один і той самий блок використовується в кількох курсах, "
            "усі вони бачитимуть один і той самий текст питання."
        ),
        default="Який метод XBlock викликається для відображення студентського представлення?",
        scope=Scope.content,
    )

    correct_answer = String(
        display_name="Правильна відповідь",
        help=(
            "Правильна відповідь на питання. "
            "Scope.content -- спільна для всіх, прив'язана до визначення блоку."
        ),
        default="student_view",
        scope=Scope.content,
    )

    explanation = String(
        display_name="Пояснення",
        help=(
            "Текст пояснення, що показується після правильної відповіді. "
            "Scope.content -- спільний для всіх."
        ),
        default=(
            "Метод student_view() -- це основне представлення XBlock, "
            "яке викликається LMS для показу блоку студентам. "
            "Він зобов'язаний повертати об'єкт Fragment з HTML, CSS та JavaScript."
        ),
        scope=Scope.content,
        # xml_node=True означає, що при серіалізації в OLX це поле
        # буде дочірнім XML-вузлом, а не атрибутом:
        #   <vladx><explanation>текст</explanation></vladx>
        # а не <vladx explanation="текст" />
        xml_node=True,
    )

    # ========================================================================
    # ПОЛЯ Scope.settings  (BlockScope.USAGE + UserScope.NONE)
    # ========================================================================
    # Дані, спільні для всіх студентів, прив'язані до ВИКОРИСТАННЯ блоку.
    # Кожне використання блоку в курсі може мати свої налаштування.
    # Типове використання: назва, максимум спроб, вага оцінки, дедлайн.
    # ========================================================================

    display_name = String(
        display_name="Назва компонента",
        help=(
            "Назва, що відображається в заголовку блоку та в навігації курсу. "
            "Scope.settings = BlockScope.USAGE + UserScope.NONE -- "
            "дані спільні для всіх користувачів, але прив'язані до конкретного "
            "використання блоку (кожний екземпляр у курсі може мати свою назву)."
        ),
        default="VladX Learning Hub",
        scope=Scope.settings,
    )

    max_attempts = Integer(
        display_name="Максимум спроб",
        help=(
            "Скільки разів студент може надіслати відповідь. "
            "Тип Integer зберігає цілі числа. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default=3,
        scope=Scope.settings,
    )

    weight = Float(
        display_name="Вага завдання",
        help=(
            "Вага завдання в підсумковій оцінці (максимальний бал). "
            "Тип Float зберігає числа з плаваючою точкою. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default=1.0,
        scope=Scope.settings,
    )

    due_date = DateTime(
        display_name="Термін здачі",
        help=(
            "Дата і час, до яких потрібно надіслати відповідь. "
            "Тип DateTime зберігає дату в ISO-форматі (наприклад, '2025-12-31T23:59:59'). "
            "Значення None означає, що термін не встановлено. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default=None,
        scope=Scope.settings,
    )

    hints = List(
        display_name="Підказки",
        help=(
            "Список текстових підказок для студента. "
            "Тип List зберігає Python-список, серіалізований у JSON-масив. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default=["Це назва методу Python", "Починається на 'student_'"],
        scope=Scope.settings,
    )

    options = Dict(
        display_name="Додаткові параметри",
        help=(
            "Словник додаткових параметрів конфігурації. "
            "Тип Dict зберігає Python-словник, серіалізований у JSON-об'єкт. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default={"show_explanation": True, "shuffle_hints": False},
        scope=Scope.settings,
    )

    allow_reset = Boolean(
        display_name="Дозволити скидання",
        help=(
            "Чи може студент скинути свою відповідь і почати заново. "
            "Тип Boolean зберігає True/False. "
            "Scope.settings -- налаштування конкретного використання блоку."
        ),
        default=True,
        scope=Scope.settings,
    )

    # ========================================================================
    # ПОЛЯ Scope.user_state  (BlockScope.USAGE + UserScope.ONE)
    # ========================================================================
    # Дані конкретного студента для конкретного використання блоку.
    # У кожного студента -- свої значення цих полів.
    # Типове використання: відповідь студента, кількість спроб, отриманий бал.
    # ========================================================================

    student_answer = String(
        help=(
            "Відповідь, введена студентом. "
            "Scope.user_state = BlockScope.USAGE + UserScope.ONE -- "
            "дані прив'язані до конкретного студента І конкретного використання блоку. "
            "Кожний студент бачить лише свою відповідь."
        ),
        default="",
        scope=Scope.user_state,
    )

    attempts_used = Integer(
        help=(
            "Скільки спроб студент вже використав. "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=0,
        scope=Scope.user_state,
    )

    is_submitted = Boolean(
        help=(
            "Чи надіслано відповідь (хоча б раз). "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=False,
        scope=Scope.user_state,
    )

    score_earned = Float(
        help=(
            "Бали, отримані студентом за це завдання. "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=0.0,
        scope=Scope.user_state,
    )

    student_data = Any(
        help=(
            "Довільні дані студента. "
            "Тип Any може зберігати БУДЬ-ЯКИЙ JSON-серіалізований Python-об'єкт: "
            "dict, list, str, int, None та їх комбінації. "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=None,
        scope=Scope.user_state,
    )

    voted = Boolean(
        help=(
            "Чи голосував цей студент за/проти питання. "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=False,
        scope=Scope.user_state,
    )

    hint_index = Integer(
        help=(
            "Індекс останньої показаної підказки для цього студента. "
            "Scope.user_state -- індивідуально для кожного студента."
        ),
        default=0,
        scope=Scope.user_state,
    )

    # ========================================================================
    # ПОЛЯ Scope.user_state_summary  (BlockScope.USAGE + UserScope.ALL)
    # ========================================================================
    # Дані, агреговані по ВСІХ студентах для конкретного використання блоку.
    # Усі студенти бачать одні й ті самі значення, і кожний може їх змінювати.
    # Типове використання: загальний лічильник відповідей, голоси, гістограми.
    # УВАГА: при конкурентному записі можливі перегони (race conditions).
    # ========================================================================

    total_submissions = Integer(
        help=(
            "Загальна кількість надсилань відповідей усіма студентами. "
            "Scope.user_state_summary = BlockScope.USAGE + UserScope.ALL -- "
            "агреговані дані, видимі всім і змінювані всіма."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    upvotes = Integer(
        help=(
            "Загальна кількість голосів 'за' від усіх студентів. "
            "Scope.user_state_summary -- агреговані дані."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    downvotes = Integer(
        help=(
            "Загальна кількість голосів 'проти' від усіх студентів. "
            "Scope.user_state_summary -- агреговані дані."
        ),
        default=0,
        scope=Scope.user_state_summary,
    )

    # ========================================================================
    # ПОЛЯ Scope.preferences  (BlockScope.TYPE + UserScope.ONE)
    # ========================================================================
    # Уподобання конкретного студента для ВСІХ блоків даного типу (VladXBlock).
    # Якщо студент перемкне режим відображення в одному VladXBlock,
    # це значення буде спільним для ВСІХ VladXBlock-ів цього студента.
    # Типове використання: швидкість відеоплеєра, мова субтитрів, тема оформлення.
    # ========================================================================

    display_mode = String(
        help=(
            "Бажаний режим відображення: 'full' (повний) або 'compact' (компактний). "
            "Scope.preferences = BlockScope.TYPE + UserScope.ONE -- "
            "дані прив'язані до конкретного студента, але застосовуються до ВСІХ блоків "
            "типу VladXBlock на всій платформі."
        ),
        default="full",
        scope=Scope.preferences,
        values=["compact", "full"],
    )

    # ========================================================================
    # ПОЛЯ Scope.user_info  (BlockScope.ALL + UserScope.ONE)
    # ========================================================================
    # Інформація про конкретного студента, глобальна для ВСІХ блоків ВСІХ типів.
    # Типове використання: часовий пояс користувача, мова інтерфейсу.
    # УВАГА: різні типи блоків ділять один простір імен полів --
    # два поля з однаковим іменем у різних блоках посилатимуться на одні дані!
    # ========================================================================

    user_language = String(
        help=(
            "Бажана мова користувача. "
            "Scope.user_info = BlockScope.ALL + UserScope.ONE -- "
            "дані прив'язані до конкретного студента, але глобальні для ВСІХ блоків. "
            "ОБЕРЕЖНО: поля з однаковими іменами в різних XBlock-ах конфліктуватимуть!"
        ),
        default="uk",
        scope=Scope.user_info,
    )

    # ========================================================================
    # ДОПОМІЖНІ МЕТОДИ
    # ========================================================================

    def resource_string(self, path):
        """
        Завантаження текстового ресурсу з пакета.

        Використовує importlib.resources (Python 3.9+, xblock 5.0+).
        files(__package__) повертає шлях до поточного пакета (vladx/),
        joinpath(path) додає відносний шлях до файлу,
        read_text() читає вміст як рядок.

        Застарілий спосіб (до xblock 5.0):
            import pkg_resources
            pkg_resources.resource_string(__name__, path).decode('utf-8')
        """
        return files(__package__).joinpath(path).read_text(encoding="utf-8")

    # ========================================================================
    # ПРЕДСТАВЛЕННЯ (VIEWS)
    # ========================================================================
    #
    # Представлення -- це метод, що повертає об'єкт Fragment.
    # Fragment містить HTML, CSS та JavaScript для відображення блоку.
    #
    # Runtime викликає представлення за іменем:
    #   runtime.render(block, 'student_view', context)
    #
    # Стандартні імена представлень:
    #   'student_view'  -- основне представлення для студентів (ОБОВ'ЯЗКОВО для LMS)
    #   'studio_view'   -- представлення редагування в Studio
    #   'author_view'   -- попередній перегляд у Studio (якщо немає -- використовується student_view)
    #
    # Будь-який метод може стати представленням -- головне, щоб runtime знав його ім'я.
    # В LMS використовуються student_view та studio_view.
    # У Workbench за замовчуванням використовується student_view.
    # ========================================================================

    @XBlock.supports('multi_device')
    def student_view(self, context=None):
        """
        Основне представлення для студентів (student_view).

        Це ОБОВ'ЯЗКОВИЙ метод для роботи в LMS Open edX.
        Викликається, коли студент відкриває сторінку з цим блоком.

        Декоратор @XBlock.supports('multi_device') повідомляє платформі,
        що це представлення коректно відображається на мобільних пристроях.
        Платформа використовує цю інформацію для фільтрації блоків.

        Параметри:
            context (dict або None) -- контекст відтворення, переданий runtime-ом.
                Може містити інформацію про батьківський блок, режим перегляду тощо.
                Передається в усі вкладені виклики render_child().

        Повертає:
            Fragment -- об'єкт, що містить HTML, CSS та JavaScript блоку.
        """
        # --- Крок 1: Завантаження та форматування HTML-шаблону ---
        # resource_string() завантажує файл з пакета vladx/static/html/vladx.html
        # .format(self=self) підставляє значення полів: {self.field_name} -> значення
        html = self.resource_string("static/html/vladx.html")
        frag = Fragment(html.format(self=self))

        # --- Крок 2: Додавання CSS ---
        # frag.add_css() вбудовує CSS прямо в сторінку (inline <style>).
        # Альтернатива: frag.add_css_url('url') -- підключення зовнішнього CSS-файлу.
        frag.add_css(self.resource_string("static/css/vladx.css"))

        # --- Крок 3: Додавання JavaScript ---
        # frag.add_javascript() вбудовує JS прямо в сторінку.
        # Альтернатива: frag.add_javascript_url('url') -- підключення зовнішнього JS-файлу.
        frag.add_javascript(self.resource_string("static/js/src/vladx.js"))

        # --- Крок 4: Рендеринг дочірніх блоків ---
        # self.children -- список usage_id дочірніх блоків (доступний при has_children=True).
        # self.runtime.get_block(child_id) -- створює екземпляр дочірнього блоку.
        # self.runtime.render_child(child, view_name, context) -- рендерить дочірній блок,
        #   повертаючи Fragment.
        # frag.add_frag_resources(child_frag) -- додає CSS/JS дочірнього блоку до батьківського.
        # child_frag.content -- HTML-вміст дочірнього блоку.
        if self.children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                child_frag = self.runtime.render_child(child, 'student_view', context)
                # add_frag_resources копіює CSS та JS з дочірнього Fragment
                # до батьківського, щоб стилі та скрипти дочірніх блоків працювали.
                frag.add_fragment_resources(child_frag)
                # Додаємо HTML-вміст дочірнього блоку в кінець батьківського.
                frag.add_content(child_frag.content)

        # --- Крок 5: Ініціалізація JavaScript ---
        # frag.initialize_js('FunctionName') вказує runtime-у, яку JS-функцію
        # викликати при ініціалізації блоку. Ім'я функції повинно збігатися
        # з функцією в JS-файлі: function VladXBlock(runtime, element) { ... }
        #
        # Runtime автоматично знайде DOM-елемент блоку та передасть його як element.
        frag.initialize_js('VladXBlock')

        return frag

    def studio_view(self, context=None):
        """
        Представлення для редагування в Studio (studio_view).

        Викликається, коли викладач натискає "Редагувати" (Edit)
        на компоненті в Studio.

        Studio відображає цей Fragment у модальному вікні.
        JavaScript всередині повинен:
        1. Зібрати дані з форми
        2. Надіслати їх на сервер через обробник save_settings
        3. Викликати runtime.notify('save', {state: 'end'}) для закриття вікна

        Параметри:
            context (dict або None) -- контекст від Studio.

        Повертає:
            Fragment -- форма редагування.
        """
        html = self.resource_string("static/html/vladx_studio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/vladx.css"))
        frag.add_javascript(self.resource_string("static/js/src/vladx_studio.js"))
        # Ім'я JS-функції для Studio -- окреме від student_view
        frag.initialize_js('VladXStudio')
        return frag

    def author_view(self, context=None):
        """
        Представлення для попереднього перегляду автором (author_view).

        Показується в Studio в режимі попереднього перегляду (не редагування).
        Якщо цей метод не визначено, Studio використовує student_view.

        author_view повинен бути максимально схожим на student_view,
        але може містити додаткові елементи для автора
        (наприклад, бейдж режиму, приховані дані тощо).
        """
        # Повторно використовуємо student_view
        frag = self.student_view(context)
        # Додаємо бейдж "Режим автора" -- видимий лише в Studio
        frag.add_content(
            '<div class="vladx-author-badge">Режим автора (author_view)</div>'
        )
        return frag

    def fallback_view(self, view_name, context=None):
        """
        Обробник для невизначених представлень (fallback_view).

        Якщо runtime запитує представлення з іменем, яке не визначено
        як метод (наприклад, 'some_custom_view'), XBlock викликає fallback_view.

        Це корисно для:
        - Обробки нестандартних імен представлень
        - Налагодження (яке представлення запитано)
        - Надання інформативного повідомлення замість помилки

        Параметри:
            view_name (str) -- ім'я запитаного представлення, яке не знайдено.
            context (dict або None) -- контекст від runtime.

        Повертає:
            Fragment -- HTML-повідомлення про те, що представлення не визначено.
        """
        return Fragment(
            '<div class="vladx-fallback">'
            '<p><strong>VladX:</strong> Представлення '
            '<code>{}</code> не визначено.</p>'
            '<p>Використовується fallback_view. Визначені представлення: '
            'student_view, studio_view, author_view.</p>'
            '</div>'.format(view_name)
        )

    # ========================================================================
    # ОБРОБНИКИ (HANDLERS)
    # ========================================================================
    #
    # Обробник -- це метод, що викликається з JavaScript через AJAX.
    # JavaScript отримує URL обробника через: runtime.handlerUrl(element, 'ім'я')
    #
    # Два типи обробників:
    #
    # @XBlock.json_handler -- спрощений:
    #   - Автоматично парсить JSON з тіла POST-запиту -> аргумент `data` (dict)
    #   - Автоматично серіалізує повернутий dict/list у JSON-відповідь
    #   - Повертає 405, якщо метод не POST
    #   - Повертає 400, якщо тіло не валідний JSON
    #
    # @XBlock.handler -- сирий:
    #   - Отримує webob.Request як аргумент
    #   - Повинен повернути webob.Response
    #   - Повний контроль над HTTP-відповіддю (заголовки, код, тип контенту)
    #
    # Параметр suffix -- все, що йде після імені обробника в URL:
    #   /handler/usage/submit_answer/extra/path  ->  suffix='extra/path'
    # ========================================================================

    @XBlock.json_handler
    def submit_answer(self, data, suffix=''):
        """
        Обробник надсилання відповіді студентом.

        @XBlock.json_handler автоматично:
        1. Перевіряє, що запит -- POST (інакше 405 Method Not Allowed)
        2. Парсить JSON з тіла запиту -> аргумент data (dict)
        3. Серіалізує повернутий dict у JSON-відповідь з Content-Type: application/json

        Параметри:
            data (dict)  -- десеріалізовані JSON-дані з тіла запиту.
                            Очікується: {"answer": "текст_відповіді"}
            suffix (str) -- додатковий шлях після імені обробника (зазвичай порожній).

        Повертає:
            dict -- JSON-відповідь з результатом перевірки.
        """
        # --- Перевіряємо, чи не вичерпані спроби ---
        if self.attempts_used >= self.max_attempts:
            return {
                "success": False,
                "error": "Вичерпано всі спроби ({}/{})".format(
                    self.attempts_used, self.max_attempts
                ),
            }

        # --- Зберігаємо відповідь студента ---
        # Присвоєння self.student_answer автоматично зберігає значення
        # у сховищі (runtime викликає FieldData.set() при зміні поля).
        self.student_answer = data.get("answer", "")
        self.attempts_used += 1
        self.is_submitted = True

        # --- Збільшуємо загальний лічильник відповідей ---
        # Це поле Scope.user_state_summary -- воно спільне для всіх студентів.
        self.total_submissions += 1

        # --- Перевіряємо правильність відповіді ---
        is_correct = (
            self.student_answer.strip().lower()
            == self.correct_answer.strip().lower()
        )

        # --- Розраховуємо та зберігаємо оцінку ---
        earned = self.weight if is_correct else 0.0
        self.score_earned = earned

        # --- Публікуємо подію оцінки (GRADE EVENT) ---
        # self.runtime.publish() надсилає подію до системи подій платформи.
        #
        # Для оцінювання використовується тип події 'grade':
        #   'value'     -- отриманий бал
        #   'max_value' -- максимально можливий бал
        #
        # Платформа автоматично оновлює журнал оцінок студента.
        # Для роботи оцінювання ОБОВ'ЯЗКОВО: has_score = True на рівні класу.
        self.runtime.publish(self, 'grade', {
            'value': earned,
            'max_value': self.weight,
        })

        # --- Публікуємо користувацьку аналітичну подію ---
        # Крім стандартного 'grade', можна публікувати будь-які події
        # для аналітики, налагодження та відстеження поведінки студентів.
        # Тип події -- довільний рядок, дані -- довільний dict.
        self.runtime.publish(self, 'xblock.vladx.answer_submitted', {
            'answer': self.student_answer,
            'is_correct': is_correct,
            'attempt': self.attempts_used,
        })

        # --- Зберігаємо довільні дані (демонстрація поля Any) ---
        # Поле типу Any може зберігати будь-який JSON-серіалізований об'єкт.
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
        Обробник голосування (thumbs up / thumbs down).

        Демонструє роботу з полями Scope.user_state_summary
        (upvotes, downvotes -- агреговані дані всіх студентів)
        та Scope.user_state (voted -- індивідуальний прапорець студента).

        Параметри:
            data (dict) -- очікується {"vote_type": "up"} або {"vote_type": "down"}
        """
        if self.voted:
            return {
                "success": True,
                "upvotes": self.upvotes,
                "downvotes": self.downvotes,
            }

        vote_type = data.get("vote_type")
        if vote_type not in ("up", "down"):
            return {"success": False, "error": "Невірний тип голосу: {}".format(vote_type)}

        # Змінюємо агреговані лічильники (видимі всім студентам)
        if vote_type == "up":
            self.upvotes += 1
        else:
            self.downvotes += 1

        # Встановлюємо індивідуальний прапорець студента
        self.voted = True

        # Публікуємо аналітичну подію
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
        Обробник збереження налаштувань із Studio.

        Викликається з JavaScript studio_view при натисканні "Зберегти".
        Оновлює поля Scope.content та Scope.settings.

        Параметри:
            data (dict) -- значення полів з форми Studio.
        """
        # Оновлюємо поля Scope.settings
        self.display_name = data.get("display_name", self.display_name)
        self.max_attempts = int(data.get("max_attempts", self.max_attempts))
        self.weight = float(data.get("weight", self.weight))
        self.allow_reset = bool(data.get("allow_reset", self.allow_reset))

        # Оновлюємо поля Scope.content
        self.question_text = data.get("question_text", self.question_text)
        self.correct_answer = data.get("correct_answer", self.correct_answer)
        self.explanation = data.get("explanation", self.explanation)

        return {"success": True}

    @XBlock.json_handler
    def get_state(self, data, suffix=''):
        """
        Обробник отримання поточного стану блоку.

        Викликається з JavaScript при завантаженні сторінки для ініціалізації UI.
        Повертає значення полів з РІЗНИХ областей видимості.

        Зверніть увагу: кожне поле автоматично повертає значення
        для поточного користувача та поточного блоку відповідно до його Scope.
        """
        return {
            # Scope.user_state -- дані поточного студента
            "student_answer": self.student_answer,
            "attempts_used": self.attempts_used,
            "is_submitted": self.is_submitted,
            "score_earned": self.score_earned,
            "voted": self.voted,
            # Scope.settings -- загальні налаштування блоку
            "max_attempts": self.max_attempts,
            # Scope.user_state_summary -- агреговані дані
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "total_submissions": self.total_submissions,
            # Scope.preferences -- уподобання студента (для всіх VladXBlock)
            "display_mode": self.display_mode,
        }

    @XBlock.json_handler
    def toggle_display_mode(self, data, suffix=''):
        """
        Обробник перемикання режиму відображення.

        Демонструє роботу з Scope.preferences:
        значення прив'язане до ТИПУ блоку та КОНКРЕТНОГО студента.
        Якщо студент перемкне режим в одному VladXBlock,
        ВСІ його VladXBlock-и відображатимуться в новому режимі.
        """
        # Перемикаємо між "compact" та "full"
        self.display_mode = "compact" if self.display_mode == "full" else "full"
        return {"display_mode": self.display_mode}

    @XBlock.json_handler
    def reset_answer(self, data, suffix=''):
        """
        Обробник скидання відповіді студента.

        Скидає поля Scope.user_state для поточного студента.
        Поля Scope.user_state_summary (total_submissions, upvotes, downvotes)
        НЕ скидаються, оскільки вони спільні для всіх студентів.
        """
        if not self.allow_reset:
            return {"success": False, "error": "Скидання не дозволено викладачем"}

        # Скидаємо індивідуальні дані студента
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
        Обробник показу підказки.

        Демонструє роботу з полем типу List (hints) у Scope.settings
        та полем hint_index у Scope.user_state.
        """
        if not self.hints:
            return {"hint": None, "message": "Підказки не задано"}

        # hint_index -- індивідуальний для кожного студента
        if self.hint_index >= len(self.hints):
            return {"hint": None, "message": "Усі підказки вже показано"}

        hint = self.hints[self.hint_index]
        self.hint_index += 1

        return {
            "hint": hint,
            "hints_remaining": len(self.hints) - self.hint_index,
        }

    @XBlock.handler
    def raw_data_handler(self, request, suffix=''):
        """
        Сирий обробник (raw handler), що повертає webob.Response.

        @XBlock.handler (БЕЗ json_) -- це низькорівневий декоратор:
        - Отримує webob.Request (повний HTTP-запит)
        - Повинен повернути webob.Response (повну HTTP-відповідь)
        - Немає автоматичної JSON-серіалізації
        - Повний контроль: код відповіді, заголовки, Content-Type, тіло

        Коли використовувати raw handler замість json_handler:
        - Потрібно повернути не-JSON дані (HTML, CSV, бінарні файли)
        - Потрібно обробити GET-запити (json_handler вимагає POST)
        - Потрібен контроль над HTTP-заголовками відповіді
        - Потрібно повернути потокову відповідь (streaming)

        Параметри:
            request (webob.Request) -- повний HTTP-запит.
                request.method  -- HTTP-метод ('GET', 'POST', ...)
                request.body    -- тіло запиту (bytes)
                request.params  -- параметри запиту (query string + form data)
            suffix (str) -- додатковий шлях після імені обробника.
        """
        # Формуємо JSON-відповідь вручну
        response_data = json.dumps({
            "raw_handler": True,
            "block_type": "vladx",
            "usage_id": str(self.scope_ids.usage_id),
            "http_method": request.method,
            "suffix": suffix,
        })

        # Створюємо webob.Response з повним контролем
        return Response(
            body=response_data,
            content_type="application/json",
            charset="utf-8",
        )

    # ========================================================================
    # ВАЛІДАЦІЯ
    # ========================================================================

    def validate(self):
        """
        Валідація налаштувань блоку.

        Метод validate() викликається платформою (Studio) для перевірки
        коректності налаштувань блоку. Повертає об'єкт Validation
        з повідомленнями про помилки та попередження.

        Типи повідомлень:
        - ValidationMessage.ERROR   -- помилка, блок може працювати некоректно
        - ValidationMessage.WARNING -- попередження, блок працюватиме

        ВАЖЛИВО: завжди викликайте super().validate() для наслідування
        валідації з базового класу.
        """
        validation = super().validate()

        if not self.question_text:
            validation.add(
                ValidationMessage(
                    ValidationMessage.ERROR,
                    "Текст питання не може бути порожнім."
                )
            )
        if self.max_attempts < 1:
            validation.add(
                ValidationMessage(
                    ValidationMessage.WARNING,
                    "Кількість спроб повинна бути не менше 1."
                )
            )
        if self.weight <= 0:
            validation.add(
                ValidationMessage(
                    ValidationMessage.WARNING,
                    "Вага завдання повинна бути додатним числом."
                )
            )

        return validation

    # ========================================================================
    # СЕРІАЛІЗАЦІЯ XML / OLX (Open Learning XML)
    # ========================================================================
    #
    # OLX -- це XML-формат, у якому Open edX зберігає структуру курсу.
    # XBlock-и автоматично серіалізуються в OLX: поля -> атрибути XML.
    #
    # Можна перевизначити parse_xml() та add_xml_to_node() для:
    # - Кастомної обробки дочірніх XML-елементів
    # - Зберігання деяких полів як дочірніх вузлів (а не атрибутів)
    # - Міграції даних при зміні формату
    #
    # Приклад OLX для цього блоку:
    #   <vladx display_name="Моє питання" max_attempts="5">
    #       <explanation>Текст пояснення</explanation>
    #       <html_demo><p>Дочірній контент</p></html_demo>
    #   </vladx>
    # ========================================================================

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """
        Десеріалізація блоку з XML/OLX.

        Перевизначаємо стандартний parse_xml, щоб:
        1. Обробити дочірній вузол <explanation> окремо (не як дочірній блок)
        2. Решту дочірніх вузлів додати як дочірні XBlock-и

        Параметри:
            node (lxml.etree.Element) -- XML-вузол цього блоку.
            runtime (Runtime)         -- поточний runtime.
            keys (ScopeIds)           -- ідентифікатори областей видимості.

        Повертає:
            XBlock -- сконструйований екземпляр блоку.
        """
        # construct_xblock_from_class створює екземпляр блоку з правильними scope_ids
        block = runtime.construct_xblock_from_class(cls, keys)

        # Обробляємо атрибути XML-вузла (display_name, max_attempts тощо)
        for name, value in node.items():
            if name == 'xblock-family':
                # Службовий атрибут, пропускаємо
                continue
            # Встановлюємо значення поля, якщо воно існує
            if hasattr(block, name):
                field = block.fields.get(name)
                if field:
                    setattr(block, name, field.from_string(value))

        # Обробляємо дочірні XML-вузли
        for child_node in node:
            if child_node.tag == "explanation":
                # <explanation> -- це НЕ дочірній блок, а поле з xml_node=True
                block.explanation = child_node.text or ""
            else:
                # Усі інші дочірні вузли -- це дочірні XBlock-и
                block.runtime.add_node_as_child(block, child_node)

        # Текст XML-вузла може містити текст питання (для короткого запису)
        if node.text and node.text.strip():
            block.question_text = node.text.strip()

        return block

    def add_xml_to_node(self, node):
        """
        Серіалізація блоку в XML/OLX.

        Перевизначаємо стандартний add_xml_to_node, щоб:
        1. Серіалізувати поле explanation як дочірній вузол <explanation>
        2. Серіалізувати дочірні блоки як дочірні XML-вузли

        Параметри:
            node (lxml.etree.Element) -- XML-вузол, у який записується блок.
        """
        # Встановлюємо ім'я XML-тега (зазвичай збігається з іменем entry_point)
        node.tag = self.xml_element_name()
        node.set('xblock-family', self.entry_point)

        # Серіалізуємо поля як атрибути XML (крім спеціальних)
        skip_fields = {'children', 'parent', 'explanation'}
        for field_name, field in self.fields.items():
            if field_name in skip_fields:
                continue
            if field.is_set_on(self):
                node.set(field_name, field.to_string(field.read_from(self)))

        # Поле explanation серіалізується як дочірній XML-вузол
        if self.explanation:
            from lxml import etree
            expl_node = etree.SubElement(node, "explanation")
            expl_node.text = self.explanation

        # Додаємо дочірні блоки як дочірні XML-вузли
        if self.has_children:
            self.add_children_to_node(node)

    # ========================================================================
    # ПОШУКОВА ІНДЕКСАЦІЯ
    # ========================================================================

    def index_dictionary(self):
        """
        Словник для пошукової індексації вмісту блоку.

        Викликається платформою Open edX для індексації контенту
        в пошуковій системі (ElasticSearch/OpenSearch).
        Студенти та викладачі можуть знаходити блоки через пошук.

        Повертає:
            dict -- словник з полями для індексації.
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
    # СЦЕНАРІЇ ДЛЯ XBLOCK WORKBENCH
    # ========================================================================

    @staticmethod
    def workbench_scenarios():
        """
        Сценарії для XBlock Workbench.

        XBlock Workbench -- це середовище розробки та тестування XBlock-ів.
        Кожний сценарій -- це кортеж (назва, XML-рядок).

        XML-рядок визначає, які блоки створити та з якими налаштуваннями.
        Workbench парсить XML і створює блоки через parse_xml().

        Спеціальні теги Workbench:
        - <vertical_demo> -- контейнер, що розташовує блоки вертикально
        - <html_demo>     -- простий HTML-блок для демонстрації дочірніх елементів

        Повертає:
            list[tuple[str, str]] -- список пар (назва_сценарію, xml_рядок).
        """
        return [
            # --- Сценарій 1: Базовий блок з налаштуваннями за замовчуванням ---
            ("VladX -- Базовий",
             """<vladx/>"""),

            # --- Сценарій 2: Блок з користувацькими налаштуваннями ---
            # Атрибути XML відповідають полям Scope.content та Scope.settings
            ("VladX -- З налаштуваннями",
             """<vladx
                    display_name="Питання про обробники"
                    question_text="Який декоратор використовується для JSON-обробників у XBlock?"
                    correct_answer="json_handler"
                    max_attempts="5"
                    weight="2.0"
                />"""),

            # --- Сценарій 3: Кілька блоків у вертикальному контейнері ---
            # vertical_demo -- вбудований блок Workbench для вертикальної компоновки
            ("VladX -- Кілька блоків",
             """<vertical_demo>
                    <vladx display_name="Питання 1"/>
                    <vladx display_name="Питання 2"
                           question_text="Який scope зберігає дані одного студента?"
                           correct_answer="user_state"/>
                    <vladx display_name="Питання 3"
                           question_text="Який атрибут класу вмикає підтримку дочірніх блоків?"
                           correct_answer="has_children"/>
                </vertical_demo>"""),

            # --- Сценарій 4: Блок з дочірніми елементами ---
            # html_demo -- вбудований блок Workbench для відображення HTML
            # Дочірні блоки рендеряться через self.runtime.render_child()
            ("VladX -- З дочірніми блоками",
             """<vladx display_name="Питання з підказками">
                    <html_demo><div style="padding: 10px; background: #eef;">
                        <b>Підказка:</b> Це назва методу Python, який повертає Fragment.
                    </div></html_demo>
                </vladx>"""),
        ]


# ============================================================================
# ПРИМІТКА: ІМПОРТ ValidationMessage
# ============================================================================
# ValidationMessage використовується в методі validate().
# Імпортуємо тут, оскільки в деяких версіях xblock цей клас
# може знаходитися в різних модулях.
# ============================================================================
try:
    from xblock.validation import ValidationMessage
except ImportError:
    # Заглушка, якщо модуль валідації недоступний (старі версії xblock)
    class ValidationMessage:
        """Заглушка для ValidationMessage, якщо модуль недоступний."""
        ERROR = 'error'
        WARNING = 'warning'

        def __init__(self, message_type, message_text):
            self.type = message_type
            self.text = message_text
