/* JavaScript for VladXBlock student_view. */
function VladXBlock(runtime, element) {

    var submitUrl = runtime.handlerUrl(element, 'submit_answer');
    var voteUrl = runtime.handlerUrl(element, 'vote');
    var getStateUrl = runtime.handlerUrl(element, 'get_state');
    var toggleModeUrl = runtime.handlerUrl(element, 'toggle_display_mode');
    var resetUrl = runtime.handlerUrl(element, 'reset_answer');
    var hintUrl = runtime.handlerUrl(element, 'show_hint');

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

    function showResult(data) {
        var $result = $('.vladx-result', element);
        var $message = $('.vladx-result-message', element);
        var $explanation = $('.vladx-explanation', element);

        $result.removeClass('vladx-correct vladx-incorrect vladx-error');

        if (data.error) {
            $result.addClass('vladx-error');
            $message.text(data.error);
            $explanation.text('');
        } else if (data.is_correct) {
            $result.addClass('vladx-correct');
            $message.text('Correct!');
            $explanation.text(data.explanation || '');
        } else {
            $result.addClass('vladx-incorrect');
            $message.text('Incorrect. Try again.');
            $explanation.text('');
        }
    }

    function updateVotes(data) {
        $('.vladx-upvote-count', element).text(data.upvotes);
        $('.vladx-downvote-count', element).text(data.downvotes);
    }

    $('.vladx-submit-btn', element).on('click', function() {
        var answer = $('.vladx-answer-input', element).val();
        $.ajax({
            type: "POST",
            url: submitUrl,
            data: JSON.stringify({ answer: answer }),
            success: function(response) {
                if (response.success) {
                    showResult(response);
                    updateAttemptsAndScore(response);
                    $('.vladx-total-sub-count', element).text(response.total_submissions);
                    if (response.attempts_used >= response.max_attempts) {
                        $('.vladx-submit-btn', element).prop('disabled', true);
                    }
                } else {
                    showResult({ error: response.error });
                }
            }
        });
    });

    $('.vladx-upvote', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: voteUrl,
            data: JSON.stringify({ vote_type: 'up' }),
            success: function(response) {
                if (response.success) { updateVotes(response); }
            }
        });
    });

    $('.vladx-downvote', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: voteUrl,
            data: JSON.stringify({ vote_type: 'down' }),
            success: function(response) {
                if (response.success) { updateVotes(response); }
            }
        });
    });

    $('.vladx-toggle-mode', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: toggleModeUrl,
            data: JSON.stringify({}),
            success: function(response) {
                $('.vladx-block', element).attr('data-mode', response.display_mode);
                $('.vladx-toggle-mode', element).text(response.display_mode);
            }
        });
    });

    $('.vladx-reset-btn', element).on('click', function() {
        $.ajax({
            type: "POST",
            url: resetUrl,
            data: JSON.stringify({}),
            success: function(response) {
                if (response.success) {
                    $('.vladx-answer-input', element).val('');
                    $('.vladx-result', element).removeClass('vladx-correct vladx-incorrect vladx-error');
                    $('.vladx-attempts-used', element).text('0');
                    $('.vladx-score-value', element).text('0.0');
                    $('.vladx-submit-btn', element).prop('disabled', false);
                    $('.vladx-hint-text', element).removeClass('vladx-visible').text('');
                } else {
                    alert(response.error);
                }
            }
        });
    });

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

    $(function() {
        $.ajax({
            type: "POST",
            url: getStateUrl,
            data: JSON.stringify({}),
            success: function(state) {
                updateAttemptsAndScore(state);
                updateVotes(state);
                $('.vladx-block', element).attr('data-mode', state.display_mode);
                $('.vladx-toggle-mode', element).text(state.display_mode);
                if (state.attempts_used >= state.max_attempts) {
                    $('.vladx-submit-btn', element).prop('disabled', true);
                }
                if (state.is_submitted && state.student_answer) {
                    $('.vladx-answer-input', element).val(state.student_answer);
                }
                
                if (state.voted) {
                    $element.find('.vladx-upvote').prop('disabled', true);
                    $element.find('.vladx-downvote').prop('disabled', true);
                }
            }
        });
    });
}
