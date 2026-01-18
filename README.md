# Face Crypto: Privacy Protection & Encryption System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/framework-Flask-green)
![OpenCV](https://img.shields.io/badge/library-OpenCV-red)
![Security](https://img.shields.io/badge/security-AES--GCM-orange)

**Face Crypto** adalah aplikasi berbasis web yang menggabungkan teknik Pengolahan Citra Digital (Digital Image Processing) dan Kriptografi Modern untuk melindungi privasi biometrik wajah. Sistem ini menawarkan solusi hibrida: menyembunyikan identitas wajah untuk konsumsi publik (melalui blurring) sekaligus mengamankan file asli agar dapat dipulihkan kembali oleh pemiliknya (melalui enkripsi).

---

## 📖 Latar Belakang

Di era digital saat ini, privasi menjadi isu yang sangat krusial. Maraknya penyebaran foto di media sosial meningkatkan risiko penyalahgunaan data biometrik wajah, seperti *identity theft* dan *deepfake*.

Metode perlindungan konvensional seperti **blurring** atau **pixelation** memiliki kelemahan fatal: sifatnya **irreversible** (tidak dapat dibalik). Setelah foto di-blur, informasi asli hilang permanen, sehingga pemilik foto kehilangan akses ke arsip aslinya jika tidak memiliki cadangan terpisah.

**Face Crypto hadir untuk memecahkan dilema tersebut dengan menyediakan dua layer perlindungan:**
1.  **Visual Privacy:** Tampilan publik yang aman (wajah disamarkan).
2.  **Data Security:** Penyimpanan file asli yang terenkripsi dan *reversible* (dapat didekripsi).

---

## 🚀 Fitur Utama

Sistem ini mengintegrasikan empat komponen teknologi utama:

1.  [cite_start]**Face Detection (Haar Cascade)** [cite: 51, 56]
    * Mendeteksi lokasi wajah secara otomatis menggunakan algoritma *Viola-Jones* (Haar Cascade Classifier).
    * Menentukan *Region of Interest* (ROI) yang akan diproses.

2.  [cite_start]**Visualisasi Edge Detection (Canny)** [cite: 71, 78]
    * Menganalisis struktur geometris wajah menggunakan algoritma Canny.
    * Menampilkan kontur wajah untuk keperluan analisis fitur tanpa menampilkan identitas jelas.

3.  [cite_start]**Privacy Protection (Gaussian Blur)** [cite: 58, 60]
    * Menerapkan filter *Gaussian Blur* hanya pada area wajah yang terdeteksi.
    * Hasil blur digunakan untuk keperluan *sharing* publik yang aman.

4.  [cite_start]**Secure Storage (AES-GCM Encryption)** [cite: 80, 90]
    * Mengenkripsi *raw bytes* citra asli menggunakan algoritma **AES-GCM** (Advanced Encryption Standard - Galois/Counter Mode).
    * Menggunakan **PBKDF2** untuk *key derivation* dari password pengguna.
    * Menghasilkan file `.enc` yang menjamin kerahasiaan (*confidentiality*) dan integritas (*integrity*) data.

---

## 🛠️ Teknologi yang Digunakan

* **Bahasa Pemrograman:** Python 3.x
* **Web Framework:** Flask
* **Computer Vision:** OpenCV (`cv2`), NumPy
* **Kriptografi:** `cryptography.hazmat`, `hashlib`
* **Frontend:** HTML5, CSS3 (Modern Glassmorphism UI)

---

## 📸 Screenshots



| Halaman Encrypt | Halaman Decrypt |
|:---:|:---:|
| <img width="1452" height="890" alt="image" src="https://github.com/user-attachments/assets/ed9d67b0-edd1-49c0-b656-5fc99fc9304f" />  |<img width="959" height="866" alt="image" src="https://github.com/user-attachments/assets/32521ffb-c8d7-4851-ad34-8f137bdf7653" />  |



---
