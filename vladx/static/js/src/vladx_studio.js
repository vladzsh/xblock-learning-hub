/* ============================================================================
 * JavaScript для представления Studio (studio_view) VladX Learning Hub
 * ============================================================================
 *
 * ВАЖНО ДЛЯ XBLOCK-РАЗРАБОТЧИКА:
 *
 * Studio -- приложение Open edX для создания курсов.
 * Это представление открывается при нажатии "Редактировать" (Edit) на блоке.
 *
 * Ключевые отличия от student_view JavaScript:
 *
 * 1. Для сохранения настроек используется обработчик save_settings.
 *
 * 2. После успешного сохранения ОБЯЗАТЕЛЬНО вызвать:
 *    runtime.notify('save', {state: 'end'})
 *    Это сообщает Studio, что редактирование завершено, и Studio закрывает
 *    модальное окно редактирования.
 *
 * 3. Для отмены вызвать:
 *    runtime.notify('cancel', {})
 *    Studio закроет окно без сохранения.
 *
 * 4. Имя функции 'VladXStudio' должно совпадать с аргументом
 *    frag.initialize_js('VladXStudio') в Python-методе studio_view().
 * ============================================================================ */

function VladXStudio(runtime, element) {

    /* URL обработчика сохранения настроек на сервере */
    var saveUrl = runtime.handlerUrl(element, 'save_settings');

    /* ====================================================================
     * ИНИЦИАЛИЗАЦИЯ ФОРМЫ
     * ====================================================================
     * Checkbox в HTML получает значение как строку "True"/"False" через
     * data-value атрибут (потому что Python bool рендерится так в шаблоне).
     * Здесь мы конвертируем строку в состояние checked.
     * ==================================================================== */
    var $allowReset = $('#vladx-allow-reset', element);
    $allowReset.prop('checked', $allowReset.data('value') === 'True');

    /* ====================================================================
     * ОБРАБОТЧИК КНОПКИ "СОХРАНИТЬ"
     * ====================================================================
     * 1. Собираем значения из формы
     * 2. Отправляем POST-запрос к обработчику save_settings
     * 3. При успехе -- вызываем runtime.notify('save', {state: 'end'})
     * ==================================================================== */
    $('.vladx-studio-save', element).on('click', function() {
        /* Собираем данные из всех полей формы */
        var data = {
            /* String поле (Scope.settings) */
            display_name: $('#vladx-display-name', element).val(),
            /* String поле (Scope.content) */
            question_text: $('#vladx-question', element).val(),
            /* String поле (Scope.content) */
            correct_answer: $('#vladx-correct-answer', element).val(),
            /* String поле (Scope.content) */
            explanation: $('#vladx-explanation', element).val(),
            /* Integer поле (Scope.settings) -- конвертируется в int на сервере */
            max_attempts: $('#vladx-max-attempts', element).val(),
            /* Float поле (Scope.settings) -- конвертируется в float на сервере */
            weight: $('#vladx-weight', element).val(),
            /* Boolean поле (Scope.settings) -- checkbox.is(':checked') возвращает boolean */
            allow_reset: $('#vladx-allow-reset', element).is(':checked')
        };

        $.ajax({
            type: "POST",
            url: saveUrl,
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    /*
                     * runtime.notify('save', {state: 'end'}) -- ОБЯЗАТЕЛЬНЫЙ вызов.
                     * Без него Studio не узнает, что редактирование завершено,
                     * и модальное окно останется открытым.
                     *
                     * Варианты state:
                     *   'start' -- начало сохранения (можно показать индикатор загрузки)
                     *   'end'   -- сохранение завершено (Studio закрывает окно)
                     */
                    runtime.notify('save', {state: 'end'});
                }
            },
            error: function() {
                /* В случае ошибки -- уведомляем пользователя */
                runtime.notify('error', {msg: 'Ошибка сохранения настроек'});
            }
        });
    });

    /* ====================================================================
     * ОБРАБОТЧИК КНОПКИ "ОТМЕНА"
     * ====================================================================
     * runtime.notify('cancel', {}) сообщает Studio, что пользователь
     * отменил редактирование. Studio закрывает модальное окно
     * без сохранения изменений.
     * ==================================================================== */
    $('.vladx-studio-cancel', element).on('click', function() {
        runtime.notify('cancel', {});
    });
}
