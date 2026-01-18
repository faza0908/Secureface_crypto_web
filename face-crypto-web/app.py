import os
import uuid
import base64  
import hashlib
from flask import Flask, render_template, request, url_for, send_file
import numpy as np
import cv2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Folder output untuk menyimpan hasil pemrosesan (edge/blur/decrypt + file .enc)
OUT_DIR = os.path.join("static", "output")
os.makedirs(OUT_DIR, exist_ok=True)

# Memakai Haar Cascade bawaan OpenCV untuk deteksi wajah frontal
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def imdecode_image(file_bytes: bytes):
    """
    Mengubah bytes file (hasil upload / hasil decrypt) menjadi image BGR OpenCV.
    - bytes -> numpy array -> cv2.imdecode
    """
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def imwrite_png(path: str, img):
    """
    Menyimpan image OpenCV ke disk.
    Catatan: nama fungsi 'imwrite_png' tapi cv2.imwrite akan mengikuti ekstensi file yang diberikan.
    """
    cv2.imwrite(path, img)

def detect_faces(img_bgr):
    """
    Deteksi wajah dari gambar BGR.
    - Konversi ke grayscale agar deteksi Haar cascade lebih akurat
    - detectMultiScale mengembalikan list bounding box (x, y, w, h)
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,   # skala pencarian (semakin kecil semakin teliti tapi lebih lambat)
        minNeighbors=5,    # semakin besar semakin ketat (mengurangi false positive)
        minSize=(80, 80)   # minimal ukuran wajah yang dianggap valid
    )
    return faces

def make_edge_visual(img_bgr, faces):
    """
    Membuat visualisasi tepi (edge) menggunakan Canny.
    Lalu menambahkan kotak putih pada area wajah (hasil deteksi) sebagai highlight.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Deteksi tepi memakai Canny (threshold bawah=80, atas=160)
    edges = cv2.Canny(gray, 80, 160)

    # Konversi edges (1 channel) menjadi BGR agar mudah digambar rectangle
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    out = edges_bgr.copy()
    for (x, y, w, h) in faces:
        # Gambar kotak pada wajah yang terdeteksi
        cv2.rectangle(out, (x, y), (x + w, y + h), (255, 255, 255), 2)
    return out

def blur_faces(img_bgr, faces):
    """
    Blur area wajah yang terdeteksi.
    - Jika tidak ada wajah terdeteksi: fallback blur seluruh gambar (untuk privasi).
    - GaussianBlur kernel (41,41) cukup kuat untuk menutupi detail wajah.
    """
    out = img_bgr.copy()

    if len(faces) == 0:
        # Fallback: blur seluruh gambar bila wajah tidak terdeteksi
        return cv2.GaussianBlur(out, (41, 41), 0)

    for (x, y, w, h) in faces:
        # Ambil ROI (region of interest) area wajah
        roi = out[y:y+h, x:x+w]

        # Blur ROI, lalu tempelkan kembali ke gambar utama
        roi_blur = cv2.GaussianBlur(roi, (41, 41), 0)
        out[y:y+h, x:x+w] = roi_blur

    return out

