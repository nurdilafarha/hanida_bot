import telebot
import requests
import difflib
import os
import os
import gdown
import zipfile
from dotenv import load_dotenv 
from transformers import AutoModelForQuestionAnswering, BertTokenizerFast, pipeline

load_dotenv()
token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(token)

model_zip_path = "indobert-qa-new.zip"
output_dir = "indobert-qa"

# Hanya download kalau belum ada
if not os.path.exists(output_dir):
    # ID Google Drive kamu (shareable link ubah jadi ID saja)
    gdown.download(id="14uhVs6A4Z_3Ocn_uMfL_5aJ5LFoB5ugR", output=model_zip_path, quiet=False)
    with zipfile.ZipFile(model_zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)


MODEL_DIR = "./indobert-qa"
model = AutoModelForQuestionAnswering.from_pretrained(MODEL_DIR)
tokenizer = BertTokenizerFast.from_pretrained(MODEL_DIR)
qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

# Menu QA
menu_qa = {
    "1. Seputar Darah Haid": [
        "Definisi, dalil, dan hikmah haid",
        "Tanda balig, usia minimal, dan sifat darah haid",
        "Masa haid dan masa suci antara dua haid",
        "Darah haid saat hamil",
        "Kapan dihukumi haid dan suci"
    ],
    "2. Seputar Darah Nifas": [
        "Definisi, dalil, dan masa nifas",
        "Syarat nifas dan hukum darah terputus-putus",
        "Masa suci antara haid dan nifas"
    ],
    "3. Seputar Darah Istihadah": [
        "Definisi dan dalil istihadah",
        "Hukum wanita istihadah",
        "Kewajiban wanita istihadah ketika akan salat",
        "Darah kuat dan lemah"
    ],
    "4. 7 Keadaan Istihadah yang Menyertai Haid": [
        "Mubtada'ah mumayyizah",
        "Mubtada'ah Ghoiru Mumayyizah",
        "Mu'tadah mumayyizah",
        "Mu'tadah Ghoiru Mumayyzah",
        "Mutahayyiroh Muthlaqoh",
        "Mutahayyiroh ingat waktu tetapi lupa jumlah hari",
        "Mutahayyiroh ingat jumlah hari tetapi lupa waktu",
        "Syarat tamyiz"
    ],
    "5. 7 Keadaan Istihadah yang Menyertai Nifas": [
        "Mubtada'ah mumayyizah",
        "Mubtada'ah Ghoiru Mumayyizah",
        "Mu'tadah mumayyizah",
        "Mu'tadah Ghoiru Mumayyzah",
        "Mutahayyiroh Muthlaqoh",
        "Mutahayyiroh ingat waktu tetapi lupa jumlah hari",
        "Mutahayyiroh ingat jumlah hari tetapi lupa waktu",
        "Syarat tamyiz"
    ],
    "6. Larangan saat Haid dan Nifas": [
        "Haram salat, kewajiban qada salat",
        "Haram tawaf, menetap di masjid, dan melewati masjid",
        "Haram menyentuh dan membawa mushaf",
        "Haram membaca alquran dengan niat mengaji",
        "Haram berpuasa, haram bercerai",
        "Haram bersuci dengan niat beribadah",
        "Haram berhubungan suami istri",
    ],
    "7. Cairan kewanitaan, madzi, dan hukumnya": []
}

url = "https://raw.githubusercontent.com/nurdilafarha/QA_haid_nifas_istihadah/main/QA_dataset_after%20annotate.json"
response = requests.get(url)
raw_data = response.json()
all_data = raw_data["data"]

# === FUNGSI AMBIL KONTEKS ===
def ambil_konteks(title):
    all_title = [item.get("title", "") for item in all_data]
    kandidat = difflib.get_close_matches(title, all_title, n=1, cutoff=0.6)
    if kandidat:
        for item in all_data:
            if item.get("title", "") == kandidat[0]:
                return item["paragraphs"][0]["context"]
    return None

def jawaban_dari_chatbot(konteks_sumber, pertanyaan_pengguna):
    if not konteks_sumber.strip() or not pertanyaan_pengguna.strip():
        return "Konteks dan pertanyaan tidak boleh kosong.", 0.0
    try:
        hasil = qa_pipeline(
            question=pertanyaan_pengguna,
            context=konteks_sumber,
            max_answer_len=512  # atau bisa disesuaikan
        )
        return hasil['answer'], hasil['score']
    except Exception as e:
        return f"Error: {e}", 0.0

talk = 0
konteks_aktif = ""  # untuk simpan konteks pilihan user terakhir

