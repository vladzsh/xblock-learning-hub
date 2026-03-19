/* ============================================================================
 * JavaScript для представлення Studio (studio_view) VladX Learning Hub
 * ============================================================================
 *
 * ВАЖЛИВО ДЛЯ XBLOCK-РОЗРОБНИКА:
 *
 * Studio -- застосунок Open edX для створення курсів.
 * Це представлення відкривається при натисканні "Редагувати" (Edit) на блоці.
 *
 * Ключові відмінності від student_view JavaScript:
 *
 * 1. Для збереження налаштувань використовується обробник save_settings.
 *
 * 2. Після успішного збереження ОБОВ'ЯЗКОВО викликати:
 *    runtime.notify('save', {state: 'end'})
 *    Це повідомляє Studio, що редагування завершено, і Studio закриває
 *    модальне вікно редагування.
 *
 * 3. Для скасування викликати:
 *    runtime.notify('cancel', {})
 *    Studio закриє вікно без збереження.
 *
 * 4. Ім'я функції 'VladXStudio' повинно збігатися з аргументом
 *    frag.initialize_js('VladXStudio') в Python-методі studio_view().
 * ============================================================================ */

function VladXStudio(runtime, element) {

    /* URL обробника збереження налаштувань на сервері */
    var saveUrl = runtime.handlerUrl(element, 'save_settings');

    /* ====================================================================
     * ІНІЦІАЛІЗАЦІЯ ФОРМИ
     * ====================================================================
     * Checkbox в HTML отримує значення як рядок "True"/"False" через
     * data-value атрибут (тому що Python bool рендериться так у шаблоні).
     * Тут ми конвертуємо рядок у стан checked.
     * ==================================================================== */
    var $allowReset = $('#vladx-allow-reset', element);
    $allowReset.prop('checked', $allowReset.data('value') === 'True');

    /* ====================================================================
     * ОБРОБНИК КНОПКИ "ЗБЕРЕГТИ"
     * ====================================================================
     * 1. Збираємо значення з форми
     * 2. Надсилаємо POST-запит до обробника save_settings
     * 3. При успіху -- викликаємо runtime.notify('save', {state: 'end'})
     * ==================================================================== */
    $('.vladx-studio-save', element).on('click', function() {
        /* Збираємо дані з усіх полів форми */
        var data = {
            /* String поле (Scope.settings) */
            display_name: $('#vladx-display-name', element).val(),
            /* String поле (Scope.content) */
            question_text: $('#vladx-question', element).val(),
            /* String поле (Scope.content) */
            correct_answer: $('#vladx-correct-answer', element).val(),
            /* String поле (Scope.content) */
            explanation: $('#vladx-explanation', element).val(),
            /* Integer поле (Scope.settings) -- конвертується в int на сервері */
            max_attempts: $('#vladx-max-attempts', element).val(),
            /* Float поле (Scope.settings) -- конвертується в float на сервері */
            weight: $('#vladx-weight', element).val(),
            /* Boolean поле (Scope.settings) -- checkbox.is(':checked') повертає boolean */
            allow_reset: $('#vladx-allow-reset', element).is(':checked')
        };

        $.ajax({
            type: "POST",
            url: saveUrl,
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    /*
                     * runtime.notify('save', {state: 'end'}) -- ОБОВ'ЯЗКОВИЙ виклик.
                     * Без нього Studio не дізнається, що редагування завершено,
                     * і модальне вікно залишиться відкритим.
                     *
                     * Варіанти state:
                     *   'start' -- початок збереження (можна показати індикатор завантаження)
                     *   'end'   -- збереження завершено (Studio закриває вікно)
                     */
                    runtime.notify('save', {state: 'end'});
                }
            },
            error: function() {
                /* У разі помилки -- повідомляємо користувача */
                runtime.notify('error', {msg: 'Помилка збереження налаштувань'});
            }
        });
    });

    /* ====================================================================
     * ОБРОБНИК КНОПКИ "СКАСУВАТИ"
     * ====================================================================
     * runtime.notify('cancel', {}) повідомляє Studio, що користувач
     * скасував редагування. Studio закриває модальне вікно
     * без збереження змін.
     * ==================================================================== */
    $('.vladx-studio-cancel', element).on('click', function() {
        runtime.notify('cancel', {});
    });
}
