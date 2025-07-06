from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import os
import piexif
import json
import uuid

# Inisialisasi aplikasi Flask
app = Flask(__name__)
# Mengaktifkan CORS untuk mengizinkan permintaan dari domain lain (frontend)
CORS(app)

# Menyiapkan direktori yang dibutuhkan saat aplikasi dimulai
CLEANED_FOLDER = 'static/cleaned'
RESULTS_FOLDER = 'static/results'
os.makedirs(CLEANED_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# --- Fungsi Helper ---
def get_readable_metadata(exif_dict):
    """Mengubah data EXIF mentah menjadi format yang lebih mudah dibaca."""
    metadata = {}
    for ifd_name in exif_dict:
        if exif_dict[ifd_name] is None:
            continue
        for tag_id, value in exif_dict[ifd_name].items():
            tag_name = piexif.TAGS[ifd_name].get(tag_id, {"name": str(tag_id)})["name"]
            if isinstance(value, bytes):
                try:
                    value = value.decode(errors='ignore')
                except Exception:
                    value = str(value)
            metadata[tag_name] = str(value)
    return metadata

def convert_to_degrees(value):
    """Mengonversi koordinat GPS dari format DMS ke desimal."""
    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    return d + (m / 60.0) + (s / 3600.0)
# --- Akhir Fungsi Helper ---


# --- Endpoint API ---

@app.route('/api/analyze', methods=['POST'])
def analyze_api():
    """Endpoint untuk menerima gambar, menganalisis, dan menyimpannya."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    original_filename = image_file.filename

    # Buat ID unik untuk setiap proses agar file tidak tumpang tindih
    unique_id = str(uuid.uuid4())
    temp_path = os.path.join(CLEANED_FOLDER, f"temp_{unique_id}_{original_filename}")
    image_file.save(temp_path)

    try:
        img = Image.open(temp_path)
        exif_data = img.info.get('exif')

        result_data = {
            "original_filename": original_filename,
            "metadata": {}, "has_metadata": False, "gps_link": None
        }

        if exif_data:
            exif_dict = piexif.load(exif_data)
            result_data["metadata"] = get_readable_metadata(exif_dict)
            result_data["has_metadata"] = bool(result_data["metadata"])
            
            if "GPS" in exif_dict and exif_dict["GPS"]:
                gps_ifd = exif_dict["GPS"]
                if piexif.GPSIFD.GPSLatitude in gps_ifd and piexif.GPSIFD.GPSLongitude in gps_ifd:
                    lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
                    lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
                    lat = convert_to_degrees(gps_ifd[piexif.GPSIFD.GPSLatitude])
                    lon = convert_to_degrees(gps_ifd[piexif.GPSIFD.GPSLongitude])
                    if lat_ref == 'S': lat = -lat
                    if lon_ref == 'W': lon = -lon
                    result_data["gps_link"] = f"https://www.google.com/maps?q={lat},{lon}"

        # Simpan gambar versi bersih tanpa metadata
        clean_name = f"cleaned_{unique_id}_{original_filename}"
        clean_path = os.path.join(CLEANED_FOLDER, clean_name)
        img.save(clean_path, "jpeg", exif=b'')
        os.remove(temp_path) # Hapus file sementara

        # Buat URL lengkap untuk diakses dari frontend
        result_data["clean_image_url"] = f"{request.host_url}download/{clean_name}"
        
        # Simpan hasil analisis sebagai file JSON yang terpisah
        result_id = f"{unique_id}_{original_filename}"
        result_json_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
        with open(result_json_path, 'w') as f:
            json.dump(result_data, f)
            
        # Kembalikan hanya ID uniknya ke frontend
        return jsonify({"result_id": result_id})

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

@app.route('/api/result/<result_id>')
def get_result(result_id):
    """Endpoint untuk mengambil data hasil analisis berdasarkan ID."""
    result_json_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
    if not os.path.exists(result_json_path):
        return jsonify({"error": "Result not found"}), 404
    with open(result_json_path, 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/download/<filename>')
def download(filename):
    """Endpoint untuk mengunduh file gambar yang sudah bersih."""
    return send_file(os.path.join(CLEANED_FOLDER, filename), as_attachment=True)

# Perintah untuk menjalankan aplikasi Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
