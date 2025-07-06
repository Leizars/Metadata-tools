document.addEventListener('DOMContentLoaded', () => {
    const fileUpload = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name-display');
    const uploadForm = document.getElementById('upload-form');

    fileUpload.addEventListener('change', function() {
        fileNameDisplay.textContent = this.files.length > 0 ? this.files[0].name : '';
    });

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (fileUpload.files.length === 0) {
            alert('Please select an image first!');
            return;
        }

        const button = event.target.querySelector('button');
        button.disabled = true;
        button.textContent = 'ANALYZING...';

        const formData = new FormData();
        formData.append('image', fileUpload.files[0]);

        try {
            const response = await fetch('http://localhost:5000/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to analyze image.');
            
            const data = await response.json();
            if (data.result_id) {
                // Arahkan ke halaman hasil dengan membawa ID
                window.location.href = `result.html?id=${data.result_id}`;
            } else {
                throw new Error('Could not get result ID.');
            }

        } catch (error) {
            alert(error.message);
            button.disabled = false;
            button.textContent = 'UPLOAD';
        }
    });
});