/* JavaScript for VladXBlock studio_view. */
function VladXStudio(runtime, element) {

    var saveUrl = runtime.handlerUrl(element, 'save_settings');

    var $allowReset = $('#vladx-allow-reset', element);
    $allowReset.prop('checked', $allowReset.data('value') === 'True');

    $('.vladx-studio-save', element).on('click', function() {
        var data = {
            display_name: $('#vladx-display-name', element).val(),
            question_text: $('#vladx-question', element).val(),
            correct_answer: $('#vladx-correct-answer', element).val(),
            explanation: $('#vladx-explanation', element).val(),
            max_attempts: $('#vladx-max-attempts', element).val(),
            weight: $('#vladx-weight', element).val(),
            allow_reset: $('#vladx-allow-reset', element).is(':checked')
        };

        $.ajax({
            type: "POST",
            url: saveUrl,
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    runtime.notify('save', {state: 'end'});
                }
            },
            error: function() {
                runtime.notify('error', {msg: 'Error saving settings'});
            }
        });
    });

    $('.vladx-studio-cancel', element).on('click', function() {
        runtime.notify('cancel', {});
    });
}
