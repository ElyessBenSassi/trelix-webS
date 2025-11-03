console.log("Question Dynamic Options JS Loaded");
document.addEventListener('DOMContentLoaded', function () {
    const typeSelect = document.getElementById('id_question_type');
    const optionsField = document.getElementById('id_options');
    const correctAnswerField = document.getElementById('id_correct_answer').closest('.form-row');

    // Create the dynamic options UI
    const wrapper = document.createElement('div');
    wrapper.id = 'options-wrapper';
    wrapper.style.marginTop = '10px';
    wrapper.innerHTML = `
        <label><strong>Options</strong></label>
        <div id="options-container"></div>
        <button type="button" class="add-option-btn">+ Add Option</button>
    `;
    optionsField.parentElement.appendChild(wrapper);

    const optionsContainer = wrapper.querySelector('#options-container');
    const addBtn = wrapper.querySelector('.add-option-btn');

    // Load existing options (if editing)
    let options = [];
    try {
        options = JSON.parse(optionsField.value || '[]');
    } catch (e) {
        options = [];
    }
    renderOptions();

    addBtn.addEventListener('click', () => {
        options.push('');
        renderOptions();
    });

    function renderOptions() {
        optionsContainer.innerHTML = '';
        options.forEach((opt, i) => {
            const div = document.createElement('div');
            div.classList.add('option-row');
            div.innerHTML = `
                <input type="text" value="${opt}" placeholder="Option ${i + 1}" class="option-input"/>
                <button type="button" class="remove-option-btn">✖</button>
            `;
            optionsContainer.appendChild(div);

            div.querySelector('.remove-option-btn').addEventListener('click', () => {
                options.splice(i, 1);
                renderOptions();
            });

            div.querySelector('.option-input').addEventListener('input', (e) => {
                options[i] = e.target.value;
                optionsField.value = JSON.stringify(options);
            });
        });

        optionsField.value = JSON.stringify(options);
    }

    // Show or hide options based on type
    function toggleFields() {
        if (typeSelect.value === 'MCQ') {
            wrapper.style.display = '';
            correctAnswerField.querySelector('label').textContent = 'Correct Option';
        } else {
            wrapper.style.display = 'none';
            correctAnswerField.querySelector('label').textContent = 'Correct Answer';
        }
    }

    typeSelect.addEventListener('change', toggleFields);
    toggleFields();
});
