/* ============================================================================
 * JavaScript для студентського представлення (student_view) VladX Learning Hub
 * ============================================================================
 *
 * ВАЖЛИВО ДЛЯ XBLOCK-РОЗРОБНИКА:
 *
 * 1. Цей файл додається до Fragment через frag.add_javascript() в Python.
 *
 * 2. Функція VladXBlock(runtime, element) викликається автоматично завдяки
 *    frag.initialize_js('VladXBlock') в Python-коді.
 *    Ім'я функції ПОВИННО збігатися з аргументом initialize_js().
 *
 * 3. Аргументи функції ініціалізації:
 *    - runtime  -- об'єкт середовища виконання XBlock (надається платформою)
 *    - element  -- DOM-елемент, що містить HTML-вміст цього блоку
 *
 * 4. runtime надає ключові методи:
 *    - runtime.handlerUrl(element, 'handler_name') -- створює URL для AJAX-запиту
 *      до серверного обробника. Це ЄДИНИЙ спосіб спілкування JS з Python.
 *    - runtime.children(element) -- повертає список дочірніх блоків
 *    - runtime.childMap(element, 'child_name') -- знаходить дочірній блок за іменем
 *
 * 5. jQuery ($) доступний глобально в середовищі XBlock Workbench та Open edX.
 *    ЗАВЖДИ використовуйте $(selector, element) -- другий аргумент element
 *    обмежує пошук DOM-елементів поточним блоком. Без цього селектор
 *    знайде елементи ВСІХ блоків на сторінці!
 *
 * 6. AJAX-запити до обробників ЗАВЖДИ використовують метод POST.
 *    Дані передаються як JSON.stringify({...}).
 *    @XBlock.json_handler автоматично парсить JSON та повертає JSON.
 * ============================================================================ */

