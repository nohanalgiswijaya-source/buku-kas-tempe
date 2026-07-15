import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
# Library koneksi Google Sheets resmi dari Streamlit
from streamlit_gsheets import GSheetsConnection

# --- SETTING DASHBOARD (Harus paling atas) ---
st.set_page_config(page_title="BUKUDIGI - Catatan Keuangan Usaha", layout="wide")

st.title("BUKUDIGI - Buku Catatan Digital Keuangan Usahamu")
st.markdown("### *Kelola pemasukan dan pengeluaran dengan lebih rapi.*")

st.divider()

# =========================================================================
# CONFIG: HUBUNGKAN KE GOOGLE SHEETS
# =========================================================================
url_sheets = "https://docs.google.com/spreadsheets/d/1qtKhihSp1OiOdzIqlB7TOnnqn-Jlb6XlhVPDS_2ZyYI/edit?usp=sharing"

# Inisialisasi koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# =========================================================================
# HELPER: Bersihkan kolom teks agar aman dipakai .str.xxx()
# =========================================================================
def bersihkan_kolom_teks(df, kolom):
    """Pastikan kolom bertipe string murni (bukan object campuran/NaN/angka),
    supaya .str.lower() / .str.contains() tidak melempar AttributeError."""
    if kolom in df.columns:
        df[kolom] = df[kolom].fillna("").astype(str).str.strip()
    else:
        df[kolom] = ""
    return df

# =========================================================================
# FUNGSI DATABASE AKUN (Membaca & Menyimpan Pendaftaran Ke Google Sheets)
# =========================================================================
def load_akun_dari_sheets():
    try:
        df = conn.read(spreadsheet=url_sheets, worksheet="Akun", ttl=0)
        df = df.dropna(subset=["Nama UMKM"], how="all")
        df = bersihkan_kolom_teks(df, "Nama UMKM")
        df = bersihkan_kolom_teks(df, "Token Rahasia")
        # Buang baris yang nama-nya kosong setelah dibersihkan
        df = df[df["Nama UMKM"] != ""].reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame(columns=["Nama UMKM", "Token Rahasia"])

def simpan_akun_ke_sheets(df_baru):
    conn.update(spreadsheet=url_sheets, worksheet="Akun", data=df_baru)
    st.cache_data.clear()

# Inisialisasi Session State untuk menyimpan status login
if "login_umkm" not in st.session_state:
    st.session_state["login_umkm"] = None

# =========================================================================
# HALAMAN LOGIN & PENDAFTARAN (JIKA BELUM LOGIN)
# =========================================================================
if st.session_state["login_umkm"] is None:
    tab_masuk, tab_daftar = st.tabs(["🔑 Masuk Akun Usaha", "📝 Daftar Akun Usaha Baru"])

    # --- TAB MASUK ---
    with tab_masuk:
        st.subheader("Silakan masuk untuk melihat buku kas Anda")
        input_nama_masuk = st.text_input("Nama UMKM / Usaha Anda:", placeholder="Contoh: Tempe Koro Ibu Marni", key="login_nama")
        input_token_masuk = st.text_input("Token / PIN Rahasia Usaha:", type="password", placeholder="Masukkan PIN Anda...", key="login_pin")

        tombol_masuk = st.button("Buka dan Load Buku Kas", use_container_width=True, key="btn_login")

        if tombol_masuk:
            nama_clean = input_nama_masuk.strip()
            token_clean = input_token_masuk.strip()

            if not nama_clean or not token_clean:
                st.error("Nama UMKM dan Token/PIN tidak boleh kosong!")
            else:
                df_akun = load_akun_dari_sheets()
                if df_akun.empty:
                    st.error("Nama UMKM belum terdaftar! Silakan daftar baru di tab sebelah.")
                else:
                    # Cari akun di Google Sheets (kolom sudah dijamin string di load_akun_dari_sheets)
                    akun_cocok = df_akun[df_akun["Nama UMKM"].str.lower() == nama_clean.lower()]

                    if akun_cocok.empty:
                        st.error("Nama UMKM belum terdaftar! Silakan daftar baru di tab sebelah.")
                    else:
                        token_seharusnya = str(akun_cocok.iloc[0]["Token Rahasia"]).strip()
                        if token_seharusnya.endswith(".0"):
                            token_seharusnya = token_seharusnya[:-2]
                        if token_clean == token_seharusnya:
                            st.session_state["login_umkm"] = akun_cocok.iloc[0]["Nama UMKM"]
                            st.success(f"Login Sukses! Membuka data {st.session_state['login_umkm']}...")
                            st.rerun()
                        else:
                            st.error("Token / PIN salah! Akses ditolak.")

    # --- TAB DAFTAR ---
    with tab_daftar:
        st.subheader("Pendaftaran Akun Usaha Baru (Satu Akun untuk Satu HP/Toko)")
        input_nama_daftar = st.text_input("Nama UMKM / Usaha Baru:", placeholder="Contoh: Tempe Koro Ibu Marni", key="reg_nama")
        input_token_daftar = st.text_input("Buat Token / PIN Rahasia Usaha:", type="password", placeholder="Masukkan angka/huruf bebas...", key="reg_pin")

        tombol_daftar = st.button("Daftarkan Akun Baru", use_container_width=True, key="btn_reg")

        if tombol_daftar:
            nama_reg_clean = input_nama_daftar.strip()
            token_reg_clean = input_token_daftar.strip()

            if not nama_reg_clean or not token_reg_clean:
                st.error("Harap isi Nama UMKM dan Token/PIN baru Anda!")
            else:
                df_akun = load_akun_dari_sheets()
                # Cek apakah nama sudah dipakai
                if not df_akun.empty and nama_reg_clean.lower() in df_akun["Nama UMKM"].str.lower().values:
                    st.error("Nama UMKM ini sudah terdaftar! Gunakan nama lain atau silakan langsung masuk di tab sebelah.")
                else:
                    # Tambah ke dataframe akun
                    akun_baru = pd.DataFrame([{"Nama UMKM": nama_reg_clean, "Token Rahasia": token_reg_clean}])
                    df_akun_update = pd.concat([df_akun, akun_baru], ignore_index=True)

                    # Simpan ke Google Sheets
                    simpan_akun_ke_sheets(df_akun_update)
                    st.success(f"Pendaftaran Berhasil! Akun '{nama_reg_clean}' sekarang terdaftar permanen di Cloud. Silakan beralih ke tab 'Masuk Akun' untuk login.")

    st.stop()

