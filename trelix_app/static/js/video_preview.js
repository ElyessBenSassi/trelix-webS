document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.querySelector('input[type="file"][name$="video"]');
    const previewContainer = document.getElementById('video_preview_container');

    if (fileInput && previewContainer) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const url = URL.createObjectURL(file);
                previewContainer.innerHTML = `<video width="300" height="200" controls><source src="${url}" type="${file.type}"></video>`;
            } else {
                previewContainer.innerHTML = "Aucune vidéo";
            }
        });
    }
});
