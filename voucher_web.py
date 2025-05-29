
import os
import random
import string
import smtplib
import pandas as pd
from datetime import datetime
from flask import Flask, request, render_template, redirect
from email.mime.text import MIMEText
from PIL import Image
import pytesseract

# === KONFIGURASI ===
EMAIL_PENGIRIM = "oneselltulungagung@gmail.com"
APP_PASSWORD = "ISI_APP_PASSWORD_KAMU"
EXCEL_FILE = "data_klaim.xlsx"
AKUN_IG = "dihemarttulungagung"
BATAS_KLAIM = 50

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# === SETUP FLASK ===
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === FUNGSI BANTUAN ===
def generate_voucher_code():
    return "DIHE-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_text_in_image(image_path, keywords):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image).lower()
    return all(keyword in text for keyword in keywords)

def has_profile_pic_bottom_right(image_path):
    image = Image.open(image_path)
    width, height = image.size
    bottom_right = image.crop((width - 150, height - 150, width, height))
    gray = bottom_right.convert('L')
    colors = gray.getcolors()
    if not colors:
        return False
    return len(colors) > 5  # heuristik: ada variasi warna berarti ada foto profil

def send_email_voucher(recipient_email, voucher_code):
    subject = "Kode Voucher DIHEMART"
    body = f"""Hai, terima kasih telah mengikuti Instagram kami!

Berikut kode voucher diskon Rp10.000 untuk kamu:
🔑 {voucher_code}

Gunakan saat belanja ya!
Salam, DIHEMART"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_PENGIRIM
    msg["To"] = recipient_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_PENGIRIM, APP_PASSWORD)
        server.send_message(msg)

# === ROUTE ===
@app.route("/", methods=["GET", "POST"])
def klaim():
    if request.method == "POST":
        email = request.form["email"].strip()
        file = request.files["screenshot"]

        if not file or not allowed_file(file.filename):
            return "❌ File tidak valid. Harus JPG/PNG."

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        df = pd.read_excel(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else pd.DataFrame(columns=["Email", "Kode", "Waktu", "Status"])

        if len(df) >= BATAS_KLAIM:
            return "⚠️ Kupon sudah habis."

        if email in df["Email"].values:
            return "⚠️ Email ini sudah pernah klaim."

        if not check_text_in_image(filepath, ["mengikuti", AKUN_IG]):
            return "❌ Screenshot tidak menunjukkan bahwa kamu follow akun kami."

        if not has_profile_pic_bottom_right(filepath):
            return "❌ Screenshot tidak menunjukkan akun milik sendiri (foto profil tidak terlihat)."

        kode = generate_voucher_code()
        send_email_voucher(email, kode)

        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[len(df)] = [email, kode, waktu, "Klaim Berhasil"]
        df.to_excel(EXCEL_FILE, index=False)

        return f"✅ Berhasil! Kode voucher dikirim ke {email}"

    return render_template("form.html")

# === JALANKAN ===
if __name__ == "__main__":
    app.run(debug=True)