function VladXBlock(runtime, element) {

    /* ====================================================================
     * ОТРИМАННЯ URL-ів СЕРВЕРНИХ ОБРОБНИКІВ
     * ====================================================================
     * runtime.handlerUrl() генерує повний URL для кожного обробника.
     * Формат URL залежить від runtime-у:
     *   Workbench: /handler/{usage_id}/{handler_name}/
     *   LMS:       /courses/{course}/xblock/{usage}/handler/{handler_name}
     * ==================================================================== */
    /* Кешуємо jQuery-обгортку для зручності */
    var $element = $(element);

    /* URL обробника надсилання відповіді (@XBlock.json_handler submit_answer) */
    var submitUrl = runtime.handlerUrl(element, 'submit_answer');

    /* URL обробника голосування (@XBlock.json_handler vote) */
    var voteUrl = runtime.handlerUrl(element, 'vote');

    /* URL обробника отримання стану (@XBlock.json_handler get_state) */
    var getStateUrl = runtime.handlerUrl(element, 'get_state');

    /* URL обробника перемикання режиму (@XBlock.json_handler toggle_display_mode) */
    var toggleModeUrl = runtime.handlerUrl(element, 'toggle_display_mode');

    /* URL обробника скидання відповіді (@XBlock.json_handler reset_answer) */
    var resetUrl = runtime.handlerUrl(element, 'reset_answer');

    /* URL обробника показу підказки (@XBlock.json_handler show_hint) */
    var hintUrl = runtime.handlerUrl(element, 'show_hint');

    /* ====================================================================
     * ДОПОМІЖНІ ФУНКЦІЇ ОНОВЛЕННЯ ІНТЕРФЕЙСУ
     * ==================================================================== */

    /**
     * Оновити відображення лічильника спроб та балів.
     * Викликається після кожної дії, що змінює стан.
     */
    function updateAttemptsAndScore(data) {
        if (data.attempts_used !== undefined) {
            $('.vladx-attempts-used', element).text(data.attempts_used);
        }
        if (data.max_attempts !== undefined) {
            $('.vladx-max-attempts', element).text(data.max_attempts);
        }
        if (data.score !== undefined) {
            $('.vladx-score-value', element).text(data.score);
        }
        if (data.score_earned !== undefined) {
            $('.vladx-score-value', element).text(data.score_earned);
        }
        if (data.total_submissions !== undefined) {
            $('.vladx-total-sub-count', element).text(data.total_submissions);
        }
    }

    /**
     * Оновити відображення результату (правильно/неправильно/помилка).
     */
    function showResult(data) {
        var $result = $('.vladx-result', element);
        var $message = $('.vladx-result-message', element);
        var $explanation = $('.vladx-explanation', element);

        /* Скинути всі CSS-класи результату */
        $result.removeClass('vladx-correct vladx-incorrect vladx-error');

        if (data.error) {
            /* Помилка (наприклад, вичерпано спроби) */
            $result.addClass('vladx-error');
            $message.text(data.error);
            $explanation.text('');
        } else if (data.is_correct) {
            /* Правильна відповідь */
            $result.addClass('vladx-correct');
            $message.text('Правильно!');
            $explanation.text(data.explanation || '');
        } else {
            /* Неправильна відповідь */
            $result.addClass('vladx-incorrect');
            $message.text('Неправильно. Спробуйте ще раз.');
            $explanation.text('');
        }
    }

    /**
     * Оновити лічильники голосів.
     */
    function updateVotes(data) {
        $('.vladx-upvote-count', element).text(data.upvotes);
        $('.vladx-downvote-count', element).text(data.downvotes);
    }

    /* ====================================================================
     * ОБРОБНИКИ ПОДІЙ КОРИСТУВАЦЬКОГО ІНТЕРФЕЙСУ
     * ====================================================================
     * Кожний обробник надсилає AJAX POST-запит до серверного обробника
     * та оновлює UI при успішній відповіді.
     * ==================================================================== */

    /**
     * НАДСИЛАННЯ ВІДПОВІДІ
     * Натискання кнопки "Надіслати" -> POST на submit_answer -> оновлення UI
     */
    $('.vladx-submit-btn', element).on('click', function() {
        /* Отримуємо текст відповіді з поля введення */
        var answer = $('.vladx-answer-input', element).val();

        $.ajax({
            type: "POST",                              /* Обов'язково POST для XBlock-обробників */
            url: submitUrl,                            /* URL, отриманий від runtime.handlerUrl() */
            data: JSON.stringify({ answer: answer }),   /* Дані ЗАВЖДИ як JSON-рядок */
            success: function(response) {
                /* response -- JSON-об'єкт, повернутий @XBlock.json_handler */
                if (response.success) {
                    showResult(response);
                    updateAttemptsAndScore(response);
                    /* Оновлюємо total_submissions */
                    $('.vladx-total-sub-count', element).text(response.total_submissions);
                    /* Блокуємо кнопку, якщо спроби вичерпано */
                    if (response.attempts_used >= response.max_attempts) {
                        $('.vladx-submit-btn', element).prop('disabled', true);
                    }
                } else {
                    showResult({ error: response.error });
                }
            }
        });
    });

    /**
     * ГОЛОСУВАННЯ "ЗА"
     * Натискання кнопки thumbs-up -> POST на vote з vote_type='up'
     */
    $('.vladx-upvote', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: voteUrl,
            data: JSON.stringify({ vote_type: 'up' }),
            success: function(response) {
                if (response.success) {
                    updateVotes(response);
                }
            }
        });
    });

    /**
     * ГОЛОСУВАННЯ "ПРОТИ"
     * Натискання кнопки thumbs-down -> POST на vote з vote_type='down'
     */
    $('.vladx-downvote', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: voteUrl,
            data: JSON.stringify({ vote_type: 'down' }),
            success: function(response) {
                if (response.success) {
                    updateVotes(response);
                }
            }
        });
    });

    /**
     * ПЕРЕМИКАННЯ РЕЖИМУ ВІДОБРАЖЕННЯ
     * Перемикає Scope.preferences між "compact" та "full"
     */
    $('.vladx-toggle-mode', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: toggleModeUrl,
            data: JSON.stringify({}),
            success: function(response) {
                /* Оновлюємо data-атрибут, який керує CSS-стилями */
                $('.vladx-block', element).attr('data-mode', response.display_mode);
                /* Оновлюємо текст кнопки */
                $('.vladx-toggle-mode', element).text(response.display_mode);
            }
        });
    });

    /**
     * СКИДАННЯ ВІДПОВІДІ
     * Очищає відповідь студента та скидає спроби
     */
    $('.vladx-reset-btn', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: resetUrl,
            data: JSON.stringify({}),
            success: function(response) {
                if (response.success) {
                    /* Очищаємо поле введення */
                    $('.vladx-answer-input', element).val('');
                    /* Приховуємо результат */
                    $('.vladx-result', element).removeClass('vladx-correct vladx-incorrect vladx-error');
                    /* Скидаємо лічильники */
                    $('.vladx-attempts-used', element).text('0');
                    $('.vladx-score-value', element).text('0.0');
                    /* Розблоковуємо кнопку надсилання */
                    $('.vladx-submit-btn', element).prop('disabled', false);
                    /* Приховуємо підказку */
                    $('.vladx-hint-text', element).removeClass('vladx-visible').text('');
                } else {
                    alert(response.error);
                }
            }
        });
    });

    /**
     * ПОКАЗ ПІДКАЗКИ
     * Запитує наступну підказку зі списку hints (Scope.settings, тип List)
     */
    $('.vladx-hint-btn', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: hintUrl,
            data: JSON.stringify({}),
            success: function(response) {
                if (response.hint) {
                    var $hintText = $('.vladx-hint-text', element);
                    $hintText.text(response.hint);
                    $hintText.addClass('vladx-visible');
                }
            }
        });
    });

    /* ====================================================================
     * ІНІЦІАЛІЗАЦІЯ: ЗАВАНТАЖЕННЯ ПОЧАТКОВОГО СТАНУ
     * ====================================================================
     * При завантаженні сторінки запитуємо поточний стан блоку,
     * щоб коректно відобразити спроби, бали, режим тощо.
     *
     * $(function() { ... }) -- виконується після завантаження DOM.
     * ==================================================================== */
    $(function() {
        $.ajax({
            type: "POST",
            url: getStateUrl,
            data: JSON.stringify({}),
            success: function(state) {
                /* Оновлюємо всі елементи інтерфейсу за поточним станом */
                updateAttemptsAndScore(state);
                updateVotes(state);

                /* Встановлюємо режим відображення */
                $('.vladx-block', element).attr('data-mode', state.display_mode);
                $('.vladx-toggle-mode', element).text(state.display_mode);

                /* Блокуємо надсилання, якщо спроби вичерпано */
                if (state.attempts_used >= state.max_attempts) {
                    $('.vladx-submit-btn', element).prop('disabled', true);
                }

                if (state.voted) {
                    $element.find('.vladx-upvote').prop('disabled', true);
                    $element.find('.vladx-downvote').prop('disabled', true);
                }

                /* Якщо відповідь вже було надіслано -- показуємо результат */
                if (state.is_submitted && state.student_answer) {
                    $('.vladx-answer-input', element).val(state.student_answer);
                }
            }
        });
    });
}
