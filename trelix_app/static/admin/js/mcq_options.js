(function($) {
    $(document).ready(function() {
        // Show/hide options when question type changes
        $('select[name="question_type"]').change(function() {
            var optionsField = $('.field-options');
            if ($(this).val() === 'MCQ') {
                optionsField.show();
            } else {
                optionsField.hide();
            }
        }).trigger('change');  // Trigger on page load
    });
})(django.jQuery);