def kdf_pbkdf2(password: str, salt: bytes, iterations: int = 200_000) -> bytes:
    """
    KDF (Key Derivation Function) untuk membentuk key 32 byte dari password.
    - PBKDF2-HMAC-SHA256
    - iterations tinggi (200k) untuk memperlambat brute force
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=32
    )

def encrypt_bytes(plain: bytes, password: str) -> bytes:
    """
    Enkripsi bytes mentah menggunakan AES-GCM.
    Format output:
      b'KF1' + salt(16) + nonce(12) + ciphertext(+tag)
    - KF1 = header signature agar kita tahu format file valid
    - salt = untuk PBKDF2 (membuat key unik tiap file)
    - nonce = IV 12 byte (standar AES-GCM)
    - ct = ciphertext + authentication tag (dihasilkan AESGCM.encrypt)
    """
    salt = os.urandom(16)
    key = kdf_pbkdf2(password, salt)

    nonce = os.urandom(12)
    aesgcm = AESGCM(key)

    ct = aesgcm.encrypt(nonce, plain, None)
    return b"KF1" + salt + nonce + ct

def decrypt_bytes(blob: bytes, password: str) -> bytes:
    """
    Dekripsi file terenkripsi (format KF1).
    - Validasi panjang minimal dan header
    - Ambil salt, nonce, ciphertext
    - Derive key dari password + salt
    - AESGCM.decrypt akan error jika password salah / data corrupt (tag mismatch)
    """
    if len(blob) < 3 + 16 + 12:
        raise ValueError("File terlalu pendek / format tidak valid.")
    if blob[:3] != b"KF1":
        raise ValueError("Header tidak valid (bukan file .enc dari app ini).")

    salt = blob[3:19]
    nonce = blob[19:31]
    ct = blob[31:]

    key = kdf_pbkdf2(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)

@app.route("/", methods=["GET"])
def index():
    """
    Halaman utama: render form upload gambar + form decrypt .enc.
    """
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    """
    Endpoint untuk:
    1) menerima gambar upload
    2) deteksi wajah
    3) buat output edge visualization
    4) blur wajah untuk preview privasi
    5) enkripsi file gambar original (raw bytes) menjadi .enc
    """
    file = request.files.get("image")
    password = request.form.get("password", "").strip()

    # Validasi input dasar
    if not file or file.filename == "":
        return render_template("index.html", error="File gambar belum dipilih.")
    if not password:
        return render_template("index.html", error="Password enkripsi wajib diisi.")

    raw = file.read()
    img = imdecode_image(raw)

    # Pastikan file memang gambar valid
    if img is None:
        return render_template("index.html", error="Gagal membaca gambar. Pastikan file gambar valid (jpg/png).")

    # 1) Deteksi wajah
    faces = detect_faces(img)

    # 2) Buat hasil edges + highlight wajah
    edge_img = make_edge_visual(img, faces)

    # 3) Buat preview blur wajah (privasi)
    blur_img = blur_faces(img, faces)

    # Token unik untuk nama file output
    token = uuid.uuid4().hex

    # Path output
    edge_path = os.path.join(OUT_DIR, f"{token}_edge.png")
    blur_path = os.path.join(OUT_DIR, f"{token}_blur.png")
    enc_path = os.path.join(OUT_DIR, f"{token}.enc")

    # Simpan file preview (PNG) ke disk
    imwrite_png(edge_path, edge_img)
    imwrite_png(blur_path, blur_img)

    # Enkripsi bytes gambar original (raw) lalu simpan jadi file .enc
    enc_blob = encrypt_bytes(raw, password)
    with open(enc_path, "wb") as f:
        f.write(enc_blob)

    # Render halaman dengan URL hasil preview + link download .enc
    return render_template(
        "index.html",
        edge_url=url_for("static", filename=f"output/{token}_edge.png"),
        blur_url=url_for("static", filename=f"output/{token}_blur.png"),
        enc_download=url_for("download_enc", token=token),
        face_count=len(faces),
    )

@app.route("/download/<token>.enc", methods=["GET"])
def download_enc(token):
    """
    Download file .enc berdasarkan token.
    """
    enc_path = os.path.join(OUT_DIR, f"{token}.enc")
    return send_file(enc_path, as_attachment=True, download_name=f"{token}.enc")

@app.route("/decrypt", methods=["POST"])
def decrypt():
    """
    Endpoint untuk:
    1) menerima file .enc
    2) decrypt menggunakan password
    3) decode hasil decrypt menjadi gambar
    4) simpan sebagai PNG untuk preview
    """
    file = request.files.get("encfile")
    password = request.form.get("password_dec", "").strip()

    # Validasi input dasar
    if not file or file.filename == "":
        return render_template("index.html", error="File .enc belum dipilih.")
    if not password:
        return render_template("index.html", error="Password decrypt wajib diisi.")

    blob = file.read()

    # Coba decrypt
    try:
        plain = decrypt_bytes(blob, password)
    except Exception as e:
        # Jika password salah / file rusak / format salah
        return render_template("index.html", error=f"Decrypt gagal: {str(e)}")

    # Hasil decrypt berupa bytes gambar original
    img = imdecode_image(plain)
    if img is None:
        # Kalau plain bukan file gambar valid (misal input .enc bukan dari sistem ini)
        return render_template("index.html", error="Decrypt berhasil, tapi hasilnya bukan gambar yang bisa dibaca.")

    # Simpan preview hasil decrypt
    token = uuid.uuid4().hex
    dec_path = os.path.join(OUT_DIR, f"{token}_decrypted.png")
    imwrite_png(dec_path, img)

    return render_template(
        "index.html",
        decrypted_url=url_for("static", filename=f"output/{token}_decrypted.png"),
    )

if __name__ == "__main__":
    # debug=True: auto reload saat perubahan kode (untuk development)
    app.run(debug=True)