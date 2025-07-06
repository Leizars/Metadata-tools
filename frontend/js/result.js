document.addEventListener('DOMContentLoaded', async () => {
    // Ambil ID dari URL
    const params = new URLSearchParams(window.location.search);
    const resultId = params.get('id');

    const metadataContainer = document.getElementById('metadata-details');

    if (!resultId) {
        metadataContainer.innerHTML = '<p>🚫 Error: Result ID not found in URL.</p>';
        return;
    }

    try {
        // Minta data lengkap dari backend menggunakan ID
        const response = await fetch(`http://localhost:5000/api/result/${resultId}`);
        if (!response.ok) throw new Error('Could not fetch analysis results.');

        const data = await response.json();

        // Isi halaman dengan data yang diterima
        document.getElementById('original-filename').textContent = data.original_filename;

        metadataContainer.innerHTML = ''; // Kosongkan
        if (data.has_metadata) {
            const p = document.createElement('p');
            p.innerHTML = `✅ EXIF metadata found (${Object.keys(data.metadata).length} entries):`;
            metadataContainer.appendChild(p);

            const ul = document.createElement('ul');
            for (const key in data.metadata) {
                if (key !== "GPSInfo") { // Jangan tampilkan info mentah GPS
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${key}:</strong> ${data.metadata[key]}`;
                    ul.appendChild(li);
                }
            }
            metadataContainer.appendChild(ul);
            
            if (data.gps_link) {
                 const gpsP = document.createElement('p');
                 gpsP.innerHTML = `📍 Location detected: <a href="${data.gps_link}" target="_blank">View on Google Maps</a>`;
                 metadataContainer.appendChild(gpsP);
            }
        } else {
            const p = document.createElement('p');
            p.textContent = '🚫 No EXIF metadata was found.';
            metadataContainer.appendChild(p);
        }

        document.getElementById('cleaned-image').src = data.clean_image_url;
        document.getElementById('download-link').href = data.clean_image_url;

    } catch (error) {
        metadataContainer.innerHTML = `<p>🚫 Error: ${error.message}</p>`;
    }
});