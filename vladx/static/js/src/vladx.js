/* ============================================================================
 * JavaScript для студенческого представления (student_view) VladX Learning Hub
 * ============================================================================
 *
 * ВАЖНО ДЛЯ XBLOCK-РАЗРАБОТЧИКА:
 *
 * 1. Этот файл добавляется во Fragment через frag.add_javascript() в Python.
 *
 * 2. Функция VladXBlock(runtime, element) вызывается автоматически благодаря
 *    frag.initialize_js('VladXBlock') в Python-коде.
 *    Имя функции ДОЛЖНО совпадать с аргументом initialize_js().
 *
 * 3. Аргументы функции инициализации:
 *    - runtime  -- объект среды выполнения XBlock (предоставляется платформой)
 *    - element  -- DOM-элемент, содержащий HTML-содержимое этого блока
 *
 * 4. runtime предоставляет ключевые методы:
 *    - runtime.handlerUrl(element, 'handler_name') -- создаёт URL для AJAX-запроса
 *      к серверному обработчику. Это ЕДИНСТВЕННЫЙ способ общения JS с Python.
 *    - runtime.children(element) -- возвращает список дочерних блоков
 *    - runtime.childMap(element, 'child_name') -- находит дочерний блок по имени
 *
 * 5. jQuery ($) доступен глобально в среде XBlock Workbench и Open edX.
 *    ВСЕГДА используйте $(selector, element) -- второй аргумент element
 *    ограничивает поиск DOM-элементов текущим блоком. Без этого селектор
 *    найдёт элементы ВСЕХ блоков на странице!
 *
 * 6. AJAX-запросы к обработчикам ВСЕГДА используют метод POST.
 *    Данные передаются как JSON.stringify({...}).
 *    @XBlock.json_handler автоматически парсит JSON и возвращает JSON.
 * ============================================================================ */