# ==========================================
# HALAMAN UTAMA PEMBUKAAN (JIKA SUDAH LOG IN)
# ==========================================
umkm_terpilih = str(st.session_state["login_umkm"]).strip()

col_header, col_logout = st.columns([4, 1])
with col_header:
    st.markdown(f"### Selamat Datang Kembali, **{umkm_terpilih}**!")
with col_logout:
    if st.button("Keluar dan Kunci Kas", use_container_width=True):
        st.session_state["login_umkm"] = None
        states_to_clear = ["jumlah_dana_raw", "jumlah_dp_raw", "val_bayar_p", "val_bayar_u"]
        for key in states_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.info("Database Kas Terkunci Aman: Sinkronisasi Otomatis dengan Google Sheets Cloud")

# --- FUNGSI LOAD & SIMPAN DATABASE MENGGUNAKAN GOOGLE SHEETS ---
def load_data_offline():
    kolom = [
        "Nama UMKM", "Tanggal", "Keterangan Transaksi", "Jenis",
        "Kategori Spesifik", "Masuk (Rp)", "Keluar (Rp)",
        "Status Pembayaran", "Metode Pembayaran", "Harga Total Asli", "DP Awal"
    ]
    try:
        df = conn.read(spreadsheet=url_sheets, worksheet="Kas_Marni", ttl=0)
        df = df.dropna(subset=["Tanggal", "Keterangan Transaksi"], how="all")

        # Pastikan semua kolom wajib ada
        for k in kolom:
            if k not in df.columns:
                df[k] = "" if k not in ["Masuk (Rp)", "Keluar (Rp)", "Harga Total Asli", "DP Awal"] else 0

        # Bersihkan kolom teks yang sering dipakai .str.xxx() agar tidak AttributeError
        df = bersihkan_kolom_teks(df, "Nama UMKM")
        df = bersihkan_kolom_teks(df, "Keterangan Transaksi")
        df = bersihkan_kolom_teks(df, "Jenis")
        df = bersihkan_kolom_teks(df, "Kategori Spesifik")
        df = bersihkan_kolom_teks(df, "Status Pembayaran")
        df = bersihkan_kolom_teks(df, "Metode Pembayaran")

        return df
    except Exception:
        return pd.DataFrame(columns=kolom)

def simpan_data_offline(df_baru):
    # Buang kolom index internal "ID_Asli" atau "Saldo Sisa (Rp)" sebelum upload jika ada
    kolom_wajib = [
        "Nama UMKM", "Tanggal", "Keterangan Transaksi", "Jenis",
        "Kategori Spesifik", "Masuk (Rp)", "Keluar (Rp)",
        "Status Pembayaran", "Metode Pembayaran", "Harga Total Asli", "DP Awal"
    ]
    df_save = df_baru[kolom_wajib].copy()
    conn.update(spreadsheet=url_sheets, worksheet="Kas_Marni", data=df_save)
    st.cache_data.clear()

# Load semua data dari Sheets
df_all = load_data_offline()

# Upgrade path jika kolom "Nama UMKM" belum ada di file lama / kosong semua
if df_all.empty or (df_all["Nama UMKM"] == "").all():
    if not df_all.empty:
        df_all["Nama UMKM"] = "Tempe Koro Ibu Marni"

# Filter data khusus untuk UMKM yang sedang login saja (kolom sudah dijamin string)
df_keuangan = df_all[df_all["Nama UMKM"].str.lower() == umkm_terpilih.lower()].copy()

# Pastikan struktur kolom selalu lengkap
for col, default_val in [("Harga Total Asli", 0), ("DP Awal", 0)]:
    if col not in df_keuangan.columns:
        df_keuangan[col] = default_val

