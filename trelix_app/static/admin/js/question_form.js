document.addEventListener('DOMContentLoaded', function() {
    const typeSelect = document.getElementById('id_question_type');
    const optionsField = document.getElementById('id_options').closest('.form-row');
    const correctAnswerField = document.getElementById('id_correct_answer').closest('.form-row');

    function toggleFields() {
        if (typeSelect.value === 'MCQ') {
            optionsField.style.display = '';
            correctAnswerField.querySelector('label').textContent = 'Correct Option';
        } else {
            optionsField.style.display = 'none';
            correctAnswerField.querySelector('label').textContent = 'Correct Answer';
        }
    }

    if (typeSelect) {
        toggleFields();
        typeSelect.addEventListener('change', toggleFields);
    }
});