function VladXBlock(runtime, element) {

    /* ====================================================================
     * ПОЛУЧЕНИЕ URL-ов СЕРВЕРНЫХ ОБРАБОТЧИКОВ
     * ====================================================================
     * runtime.handlerUrl() генерирует полный URL для каждого обработчика.
     * Формат URL зависит от runtime-а:
     *   Workbench: /handler/{usage_id}/{handler_name}/
     *   LMS:       /courses/{course}/xblock/{usage}/handler/{handler_name}
     * ==================================================================== */
    /* Кэшируем jQuery-обёртку для удобства */
    var $element = $(element);

    /* URL обработчика отправки ответа (@XBlock.json_handler submit_answer) */
    var submitUrl = runtime.handlerUrl(element, 'submit_answer');

    /* URL обработчика голосования (@XBlock.json_handler vote) */
    var voteUrl = runtime.handlerUrl(element, 'vote');

    /* URL обработчика получения состояния (@XBlock.json_handler get_state) */
    var getStateUrl = runtime.handlerUrl(element, 'get_state');

    /* URL обработчика переключения режима (@XBlock.json_handler toggle_display_mode) */
    var toggleModeUrl = runtime.handlerUrl(element, 'toggle_display_mode');

    /* URL обработчика сброса ответа (@XBlock.json_handler reset_answer) */
    var resetUrl = runtime.handlerUrl(element, 'reset_answer');

    /* URL обработчика показа подсказки (@XBlock.json_handler show_hint) */
    var hintUrl = runtime.handlerUrl(element, 'show_hint');

    /* ====================================================================
     * ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ОБНОВЛЕНИЯ ИНТЕРФЕЙСА
     * ==================================================================== */

    /**
     * Обновить отображение счётчика попыток и баллов.
     * Вызывается после каждого действия, изменяющего состояние.
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
     * Обновить отображение результата (правильно/неправильно/ошибка).
     */
    function showResult(data) {
        var $result = $('.vladx-result', element);
        var $message = $('.vladx-result-message', element);
        var $explanation = $('.vladx-explanation', element);

        /* Сбросить все CSS-классы результата */
        $result.removeClass('vladx-correct vladx-incorrect vladx-error');

        if (data.error) {
            /* Ошибка (например, исчерпаны попытки) */
            $result.addClass('vladx-error');
            $message.text(data.error);
            $explanation.text('');
        } else if (data.is_correct) {
            /* Правильный ответ */
            $result.addClass('vladx-correct');
            $message.text('Правильно!');
            $explanation.text(data.explanation || '');
        } else {
            /* Неправильный ответ */
            $result.addClass('vladx-incorrect');
            $message.text('Неправильно. Попробуйте ещё раз.');
            $explanation.text('');
        }
    }

    /**
     * Обновить счётчики голосов.
     */
    function updateVotes(data) {
        $('.vladx-upvote-count', element).text(data.upvotes);
        $('.vladx-downvote-count', element).text(data.downvotes);
    }

    /* ====================================================================
     * ОБРАБОТЧИКИ СОБЫТИЙ ПОЛЬЗОВАТЕЛЬСКОГО ИНТЕРФЕЙСА
     * ====================================================================
     * Каждый обработчик отправляет AJAX POST-запрос к серверному обработчику
     * и обновляет UI при успешном ответе.
     * ==================================================================== */

    /**
     * ОТПРАВКА ОТВЕТА
     * Нажатие кнопки "Отправить" -> POST на submit_answer -> обновление UI
     */
    $('.vladx-submit-btn', element).on('click', function() {
        /* Получаем текст ответа из поля ввода */
        var answer = $('.vladx-answer-input', element).val();

        $.ajax({
            type: "POST",                              /* Обязательно POST для XBlock-обработчиков */
            url: submitUrl,                            /* URL, полученный от runtime.handlerUrl() */
            data: JSON.stringify({ answer: answer }),   /* Данные ВСЕГДА как JSON-строка */
            success: function(response) {
                /* response -- JSON-объект, возвращённый @XBlock.json_handler */
                if (response.success) {
                    showResult(response);
                    updateAttemptsAndScore(response);
                    /* Обновляем total_submissions */
                    $('.vladx-total-sub-count', element).text(response.total_submissions);
                    /* Блокируем кнопку, если попытки исчерпаны */
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
     * ГОЛОСОВАНИЕ "ЗА"
     * Нажатие кнопки thumbs-up -> POST на vote с vote_type='up'
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
     * ГОЛОСОВАНИЕ "ПРОТИВ"
     * Нажатие кнопки thumbs-down -> POST на vote с vote_type='down'
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
     * ПЕРЕКЛЮЧЕНИЕ РЕЖИМА ОТОБРАЖЕНИЯ
     * Переключает Scope.preferences между "compact" и "full"
     */
    $('.vladx-toggle-mode', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: toggleModeUrl,
            data: JSON.stringify({}),
            success: function(response) {
                /* Обновляем data-атрибут, который управляет CSS-стилями */
                $('.vladx-block', element).attr('data-mode', response.display_mode);
                /* Обновляем текст кнопки */
                $('.vladx-toggle-mode', element).text(response.display_mode);
            }
        });
    });

    /**
     * СБРОС ОТВЕТА
     * Очищает ответ студента и сбрасывает попытки
     */
    $('.vladx-reset-btn', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: resetUrl,
            data: JSON.stringify({}),
            success: function(response) {
                if (response.success) {
                    /* Очищаем поле ввода */
                    $('.vladx-answer-input', element).val('');
                    /* Скрываем результат */
                    $('.vladx-result', element).removeClass('vladx-correct vladx-incorrect vladx-error');
                    /* Сбрасываем счётчики */
                    $('.vladx-attempts-used', element).text('0');
                    $('.vladx-score-value', element).text('0.0');
                    /* Разблокируем кнопку отправки */
                    $('.vladx-submit-btn', element).prop('disabled', false);
                    /* Скрываем подсказку */
                    $('.vladx-hint-text', element).removeClass('vladx-visible').text('');
                } else {
                    alert(response.error);
                }
            }
        });
    });

    /**
     * ПОКАЗ ПОДСКАЗКИ
     * Запрашивает следующую подсказку из списка hints (Scope.settings, тип List)
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
     * ИНИЦИАЛИЗАЦИЯ: ЗАГРУЗКА НАЧАЛЬНОГО СОСТОЯНИЯ
     * ====================================================================
     * При загрузке страницы запрашиваем текущее состояние блока,
     * чтобы корректно отобразить попытки, баллы, режим и т.д.
     *
     * $(function() { ... }) -- выполняется после загрузки DOM.
     * ==================================================================== */
    $(function() {
        $.ajax({
            type: "POST",
            url: getStateUrl,
            data: JSON.stringify({}),
            success: function(state) {
                /* Обновляем все элементы интерфейса по текущему состоянию */
                updateAttemptsAndScore(state);
                updateVotes(state);

                /* Устанавливаем режим отображения */
                $('.vladx-block', element).attr('data-mode', state.display_mode);
                $('.vladx-toggle-mode', element).text(state.display_mode);

                /* Блокируем отправку, если попытки исчерпаны */
                if (state.attempts_used >= state.max_attempts) {
                    $('.vladx-submit-btn', element).prop('disabled', true);
                }

                if (state.voted) {
                    $element.find('.vladx-upvote').prop('disabled', true);
                    $element.find('.vladx-downvote').prop('disabled', true);
                }

                /* Если ответ уже был отправлен -- показываем результат */
                if (state.is_submitted && state.student_answer) {
                    $('.vladx-answer-input', element).val(state.student_answer);
                }
            }
        });
    });
}