if not df_keuangan.empty:
    df_keuangan["Tanggal"] = pd.to_datetime(df_keuangan["Tanggal"], errors="coerce").dt.date
    df_keuangan["Masuk (Rp)"] = pd.to_numeric(df_keuangan["Masuk (Rp)"], errors="coerce").fillna(0)
    df_keuangan["Keluar (Rp)"] = pd.to_numeric(df_keuangan["Keluar (Rp)"], errors="coerce").fillna(0)
    df_keuangan["Harga Total Asli"] = pd.to_numeric(df_keuangan["Harga Total Asli"], errors="coerce").fillna(0)
    df_keuangan["DP Awal"] = pd.to_numeric(df_keuangan["DP Awal"], errors="coerce").fillna(0)
    if "Kategori Spesifik" in df_keuangan.columns:
        df_keuangan["Kategori Spesifik"] = df_keuangan["Kategori Spesifik"].astype(str).str.strip()

# Pembuatan Data Kumulatif & ID Asli database utama (df_all)
if not df_keuangan.empty:
    df_master = df_keuangan.copy()
    saldo_kumulatif = []
    saldo_sekarang = 0

    for idx, row in df_master.iterrows():
        saldo_sekarang += float(row["Masuk (Rp)"]) - float(row["Keluar (Rp)"])
        saldo_kumulatif.append(saldo_sekarang)

    df_master["Saldo Sisa (Rp)"] = saldo_kumulatif
    df_master["ID_Asli"] = df_master.index  # Menyimpan index asli dari df_all untuk proses hapus/edit
else:
    df_master = pd.DataFrame()

# --- MENU TAB UTAMA ---
tab1, tab2, tab3 = st.tabs(["Input dan Histori Buku Kas", "Pantau Utang dan Piutang", "Laporan Laba/Rugi dan Analisis Usaha"])

