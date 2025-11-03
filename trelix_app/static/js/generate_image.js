document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.generate-image-btn').forEach(btn => {
        btn.addEventListener('click', function () {

            const id = this.dataset.objId;
            const img = document.getElementById('generated-image-preview-' + id);
            const pathInput = document.getElementById('generated-image-path-' + id);

            img.style.display = 'block';
            img.src = '';
            img.alt = '⏳ Génération...';

            fetch('/evenements/generate-image/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ title: id })
            })
                .then(r => r.json())
                .then(data => {
                    if (data.image_url) {
                        img.src = data.image_url;
                        pathInput.value = data.image_path;
                        img.alt = '✅ Image générée';
                    } else {
                        img.alt = '❌ Erreur';
                    }
                });
        });
    });
});