@bot.message_handler(commands=['start'])
def welcome(message):
    global talk
    talk = 1  # Set mode ke pemilihan menu utama

    daftar_menu = "\n".join([f"{i+1}. {menu.split('. ', 1)[1]}" for i, menu in enumerate(menu_qa.keys())])
    pesan = (
        "🕌 Selamat datang di Chatbot Haid, Nifas, Istihadah! \n\n"
        "Silahkan pilih menu untuk bertanya\n"
        f"{daftar_menu}\n\n"
        "Ketik angka 1–7\n\n"
        "Ketik /stop untuk mengakhiri sesi"
    )
    bot.reply_to(message, pesan)

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    global talk
    bot.reply_to(message, "🛑 Terima kasih telah menggunakan Chatbot Haid, Nifas, Istihadah\n\nKetik /start jika ingin memulai kembali.")
    talk = 0

talk_submenus = []
talk_menu_judul = ""

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global talk, konteks_aktif
    global talk_submenus, talk_menu_judul

    if talk == 0:
        return bot.reply_to(message, "Halo! Ketik /start untuk memulai.")

    teks = message.text.strip().lower()

    # Stop bot
    if teks in ["stop"]:
        return stop_bot(message)

    elif teks in ["mundur"]:
        if talk == 3:  # lagi di sesi tanya-jawab
            talk = 21
            daftar_sub = "\n".join([f"{i+1}. {submenu}" for i, submenu in enumerate(talk_submenus)])
            return bot.reply_to(message, f"⬅️ Ketik angka untuk pilih menu:\n\n{daftar_sub}\n\nKetik /stop untuk mengakhiri sesi\nKetik 'ganti' untuk memilih menu lain\nKetik 'mundur' untuk kembali ke menu sebelumnya")

        elif talk == 21:  # lagi di submenu
            return welcome(message)

    # Kembali ke menu utama
    if teks == "ganti":
        talk = 1
        return welcome(message)

    # =======================
    if talk == 1:
        # pilih menu utama
        try:
            pilihan = int(teks)
            menu_list = list(menu_qa.keys())
            if 1 <= pilihan <= len(menu_list):
                talk = 2
                talk_menu = menu_list[pilihan-1]
                bot.reply_to(message, f"Kamu memilih: {talk_menu}\n\n")

                submenus = menu_qa[talk_menu]
                if not submenus:
                    konteks_aktif = ambil_konteks(talk_menu.split(". ", 1)[1])
                    bot.reply_to(message, "Silahkan ketik pertanyaan kamu")
                    talk = 3
                else:
                    daftar_sub = "\n".join([f"{i+1}. {submenu}" for i, submenu in enumerate(submenus)])
                    bot.reply_to(message, f"Ketik angka untuk pilih menu:\n\n{daftar_sub}\n\nKetik /stop untuk mengakhiri sesi\nKetik 'ganti' untuk memilih menu lain\nKetik 'mundur' untuk kembali ke menu sebelumnya")
                    talk = 21
                    talk_submenus = submenus
                    talk_menu_judul = talk_menu
            else:
                bot.reply_to(message, "❌ Menu tidak tersedia. Pilih angka 1–7.")
        except:
            bot.reply_to(message, "❌ Masukkan angka yang valid.")

    elif talk == 21:
        # pilih submenu
        try:
            pilihan = int(teks)
            if 1 <= pilihan <= len(talk_submenus):
                submenu = talk_submenus[pilihan-1]
                if "Haid" in talk_menu_judul:
                    submenu += " (haid)"
                elif "Nifas" in talk_menu_judul:
                    submenu += " (nifas)"
                konteks_aktif = ambil_konteks(submenu)
                if konteks_aktif:
                    bot.reply_to(message, f"✅ Submenu dipilih: {submenu}\nSilahkan ketik pertanyaan kamu\n\nKetik /stop untuk mengakhiri sesi\nKetik 'ganti' untuk memilih menu lain\nKetik 'mundur' untuk kembali ke menu sebelumnya")
                    talk = 3
                else:
                    bot.reply_to(message, "❌ Konteks tidak ditemukan.")
                    talk = 1
                    return welcome (message)
            else:
                bot.reply_to(message, "❌ Submenu tidak tersedia.")
        except:
            bot.reply_to(message, "❌ Masukkan angka yang valid.")

    elif talk == 3:
        # tanya jawab
        if not konteks_aktif:
            bot.reply_to(message, "❌ Konteks kosong. Ketik /tanya untuk mulai lagi.")
            return
        pertanyaan = message.text
        jawaban, skor = jawaban_dari_chatbot(konteks_aktif, pertanyaan)
        bot.reply_to(message, f"💬 Jawaban:\n{jawaban}\n\n\nSilahkan ketik pertanyaan lain\n\nKetik /stop untuk mengakhiri sesi\nKetik 'ganti' untuk memilih menu lain\nKetik 'mundur' untuk kembali ke menu sebelumnya")

bot.polling()