# ==========================================
# TAB 1: INPUT & HISTORI BUKU KAS
# ==========================================
with tab1:
    st.subheader("Catat Transaksi Baru")
    col1, col2, col3 = st.columns(3)

    with col1:
        tanggal = st.date_input("Tanggal Transaksi", datetime.now().date(), key="tgl_kas")
        jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran", "Modal"])

        if jenis == "Pemasukan":
            kategori_opsi = ["Penjualan Produk Utama", "Pendapatan Jasa / Komisi", "Penjualan Sampingan", "Lain-lain (Pemasukan)"]
        elif jenis == "Modal":
            kategori_opsi = ["Modal Awal Usaha", "Modal Tambahan Pemilik"]
        else:
            kategori_opsi = ["Bahan Baku / Stok Barang", "Operasional & Sewa Tempat", "Gaji & Upah Karyawan", "Alat & Perlengkapan Usaha", "Transportasi & Ongkir", "Lain-lain (Pengeluaran)"]

        kategori_spesifik = st.selectbox("Kategori Spesifik Usaha", kategori_opsi)

    with col2:
        keterangan = st.text_area("Keterangan Transaksi / Nama Pelanggan / Supplier", placeholder="Contoh: Pembelian ayam potong 10kg dari Pak Ali")

        if jenis == "Pemasukan":
            status_opsi = ["Lunas", "Belum Lunas / Piutang"]
            status_bayar = st.selectbox("Status Transaksi", status_opsi)
        elif jenis == "Modal":
            status_bayar = "Lunas / Masuk Kas"
        else:
            if kategori_spesifik == "Gaji & Upah Karyawan":
                status_bayar = "Dibayar (Lunas)"
                st.caption("Informasi: Status otomatis diset ke 'Dibayar (Lunas)' untuk Kategori Gaji.")
            else:
                status_opsi = ["Dibayar (Lunas)", "Bon / Utang Usaha"]
                status_bayar = st.selectbox("Status Transaksi", status_opsi)

        metode_bayar = st.selectbox("Metode Pembayaran", ["Tunai", "Transfer / QRIS", "Metode Lain"])

    with col3:
        if "jumlah_dana_raw" not in st.session_state:
            st.session_state["jumlah_dana_raw"] = ""

        input_dana_teks = st.text_input(
            "Harga Total Semua / Nilai Transaksi (Rp)",
            value=st.session_state["jumlah_dana_raw"],
            placeholder="Contoh: 150.000"
        )

        angka_polos = "".join([c for c in input_dana_teks if c.isdigit()])
        if angka_polos:
            harga_total_asli = int(angka_polos)
            teks_terformat = f"{harga_total_asli:,.0f}".replace(",", ".")
            if input_dana_teks != teks_terformat:
                st.session_state["jumlah_dana_raw"] = teks_terformat
                st.rerun()
        else:
            harga_total_asli = 0
            if input_dana_teks != "":
                st.session_state["jumlah_dana_raw"] = ""
                st.rerun()

        dp_awal = 0
        if jenis == "Pemasukan" and status_bayar == "Belum Lunas / Piutang":
            if "jumlah_dp_raw" not in st.session_state:
                st.session_state["jumlah_dp_raw"] = ""

            input_dp_teks = st.text_input("Jika Ada DP, Masukkan Nilainya (Rp) - Isi 0 Jika Tanpa DP", value=st.session_state["jumlah_dp_raw"])
            angka_dp_polos = "".join([c for c in input_dp_teks if c.isdigit()])
            if angka_dp_polos:
                dp_awal = int(angka_dp_polos)
                teks_dp_terformat = f"{dp_awal:,.0f}".replace(",", ".")
                if input_dp_teks != teks_dp_terformat:
                    st.session_state["jumlah_dp_raw"] = teks_dp_terformat
                    st.rerun()
            else:
                dp_awal = 0
                if input_dp_teks != "":
                    st.session_state["jumlah_dp_raw"] = ""
                    st.rerun()

        elif jenis == "Pengeluaran" and status_bayar == "Bon / Utang Usaha":
            if "jumlah_dp_utang_raw" not in st.session_state:
                st.session_state["jumlah_dp_utang_raw"] = ""

            input_dp_utang_teks = st.text_input("Sudah Dibayar Berapa Saat Ini (Rp) - Isi 0 Jika Belum Bayar Sama Sekali", value=st.session_state["jumlah_dp_utang_raw"])
            angka_dp_utang_polos = "".join([c for c in input_dp_utang_teks if c.isdigit()])
            if angka_dp_utang_polos:
                dp_awal = int(angka_dp_utang_polos)
                teks_dp_utang_terformat = f"{dp_awal:,.0f}".replace(",", ".")
                if input_dp_utang_teks != teks_dp_utang_terformat:
                    st.session_state["jumlah_dp_utang_raw"] = teks_dp_utang_terformat
                    st.rerun()
            else:
                dp_awal = 0
                if input_dp_utang_teks != "":
                    st.session_state["jumlah_dp_utang_raw"] = ""
                    st.rerun()

        submit_kas = st.button("Simpan Ke Buku Kas Cloud", use_container_width=True)

    if submit_kas:
        if keterangan.strip() == "":
            st.error("Harap isi Keterangan Transaksi / Nama Supplier agar tidak membingungkan pembukuan!")
        elif harga_total_asli <= 0:
            st.error("Harap masukkan Jumlah Uang Riil yang valid lebih besar dari 0!")
        elif dp_awal > harga_total_asli:
            st.error("Nilai DP tidak boleh melebihi Harga Total Asli transaksi!")
        else:
            if jenis in ["Pemasukan", "Modal"]:
                if jenis == "Pemasukan" and status_bayar == "Belum Lunas / Piutang":
                    masuk = dp_awal
                else:
                    masuk = harga_total_asli
                keluar = 0
            else:
                masuk = 0
                if jenis == "Pengeluaran" and status_bayar == "Bon / Utang Usaha":
                    keluar = dp_awal
                else:
                    keluar = harga_total_asli

            keterangan_final = keterangan
            if jenis == "Pemasukan" and status_bayar == "Belum Lunas / Piutang":
                keterangan_final = f"{keterangan} | TOTAL_AWAL:{harga_total_asli}"
            elif jenis == "Pengeluaran" and status_bayar == "Bon / Utang Usaha":
                keterangan_final = f"{keterangan} | TOTAL_AWAL:{harga_total_asli}"

            new_row = pd.DataFrame([{
                "Nama UMKM": umkm_terpilih,
                "Tanggal": str(tanggal),
                "Keterangan Transaksi": keterangan_final,
                "Jenis": jenis,
                "Kategori Spesifik": kategori_spesifik.strip(),
                "Masuk (Rp)": masuk,
                "Keluar (Rp)": keluar,
                "Status Pembayaran": status_bayar,
                "Metode Pembayaran": metode_bayar,
                "Harga Total Asli": harga_total_asli,
                "DP Awal": dp_awal
            }])

            df_update = pd.concat([df_all, new_row], ignore_index=True)
            simpan_data_offline(df_update)

            st.session_state["jumlah_dana_raw"] = ""
            if "jumlah_dp_raw" in st.session_state:
                st.session_state["jumlah_dp_raw"] = ""
            st.success("Transaksi berhasil disimpan permanen ke Google Sheets!")
            st.rerun()

    st.divider()

    if not df_master.empty:
        st.subheader("Ringkasan Saldo Buku Kas Anda")

        total_harga_semua_pemasukan = df_master[df_master["Jenis"] == "Pemasukan"]["Harga Total Asli"].sum()
        total_dp_masuk = df_master[df_master["Jenis"] == "Pemasukan"]["DP Awal"].sum()
        total_uang_masuk_kas = df_master["Masuk (Rp)"].sum()
        total_biaya_keluar_kas = df_master["Keluar (Rp)"].sum()
        sisa_kas_aktif = total_uang_masuk_kas - total_biaya_keluar_kas

        df_p_belum = df_master[(df_master["Jenis"] == "Pemasukan") & (df_master["Status Pembayaran"] == "Belum Lunas / Piutang")]
        total_piutang_jalan = 0
        for idx, row in df_p_belum.iterrows():
            kunci_cari = f"ID_REF:{row['ID_Asli']}"
            df_cicilan = df_all[df_all["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
            total_cicilan_masuk = df_cicilan["Masuk (Rp)"].sum()
            total_piutang_jalan += (row["Harga Total Asli"] - row["DP Awal"] - total_cicilan_masuk)

        df_u_belum = df_master[(df_master["Jenis"] == "Pengeluaran") & (df_master["Status Pembayaran"] == "Bon / Utang Usaha")]
        total_utang_jalan = 0
        for idx, row in df_u_belum.iterrows():
            kunci_cari = f"ID_REF:{row['ID_Asli']}"
            df_cicilan = df_all[df_all["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
            total_cicilan_keluar = df_cicilan["Keluar (Rp)"].sum()
            total_utang_jalan += (row["Harga Total Asli"] - row["DP Awal"] - total_cicilan_keluar)

        data_ringkasan = {
            "Total Semua Harga (Omzet Pemasukan)": [f"Rp {total_harga_semua_pemasukan:,.0f}".replace(",", ".")],
            "Total DP Masuk": [f"Rp {total_dp_masuk:,.0f}".replace(",", ".")],
            "Total Riil Masuk Ke Kas": [f"Rp {total_uang_masuk_kas:,.0f}".replace(",", ".")],
            "Total Riil Keluar Kas": [f"Rp {total_biaya_keluar_kas:,.0f}".replace(",", ".")],
            "Saldo Kas Toko Saat Ini": [f"Rp {sisa_kas_aktif:,.0f}".replace(",", ".")],
            "Total Piutang (Pelanggan Belum Bayar)": [f"Rp {total_piutang_jalan:,.0f}".replace(",", ".")],
            "Total Utang Toko (Bon ke Supplier)": [f"Rp {total_utang_jalan:,.0f}".replace(",", ".")]
        }
        st.table(pd.DataFrame(data_ringkasan))

        st.divider()

        st.write("### HISTORI DATA PEMASUKAN & MODAL")
        df_pemasukan = df_master[df_master["Jenis"].isin(["Pemasukan", "Modal"])].copy()
        if not df_pemasukan.empty:
            df_pemasukan.index = range(1, len(df_pemasukan) + 1)
            df_pemasukan.index.name = "No"
            kolom_in = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Harga Total Asli", "DP Awal", "Masuk (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pemasukan_v = df_pemasukan[kolom_in].copy()
            df_pemasukan_v["Tanggal"] = df_pemasukan_v["Tanggal"].astype(str)
            df_pemasukan_v["Keterangan Transaksi"] = df_pemasukan_v["Keterangan Transaksi"].apply(lambda x: str(x).split(" | TOTAL_AWAL:")[0])
            df_pemasukan_v["Harga Total Asli"] = df_pemasukan_v["Harga Total Asli"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pemasukan_v["DP Awal"] = df_pemasukan_v["DP Awal"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pemasukan_v["Masuk (Rp)"] = df_pemasukan_v["Masuk (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pemasukan_v["Saldo Sisa (Rp)"] = df_pemasukan_v["Saldo Sisa (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            st.dataframe(df_pemasukan_v, use_container_width=True)

        st.write("### HISTORI DATA PENGELUARAN & BEBAN NYATA")
        df_pengeluaran = df_master[df_master["Jenis"] == "Pengeluaran"].copy()
        if not df_pengeluaran.empty:
            df_pengeluaran.index = range(1, len(df_pengeluaran) + 1)
            df_pengeluaran.index.name = "No"
            kolom_out = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Harga Total Asli", "Keluar (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pengeluaran_v = df_pengeluaran[kolom_out].copy()
            df_pengeluaran_v["Tanggal"] = df_pengeluaran_v["Tanggal"].astype(str)
            df_pengeluaran_v["Keterangan Transaksi"] = df_pengeluaran_v["Keterangan Transaksi"].apply(lambda x: str(x).split(" | TOTAL_AWAL:")[0])
            df_pengeluaran_v["Harga Total Asli"] = df_pengeluaran_v["Harga Total Asli"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pengeluaran_v["Keluar (Rp)"] = df_pengeluaran_v["Keluar (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pengeluaran_v["Saldo Sisa (Rp)"] = df_pengeluaran_v["Saldo Sisa (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            st.dataframe(df_pengeluaran_v, use_container_width=True)

        st.markdown("---")
        st.markdown("### Panel Hapus Transaksi")
        pilihan_tabel_hapus = st.radio("Pilih sumber hapus data:", ["Tabel Pemasukan", "Tabel Pengeluaran"], horizontal=True)

        if pilihan_tabel_hapus == "Tabel Pemasukan" and not df_pemasukan.empty:
            no_hapus = st.number_input("Masukkan nomor 'No' baris Pemasukan:", min_value=1, max_value=len(df_pemasukan), step=1, key="no_hapus_in")
            if st.button("Hapus Baris Pemasukan", key="btn_hapus_in"):
                id_target = df_pemasukan.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_all.drop(id_target).reset_index(drop=True)
                simpan_data_offline(df_keuangan_baru)
                st.success("Data berhasil dihapus dari cloud!")
                st.rerun()

        elif pilihan_tabel_hapus == "Tabel Pengeluaran" and not df_pengeluaran.empty:
            no_hapus = st.number_input("Masukkan nomor 'No' baris Pengeluaran:", min_value=1, max_value=len(df_pengeluaran), step=1, key="no_hapus_out")
            if st.button("Hapus Baris Pengeluaran", key="btn_hapus_out"):
                id_target = df_pengeluaran.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_all.drop(id_target).reset_index(drop=True)
                simpan_data_offline(df_keuangan_baru)
                st.success("Data berhasil dihapus dari cloud!")
                st.rerun()
    else:
        st.info("Buku pembukuan kas Anda masih kosong.")

# ==========================================
# TAB 2: PANTAU UTANG & PIUTANG
# ==========================================
with tab2:
    st.header("Panel Monitoring dan Pelunasan Tanggungan Usaha")

    if not df_master.empty:
        col_piutang, col_utang = st.columns(2)

        # --- BAGIAN PIUTANG ---
        with col_piutang:
            st.markdown("### Piutang Toko (Pelanggan Belum Lunas)")
            df_piutang_raw = df_master[(df_master["Jenis"] == "Pemasukan") & (df_master["Status Pembayaran"] == "Belum Lunas / Piutang")].copy()

            valid_piutang_rows = []
            if not df_piutang_raw.empty:
                for idx, row in df_piutang_raw.iterrows():
                    ket_raw = str(row["Keterangan Transaksi"])
                    nominal_awal = float(row["Harga Total Asli"])
                    dp_dikurangi = float(row["DP Awal"])
                    nama_bersih_p = ket_raw.split(" | TOTAL_AWAL:")[0] if " | TOTAL_AWAL:" in ket_raw else ket_raw

                    kunci_cari = f"ID_REF:{row['ID_Asli']}"
                    df_cicilan = df_all[df_all["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
                    total_cicilan_masuk = df_cicilan["Masuk (Rp)"].sum()

                    sisa_p = nominal_awal - dp_dikurangi - total_cicilan_masuk
                    if sisa_p > 0:
                        row_copy = row.copy()
                        row_copy["Keterangan Usaha"] = nama_bersih_p
                        row_copy["Sudah Dicicil (Rp)"] = total_cicilan_masuk
                        row_copy["Total Sisa Piutang Bersih"] = sisa_p
                        valid_piutang_rows.append(row_copy)

            df_piutang = pd.DataFrame(valid_piutang_rows)

            if not df_piutang.empty:
                st.warning(f"Ada {len(df_piutang)} catatan piutang menggantung.")
                df_piutang_tampil = df_piutang.copy()
                df_piutang_tampil.index = range(1, len(df_piutang_tampil) + 1)
                df_piutang_tampil.index.name = "No"

                df_piutang_v = pd.DataFrame(index=df_piutang_tampil.index)
                df_piutang_v["Tanggal"] = df_piutang_tampil["Tanggal"].astype(str)
                df_piutang_v["Keterangan Pelanggan"] = df_piutang_tampil["Keterangan Usaha"]
                df_piutang_v["Sisa Piutang (Rp)"] = df_piutang_tampil["Total Sisa Piutang Bersih"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                st.dataframe(df_piutang_v, use_container_width=True)

                no_lunas_piutang = st.number_input("Pilih 'No' baris piutang:", min_value=1, max_value=len(df_piutang_tampil), step=1, key="p_no")
                tanggal_bayar_p = st.date_input("Tanggal Cicilan Diterima:", datetime.now().date(), key="p_tgl_bayar")
                status_baru_p = st.selectbox("Status Pembayaran Sekarang:", ["Belum Lunas (Dicicil Lagi)", "Lunas dibayar Penuh"], key="p_stat")

                if "val_bayar_p" not in st.session_state:
                    st.session_state["val_bayar_p"] = ""

                def format_ribuan_p():
                    teks = st.session_state["p_input_dana"]
                    angka = "".join([c for c in teks if c.isdigit()])
                    st.session_state["val_bayar_p"] = f"{int(angka):,.0f}".replace(",", ".") if angka else ""

                input_bayar_p = st.text_input("Jumlah Uang Cicilan (Rp):", value=st.session_state["val_bayar_p"], key="p_input_dana", on_change=format_ribuan_p)
                angka_p_polos = "".join([c for c in input_bayar_p if c.isdigit()])
                nominal_p = int(angka_p_polos) if angka_p_polos else 0

                if st.button("Simpan Cicilan Piutang", use_container_width=True):
                    if nominal_p <= 0:
                        st.error("Masukkan jumlah uang valid!")
                    else:
                        id_target = df_piutang_tampil.loc[no_lunas_piutang, "ID_Asli"]
                        ket_asli_toko = df_piutang_tampil.loc[no_lunas_piutang, "Keterangan Usaha"]
                        sisa_maksimal_p = df_piutang_tampil.loc[no_lunas_piutang, "Total Sisa Piutang Bersih"]

                        if status_baru_p == "Lunas dibayar Penuh" or nominal_p >= sisa_maksimal_p:
                            df_all.loc[id_target, "Status Pembayaran"] = "Lunas"
                            prefix_p = "[Pelunasan Total]"
                        else:
                            df_all.loc[id_target, "Status Pembayaran"] = "Belum Lunas / Piutang"
                            prefix_p = "[Cicilan Baru]"

                        new_trans = pd.DataFrame([{
                            "Nama UMKM": umkm_terpilih,
                            "Tanggal": str(tanggal_bayar_p),
                            "Keterangan Transaksi": f"{prefix_p} {ket_asli_toko} | ID_REF:{id_target}",
                            "Jenis": "Pemasukan",
                            "Kategori Spesifik": "Penjualan Produk Utama",
                            "Masuk (Rp)": nominal_p, "Keluar (Rp)": 0,
                            "Status Pembayaran": "Lunas", "Metode Pembayaran": "Tunai",
                            "Harga Total Asli": nominal_p, "DP Awal": 0
                        }])
                        simpan_data_offline(pd.concat([df_all, new_trans], ignore_index=True))
                        st.session_state["val_bayar_p"] = ""
                        st.success("Pembayaran tercatat permanen!")
                        st.rerun()
            else:
                st.success("Semua piutang pelanggan lunas.")

        # --- BAGIAN UTANG ---
        with col_utang:
            st.markdown("### Utang Toko (Bon Kita ke Supplier)")
            df_utang_raw = df_master[(df_master["Jenis"] == "Pengeluaran") & (df_master["Status Pembayaran"] == "Bon / Utang Usaha")].copy()

            valid_utang_rows = []
            if not df_utang_raw.empty:
                for idx, row in df_utang_raw.iterrows():
                    ket_raw = str(row["Keterangan Transaksi"])
                    nominal_awal = float(row["Harga Total Asli"])
                    dp_dikurangi_u = float(row["DP Awal"])
                    nama_clean_u = ket_raw.split(" | TOTAL_AWAL:")[0] if " | TOTAL_AWAL:" in ket_raw else ket_raw

                    kunci_cari = f"ID_REF:{row['ID_Asli']}"
                    df_cicilan = df_all[df_all["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
                    total_cicilan_keluar = df_cicilan["Keluar (Rp)"].sum()

                    total_sudah_dibayar_u = dp_dikurangi_u + total_cicilan_keluar
                    sisa_u = nominal_awal - total_sudah_dibayar_u
                    if sisa_u > 0:
                        row_copy = row.copy()
                        row_copy["Keterangan Usaha"] = nama_clean_u
                        row_copy["Total Harga Awal"] = nominal_awal
                        row_copy["Sudah Dicicil (Rp)"] = total_sudah_dibayar_u
                        row_copy["Total Sisa Utang Bersih"] = sisa_u
                        valid_utang_rows.append(row_copy)

            df_utang = pd.DataFrame(valid_utang_rows)

            if not df_utang.empty:
                st.error(f"Ada {len(df_utang)} catatan bon belum lunas ke supplier.")
                df_utang_tampil = df_utang.copy()
                df_utang_tampil.index = range(1, len(df_utang_tampil) + 1)
                df_utang_tampil.index.name = "No"

                df_utang_v = pd.DataFrame(index=df_utang_tampil.index)
                df_utang_v["Tanggal"] = df_utang_tampil["Tanggal"].astype(str)
                df_utang_v["Keterangan Supplier"] = df_utang_tampil["Keterangan Usaha"]
                df_utang_v["Total Harga (Rp)"] = df_utang_tampil["Total Harga Awal"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_utang_v["Sudah Dibayar (Rp)"] = df_utang_tampil["Sudah Dicicil (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_utang_v["Sisa Utang (Rp)"] = df_utang_tampil["Total Sisa Utang Bersih"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                st.dataframe(df_utang_v, use_container_width=True)

                no_lunas_utang = st.number_input("Pilih 'No' baris utang:", min_value=1, max_value=len(df_utang_tampil), step=1, key="u_no")
                tanggal_bayar_u = st.date_input("Tanggal Cicilan Dibayar:", datetime.now().date(), key="u_tgl_bayar")
                status_baru_u = st.selectbox("Status Pembayaran Sekarang:", ["Bon / Utang Usaha (Dicicil Baru)", "Dibayar Lunas Penuh"], key="u_stat")

                if "val_bayar_u" not in st.session_state:
                    st.session_state["val_bayar_u"] = ""

                def format_ribuan_u():
                    teks = st.session_state["u_input_dana"]
                    angka = "".join([c for c in teks if c.isdigit()])
                    st.session_state["val_bayar_u"] = f"{int(angka):,.0f}".replace(",", ".") if angka else ""

                input_bayar_u = st.text_input("Jumlah Uang Dibayar (Rp):", value=st.session_state["val_bayar_u"], key="u_input_dana", on_change=format_ribuan_u)
                angka_u_polos = "".join([c for c in input_bayar_u if c.isdigit()])
                nominal_u = int(angka_u_polos) if angka_u_polos else 0

                if st.button("Simpan Pembayaran Utang", use_container_width=True):
                    if nominal_u <= 0:
                        st.error("Masukkan jumlah uang valid!")
                    else:
                        id_target = df_utang_tampil.loc[no_lunas_utang, "ID_Asli"]
                        ket_asli_toko = df_utang_tampil.loc[no_lunas_utang, "Keterangan Usaha"]
                        sisa_maksimal_u = df_utang_tampil.loc[no_lunas_utang, "Total Sisa Utang Bersih"]

                        if status_baru_u == "Dibayar Lunas Penuh" or nominal_u >= sisa_maksimal_u:
                            df_all.loc[id_target, "Status Pembayaran"] = "Dibayar (Lunas)"
                            prefix_u = "[Pelunasan Total]"
                        else:
                            df_all.loc[id_target, "Status Pembayaran"] = "Bon / Utang Usaha"
                            prefix_u = "[Bayar Cicilan]"

                        new_trans = pd.DataFrame([{
                            "Nama UMKM": umkm_terpilih,
                            "Tanggal": str(tanggal_bayar_u),
                            "Keterangan Transaksi": f"{prefix_u} {ket_asli_toko} | ID_REF:{id_target}",
                            "Jenis": "Pengeluaran", "Kategori Spesifik": "Bahan Baku / Stok Barang",
                            "Masuk (Rp)": 0, "Keluar (Rp)": nominal_u,
                            "Status Pembayaran": "Dibayar (Lunas)", "Metode Pembayaran": "Tunai",
                            "Harga Total Asli": nominal_u, "DP Awal": 0
                        }])
                        simpan_data_offline(pd.concat([df_all, new_trans], ignore_index=True))
                        st.session_state["val_bayar_u"] = ""
                        st.success("Pembayaran utang tercatat permanen!")
                        st.rerun()
            else:
                st.success("Bebas dari utang/bon supplier.")
    else:
        st.info("Belum ada transaksi tercatat.")

# ==========================================
# TAB 3: LAPORAN LABA RUGI & ANALISIS USAHA
# ==========================================
with tab3:
    st.header("Analisis Laba Rugi Toko Anda")
    if not df_master.empty:
        df_master["Tanggal"] = pd.to_datetime(df_master["Tanggal"], errors="coerce").dt.date
        pilihan_periode = st.selectbox("Pilih Rentang Laporan Keuangan:", ["Semua Periode", "3 Bulan Terakhir", "Bulan Ini Saja"])

        hari_ini = datetime.now().date()
        if pilihan_periode == "3 Bulan Terakhir":
            df_filtered = df_master[(df_master["Tanggal"] >= (hari_ini - timedelta(days=90))) & (df_master["Tanggal"] <= hari_ini)].copy()
        elif pilihan_periode == "Bulan Ini Saja":
            df_filtered = df_master[(df_master["Tanggal"] >= hari_ini.replace(day=1)) & (df_master["Tanggal"] <= hari_ini)].copy()
        else:
            df_filtered = df_master.copy()

        in_utama = df_filtered[df_filtered["Kategori Spesifik"] == "Penjualan Produk Utama"]["Masuk (Rp)"].sum()
        in_jasa = df_filtered[df_filtered["Kategori Spesifik"] == "Pendapatan Jasa / Komisi"]["Masuk (Rp)"].sum()
        in_sampingan = df_filtered[df_filtered["Kategori Spesifik"] == "Penjualan Sampingan"]["Masuk (Rp)"].sum()
        in_lain = df_filtered[df_filtered["Kategori Spesifik"] == "Lain-lain (Pemasukan)"]["Masuk (Rp)"].sum()
        total_omzet_produk = in_utama + in_jasa + in_sampingan + in_lain

        out_bahan = df_filtered[df_filtered["Kategori Spesifik"] == "Bahan Baku / Stok Barang"]["Keluar (Rp)"].sum()
        out_operasional = df_filtered[df_filtered["Kategori Spesifik"] == "Operasional & Sewa Tempat"]["Keluar (Rp)"].sum()
        out_gaji = df_filtered[df_filtered["Kategori Spesifik"] == "Gaji & Upah Karyawan"]["Keluar (Rp)"].sum()
        out_alat = df_filtered[df_filtered["Kategori Spesifik"] == "Alat & Perlengkapan Usaha"]["Keluar (Rp)"].sum()
        out_trans = df_filtered[df_filtered["Kategori Spesifik"] == "Transportasi & Ongkir"]["Keluar (Rp)"].sum()
        out_lain = df_filtered[df_filtered["Kategori Spesifik"] == "Lain-lain (Pengeluaran)"]["Keluar (Rp)"].sum()
        total_biaya_operasional = out_bahan + out_operasional + out_gaji + out_alat + out_trans + out_lain

        laba_Internal = total_omzet_produk - total_biaya_operasional

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pemasukan (Omzet Nyata)", f"Rp {total_omzet_produk:,.0f}".replace(",", "."))
        m2.metric("Total Biaya Pengeluaran", f"Rp {total_biaya_operasional:,.0f}".replace(",", "."))
        m3.metric("LABA BERSIH USAHA" if laba_Internal >= 0 else "RUGI BERSIH USAHA", f"Rp {abs(laba_Internal):,.0f}".replace(",", "."))

        st.divider()
        col_kiri, col_kanan = st.columns(2)
        with col_kiri:
            st.subheader("Grafik Sumber Pendapatan")
            if total_omzet_produk > 0:
                df_pie_in = pd.DataFrame({"Sumber": ["Produk Utama", "Jasa/Komisi", "Sampingan", "Lain-lain"], "Jumlah (Rp)": [in_utama, in_jasa, in_sampingan, in_lain]})
                st.plotly_chart(px.pie(df_pie_in[df_pie_in["Jumlah (Rp)"] > 0], values="Jumlah (Rp)", names="Sumber", hole=0.3), use_container_width=True)
            else:
                st.info("Belum ada data.")
        with col_kanan:
            st.subheader("Alokasi Struktur Biaya")
            if total_biaya_operasional > 0:
                df_pie_out = pd.DataFrame({"Kategori": ["Bahan/Stok", "Operasional", "Gaji", "Alat Usaha", "Transportasi", "Lain-lain"], "Jumlah (Rp)": [out_bahan, out_operasional, out_gaji, out_alat, out_trans, out_lain]})
                st.plotly_chart(px.pie(df_pie_out[df_pie_out["Jumlah (Rp)"] > 0], values="Jumlah (Rp)", names="Kategori", hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu), use_container_width=True)
            else:
                st.info("Belum ada data.")
