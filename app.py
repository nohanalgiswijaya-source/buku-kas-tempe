import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import io
import plotly.express as px

# --- SETTING DASHBOARD (Harus paling atas) ---
st.set_page_config(page_title="BUKUDIGI - Catatan Keuangan Usaha", layout="wide")

st.title("BUKUDIGI - Buku Catatan Digital Keuangan Usahamu")
st.markdown("### *Kelola pemasukan dan pengeluaran dengan lebih rapi.*")
st.write("Sistem Arus Kas Riil - Pencatatan transaksi bertahap berdasarkan perpindahan uang fisik agar kas toko selalu cocok dengan dompet nyata.")

st.divider()

# --- FILE MASTER UNTUK MENYIMPAN KREDENSI UMKM (NAMA & TOKEN) ---
file_master_kredensi = "master_kredensi_umkm.xlsx"

def load_master_kredensi():
    if os.path.exists(file_master_kredensi):
        return pd.read_excel(file_master_kredensi)
    else:
        df_awal = pd.DataFrame(columns=["Nama UMKM", "Token Rahasia"])
        df_awal.to_excel(file_master_kredensi, index=False)
        return df_awal

def daftarkan_umkm_baru(nama, token):
    df_master = load_master_kredensi()
    new_user = pd.DataFrame([{"Nama UMKM": nama, "Token Rahasia": str(token)}])
    df_update = pd.concat([df_master, new_user], ignore_index=True)
    df_update.to_excel(file_master_kredensi, index=False)

# Inisialisasi Session State untuk menyimpan status login/akses
if "login_umkm" not in st.session_state:
    st.session_state["login_umkm"] = None

# ==========================================
# HALAMAN LOG IN / MASUK & DAFTAR
# ==========================================
if st.session_state["login_umkm"] is None:
    
    tab_masuk, tab_daftar = st.tabs(["Masuk Ke Buku Kas", "Daftar Akun Usaha Baru"])
    
    with tab_masuk:
        st.subheader("Silakan masukkan identitas usaha Anda untuk melihat kas")
        input_nama_masuk = st.text_input("Nama UMKM / Usaha Anda:", placeholder="Ketik nama toko Anda...")
        input_token_masuk = st.text_input("Token / PIN Rahasia Usaha:", type="password", placeholder="Masukkan token Anda...")
        
        tombol_masuk = st.button("Buka dan Load Buku Kas")
        
        if tombol_masuk:
            df_master = load_master_kredensi()
            nama_clean = input_nama_masuk.strip()
            token_clean = input_token_masuk.strip()
            
            user_match = df_master[df_master["Nama UMKM"].str.lower() == nama_clean.lower()]
            
            if user_match.empty:
                st.error("Nama UMKM belum terdaftar! Silakan daftar baru di tab sebelah.")
            else:
                token_tercatat = str(user_match.iloc[0]["Token Rahasia"])
                nama_tercatat = user_match.iloc[0]["Nama UMKM"]
                
                if token_clean == token_tercatat:
                    st.session_state["login_umkm"] = nama_tercatat
                    st.success(f"Login Sukses! Membuka data {nama_tercatat}...")
                    st.rerun()
                else:
                    st.error("Token Rahasia salah! Akses ditolak.")
                    
    with tab_daftar:
        st.subheader("Pendaftaran Ruang Pembukuan Baru")
        st.write("Daftarkan toko Anda di sini agar mendapatkan file Excel kas terpisah secara otomatis.")
        
        input_nama_daftar = st.text_input("Nama UMKM Baru:", placeholder="Contoh: Warung Berkah, Laundry Wangi")
        input_token_daftar = st.text_input("Buat Token / PIN Rahasia Baru (Bebas Angka/Huruf):", type="password", placeholder="Contoh: 12345 or rahasiatoko")
        
        tombol_daftar = st.button("Simpan dan Daftarkan Toko Sekarang")
        
        if tombol_daftar:
            nama_df_clean = input_nama_daftar.strip()
            token_df_clean = input_token_daftar.strip()
            
            if nama_df_clean == "" or token_df_clean == "":
                st.error("Nama UMKM dan Token tidak boleh kosong!")
            else:
                df_master = load_master_kredensi()
                if not df_master.empty and nama_df_clean.lower() in df_master["Nama UMKM"].str.lower().values:
                    st.error("Nama UMKM ini sudah terdaftar sebelumnya! Gunakan nama lain or langsung login.")
                else:
                    daftarkan_umkm_baru(nama_df_clean, token_df_clean)
                    st.success(f"Berhasil mendaftarkan {nama_df_clean}! Silakan masuk menggunakan tab Masuk Ke Buku Kas.")

    st.stop()

# ==========================================
# HALAMAN UTAMA PEMBUKAAN (JIKA SUDAH LOG IN)
# ==========================================
umkm_terpilih = st.session_state["login_umkm"]

col_header, col_logout = st.columns([4, 1])
with col_header:
    st.markdown(f"### Selamat Datang Kembali, **{umkm_terpilih}**!")
with col_logout:
    if st.button("Keluar dan Kunci Kas", use_container_width=True):
        st.session_state["login_umkm"] = None
        states_to_clear = ["jumlah_dana_raw", "val_bayar_p", "val_bayar_u"]
        for key in states_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

nama_clean = umkm_terpilih.replace(" ", "_").lower()
nama_file_excel = f"buku_kas_{nama_clean}.xlsx"

st.info(f"Database Kas Terkunci Aman: Mengelola file data: {nama_file_excel}")

def load_data_offline():
    if os.path.exists(nama_file_excel):
        df = pd.read_excel(nama_file_excel)
        return df
    else:
        kolom = [
            "Tanggal", "Keterangan Transaksi", "Jenis", 
            "Kategori Spesifik", "Masuk (Rp)", "Keluar (Rp)", 
            "Status Pembayaran", "Metode Pembayaran"
        ]
        df_baru = pd.DataFrame(columns=kolom)
        df_baru.to_excel(nama_file_excel, index=False)
        return df_baru

df_keuangan = load_data_offline()

# Format dasar kolom dataframe
df_keuangan["Tanggal"] = pd.to_datetime(df_keuangan["Tanggal"]).dt.date
df_keuangan["Masuk (Rp)"] = pd.to_numeric(df_keuangan["Masuk (Rp)"]).fillna(0)
df_keuangan["Keluar (Rp)"] = pd.to_numeric(df_keuangan["Keluar (Rp)"]).fillna(0)

# Pembuatan Data Kumulatif & ID Asli database
if not df_keuangan.empty:
    df_master = df_keuangan.copy()
    saldo_kumulatif = []
    saldo_sekarang = 0
    
    for idx, row in df_master.iterrows():
        saldo_sekarang += float(row["Masuk (Rp)"]) - float(row["Keluar (Rp)"])
        saldo_kumulatif.append(saldo_sekarang)
        
    df_master["Saldo Sisa (Rp)"] = saldo_kumulatif
    df_master["ID_Asli"] = df_master.index
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
        keterangan = st.text_area("Keterangan Transaksi / Nama Pelanggan / Supplier", placeholder="Contoh: Pembelian ayam potong 10kg dari Pak Ali\nContoh pemasukan: Penjualan pesanan kue tart Ibu Rina")
        
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
            "Jumlah Uang Riil (Rp)", 
            value=st.session_state["jumlah_dana_raw"],
            placeholder="Contoh: 50.000",
            help="Ketik angka saja, titik ribuan otomatis memformat sendiri."
        )

        angka_polos = "".join([c for c in input_dana_teks if c.isdigit()])
        if angka_polos:
            jumlah_dana = int(angka_polos)
            teks_terformat = f"{jumlah_dana:,.0f}".replace(",", ".")
            if input_dana_teks != teks_terformat:
                st.session_state["jumlah_dana_raw"] = teks_terformat
                st.rerun()
        else:
            jumlah_dana = 0
            if input_dana_teks != "":
                st.session_state["jumlah_dana_raw"] = ""
                st.rerun()
        
        submit_kas = st.button("Simpan Ke Buku Kas", use_container_width=True)

    if submit_kas:
        if keterangan.strip() == "":
            st.error("Harap isi Keterangan Transaksi / Nama Supplier agar tidak membingungkan pembukuan!")
        elif jumlah_dana <= 0:
            st.error("Harap masukkan Jumlah Uang Riil yang valid lebih besar dari 0!")
        else:
            masuk = jumlah_dana if jenis in ["Pemasukan", "Modal"] else 0
            keluar = jumlah_dana if jenis == "Pengeluaran" else 0
            
            keterangan_final = keterangan
            if jenis == "Pemasukan" and status_bayar in ["DP / Uang Muka", "Belum Lunas / Piutang"]:
                keterangan_final = f"{keterangan} | TOTAL_AWAL:{jumlah_dana}"
            elif jenis == "Pengeluaran" and status_bayar == "Bon / Utang Usaha":
                keterangan_final = f"{keterangan} | TOTAL_AWAL:{jumlah_dana}"

            new_row = pd.DataFrame([{
                "Tanggal": tanggal,
                "Keterangan Transaksi": keterangan_final,
                "Jenis": jenis,
                "Kategori Spesifik": kategori_spesifik,
                "Masuk (Rp)": masuk,
                "Keluar (Rp)": keluar,
                "Status Pembayaran": status_bayar,
                "Metode Pembayaran": metode_bayar
            }])
            
            df_update = pd.concat([df_keuangan, new_row], ignore_index=True)
            df_update.to_excel(nama_file_excel, index=False)
            
            st.session_state["jumlah_dana_raw"] = ""
            st.success("Transaksi berhasil dicatat ke sistem!")
            st.rerun()

    st.divider()
    
    if not df_master.empty:
        st.subheader("Ringkasan Saldo Buku Kas Anda")
        total_uang_masuk = df_master["Masuk (Rp)"].sum()
        total_biaya_keluar = df_master["Keluar (Rp)"].sum()
        sisa_kas_crumbs = total_uang_masuk - total_biaya_keluar
        
        data_ringkasan = {
            "Total Uang Masuk (Kas)": [f"Rp {total_uang_masuk:,.0f}".replace(",", ".")],
            "Total Uang Keluar (Biaya)": [f"Rp {total_biaya_keluar:,.0f}".replace(",", ".")],
            "Saldo Kas Toko Fisik Saat Ini": [f"Rp {sisa_kas_crumbs:,.0f}".replace(",", ".")]
        }
        st.table(pd.DataFrame(data_ringkasan))

        st.divider()
            
        st.write("### HISTORI DATA PEMASUKAN & MODAL")
        df_pemasukan = df_master[df_master["Jenis"].isin(["Pemasukan", "Modal"])].copy()
        if not df_pemasukan.empty:
            df_pemasukan.index = range(1, len(df_pemasukan) + 1)
            df_pemasukan.index.name = "No"
            kolom_in = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Masuk (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pemasukan_v = df_pemasukan[kolom_in].copy()
            df_pemasukan_v["Tanggal"] = df_pemasukan_v["Tanggal"].astype(str)
            df_pemasukan_v["Keterangan Transaksi"] = df_pemasukan_v["Keterangan Transaksi"].apply(lambda x: x.split(" | TOTAL_AWAL:")[0])
            df_pemasukan_v["Masuk (Rp)"] = df_pemasukan_v["Masuk (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pemasukan_v["Saldo Sisa (Rp)"] = df_pemasukan_v["Saldo Sisa (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            st.dataframe(df_pemasukan_v, use_container_width=True)
            
        st.write("### HISTORI DATA PENGELUARAN & BEBAN NYATA")
        df_pengeluaran = df_master[df_master["Jenis"] == "Pengeluaran"].copy()
        if not df_pengeluaran.empty:
            df_pengeluaran.index = range(1, len(df_pengeluaran) + 1)
            df_pengeluaran.index.name = "No"
            kolom_out = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Keluar (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pengeluaran_v = df_pengeluaran[kolom_out].copy()
            df_pengeluaran_v["Tanggal"] = df_pengeluaran_v["Tanggal"].astype(str)
            df_pengeluaran_v["Keterangan Transaksi"] = df_pengeluaran_v["Keterangan Transaksi"].apply(lambda x: x.split(" | TOTAL_AWAL:")[0])
            df_pengeluaran_v["Keluar (Rp)"] = df_pengeluaran_v["Keluar (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            df_pengeluaran_v["Saldo Sisa (Rp)"] = df_pengeluaran_v["Saldo Sisa (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            st.dataframe(df_pengeluaran_v, use_container_width=True)

        st.markdown("---")
        st.markdown("### Panel Hapus Transaksi")
        pilihan_tabel_hapus = st.radio("Pilih sumber hapus data:", ["Tabel Pemasukan", "Tabel Pengeluaran"], horizontal=True)
        
        if pilihan_tabel_hapus == "Tabel Pemasukan" and not df_pemasukan.empty:
            no_hapus = st.number_input("Masukkan nomor 'No' baris Pemasukan:", min_value=1, max_value=len(df_pemasukan), step=1)
            if st.button("Hapus Baris Pemasukan"):
                id_target = df_pemasukan.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_keuangan.drop(id_target).reset_index(drop=True)
                df_keuangan_baru.to_excel(nama_file_excel, index=False)
                st.success("Data berhasil dihapus!")
                st.rerun()
                
        elif pilihan_tabel_hapus == "Tabel Pengeluaran" and not df_pengeluaran.empty:
            no_hapus = st.number_input("Masukkan nomor 'No' baris Pengeluaran:", min_value=1, max_value=len(df_pengeluaran), step=1)
            if st.button("Hapus Baris Pengeluaran"):
                id_target = df_pengeluaran.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_keuangan.drop(id_target).reset_index(drop=True)
                df_keuangan_baru.to_excel(nama_file_excel, index=False)
                st.success("Data berhasil dihapus!")
                st.rerun()
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_master.drop(columns=["ID_Asli"]).to_excel(writer, index=False, sheet_name='Laporan_Buku_Kas')
        buffer.seek(0)
        st.download_button(
            label="Download File Pembukuan Excel Toko Anda (.xlsx)",
            data=buffer,
            file_name=f"Laporan_Kas_{nama_clean}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Buku pembukuan kas Anda masih kosong.")

# ==========================================
# TAB 2: PANTAU UTANG & PIUTANG (DENGAN TANGGAL ADJUSTMENT)
# ==========================================
with tab2:
    st.header("Panel Monitoring dan Pelunasan Tanggungan Usaha")
    st.write("Halaman ini melacak pengurangan utang dan piutang toko secara bertahap (real-time).")
    
    if not df_master.empty:
        col_piutang, col_utang = st.columns(2)
        
        # ------------------------------------------
        # BAGIAN LAJUR PIUTANG (PELANGGAN)
        # ------------------------------------------
        with col_piutang:
            st.markdown("### Piutang Toko (Pelanggan Belum Lunas)")
            
            df_piutang = df_master[(df_master["Jenis"] == "Pemasukan") & (df_master["Status Pembayaran"].isin(["DP / Uang Muka", "Belum Lunas / Piutang"]))].copy()
            
            if not df_piutang.empty:
                sisa_piutang_list = []
                total_dicicil_list = []
                nama_bersih_p_list = []
                
                for idx, row in df_piutang.iterrows():
                    ket_raw = row["Keterangan Transaksi"]
                    nominal_awal = float(row["Masuk (Rp)"])
                    
                    if " | TOTAL_AWAL:" in ket_raw:
                        parts = ket_raw.split(" | TOTAL_AWAL:")
                        nama_bersih_p = parts[0]
                        nominal_awal = float(parts[1])
                    else:
                        nama_bersih_p = ket_raw
                    
                    kunci_cari = f"ID_REF:{idx}"
                    df_cicilan = df_master[df_master["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
                    total_cicilan_masuk = df_cicilan["Masuk (Rp)"].sum()
                    
                    sisa_p = nominal_awal - total_cicilan_masuk
                    
                    total_dicicil_list.append(total_cicilan_masuk)
                    sisa_piutang_list.append(sisa_p)
                    nama_bersih_p_list.append(nama_bersih_p)
                
                df_piutang["Keterangan Usaha"] = nama_bersih_p_list
                df_piutang["Total Piutang Awal"] = df_piutang["Masuk (Rp)"]
                df_piutang["Sudah Dicicil (Rp)"] = total_dicicil_list
                df_piutang["Sisa Piutang (Rp)"] = sisa_piutang_list
                
                df_piutang = df_piutang[df_piutang["Sisa Piutang (Rp)"] > 0].copy()
            
            if not df_piutang.empty:
                st.warning(f"Ada {len(df_piutang)} catatan piutang menggantung dari pelanggan.")
                
                df_piutang_tampil = df_piutang.copy()
                df_piutang_tampil.index = range(1, len(df_piutang_tampil) + 1)
                df_piutang_tampil.index.name = "No"
                
                df_piutang_v = pd.DataFrame(index=df_piutang_tampil.index)
                df_piutang_v["Tanggal"] = df_piutang_tampil["Tanggal"].astype(str)
                df_piutang_v["Keterangan Pelanggan"] = df_piutang_tampil["Keterangan Usaha"]
                df_piutang_v["Total Piutang (Rp)"] = df_piutang_tampil["Masuk (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_piutang_v["Total Dicicil (Rp)"] = df_piutang_tampil["Sudah Dicicil (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_piutang_v["Sisa Piutang (Rp)"] = df_piutang_tampil["Sisa Piutang (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                
                st.dataframe(df_piutang_v, use_container_width=True)
                
                st.markdown("##### Proses Pembayaran Piutang Pelanggan")
                no_lunas_piutang = st.number_input("Pilih 'No' baris piutang:", min_value=1, max_value=len(df_piutang_tampil), step=1, key="p_no")
                
                # FITUR BARU: Input tanggal kustom untuk cicilan/DP piutang
                tanggal_bayar_p = st.date_input("Tanggal Penerimaan Uang Cicilan:", datetime.now().date(), key="p_tgl_bayar")
                
                status_baru_p = st.selectbox("Status Pembayaran Sekarang:", ["DP / Uang Muka (Dicicil Lagi)", "Lunas dibayar Penuh"], key="p_stat")
                
                if "val_bayar_p" not in st.session_state:
                    st.session_state["val_bayar_p"] = ""

                def format_ribuan_p():
                    teks = st.session_state["p_input_dana"]
                    angka = "".join([c for c in teks if c.isdigit()])
                    if angka:
                        st.session_state["val_bayar_p"] = f"{int(angka):,.0f}".replace(",", ".")
                    else:
                        st.session_state["val_bayar_p"] = ""

                label_p = "Jumlah Uang Cicilan yang Diterima (Rp):"
                input_bayar_p = st.text_input(label_p, value=st.session_state["val_bayar_p"], key="p_input_dana", on_change=format_ribuan_p, placeholder="Contoh: 50.000")
                
                angka_p_polos = "".join([c for c in input_bayar_p if c.isdigit()])
                nominal_p = int(angka_p_polos) if angka_p_polos else 0
                
                if st.button("Simpan Pembayaran Piutang", use_container_width=True):
                    if nominal_p <= 0:
                        st.error("Masukkan jumlah uang pembayaran yang valid!")
                    else:
                        id_target = df_piutang_tampil.loc[no_lunas_piutang, "ID_Asli"]
                        ket_asli_toko = df_piutang_tampil.loc[no_lunas_piutang, "Keterangan Usaha"]
                        sisa_maksimal_p = df_piutang_tampil.loc[no_lunas_piutang, "Sisa Piutang (Rp)"]
                        
                        if status_baru_p == "Lunas dibayar Penuh" or nominal_p >= sisa_maksimal_p:
                            df_keuangan.loc[id_target, "Status Pembayaran"] = "Lunas"
                            prefix_p = "[Pelunasan Total]"
                        else:
                            df_keuangan.loc[id_target, "Status Pembayaran"] = "DP / Uang Muka"
                            prefix_p = "[Cicilan Baru]"
                        
                        new_trans = pd.DataFrame([{
                            "Tanggal": tanggal_bayar_p,  # Menggunakan tanggal input pilihan user
                            "Keterangan Transaksi": f"{prefix_p} {ket_asli_toko} | ID_REF:{id_target}",
                            "Jenis": "Pemasukan",
                            "Kategori Spesifik": "Penjualan Produk Utama",
                            "Masuk (Rp)": nominal_p,
                            "Keluar (Rp)": 0,
                            "Status Pembayaran": "Lunas",
                            "Metode Pembayaran": "Tunai"
                        }])
                        
                        df_update = pd.concat([df_keuangan, new_trans], ignore_index=True)
                        df_update.to_excel(nama_file_excel, index=False)
                        
                        st.session_state["val_bayar_p"] = ""
                        st.success("Pembayaran cicilan piutang berhasil dicatat!")
                        st.rerun()
            else:
                st.success("Semua piutang pelanggan sudah lunas dibayar penuh.")
                
        # ------------------------------------------
        # BAGIAN LAJUR UTANG (SUPPLIER BON)
        # ------------------------------------------
        with col_utang:
            st.markdown("### Utang Toko (Bon Kita ke Supplier)")
            
            df_utang = df_master[(df_master["Jenis"] == "Pengeluaran") & (df_master["Status Pembayaran"] == "Bon / Utang Usaha")].copy()
            
            if not df_utang.empty:
                sisa_utang_list = []
                total_dibayar_list = []
                nama_bersih_u_list = []
                
                for idx, row in df_utang.iterrows():
                    ket_raw = row["Keterangan Transaksi"]
                    nominal_awal = float(row["Keluar (Rp)"])
                    
                    if " | TOTAL_AWAL:" in ket_raw:
                        parts = ket_raw.split(" | TOTAL_AWAL:")
                        nama_bersih_u = parts[0]
                        nominal_awal = float(parts[1])
                    else:
                        nama_bersih_u = ket_raw
                    
                    kunci_cari = f"ID_REF:{idx}"
                    df_cicilan = df_master[df_master["Keterangan Transaksi"].str.contains(kunci_cari, na=False)]
                    total_cicilan_keluar = df_cicilan["Keluar (Rp)"].sum()
                    
                    sisa_u = nominal_awal - total_cicilan_keluar
                    
                    total_dibayar_list.append(total_cicilan_keluar)
                    sisa_utang_list.append(sisa_u)
                    nama_bersih_u_list.append(nama_bersih_u)
                    
                df_utang["Keterangan Usaha"] = nama_bersih_u_list
                df_utang["Total Utang Awal"] = df_utang["Keluar (Rp)"]
                df_utang["Sudah Dicicil (Rp)"] = total_dibayar_list
                df_utang["Sisa Utang (Rp)"] = sisa_utang_list
                
                df_utang = df_utang[df_utang["Sisa Utang (Rp)"] > 0].copy()
                
            if not df_utang.empty:
                st.error(f"Ada {len(df_utang)} catatan bon barang yang belum kita lunasi ke supplier.")
                
                df_utang_tampil = df_utang.copy()
                df_utang_tampil.index = range(1, len(df_utang_tampil) + 1)
                df_utang_tampil.index.name = "No"
                
                df_utang_v = pd.DataFrame(index=df_utang_tampil.index)
                df_utang_v["Tanggal"] = df_utang_tampil["Tanggal"].astype(str)
                df_utang_v["Keterangan Supplier"] = df_utang_tampil["Keterangan Usaha"]
                df_utang_v["Total Utang (Rp)"] = df_utang_tampil["Keluar (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_utang_v["Total Dicicil (Rp)"] = df_utang_tampil["Sudah Dicicil (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                df_utang_v["Sisa Utang (Rp)"] = df_utang_tampil["Sisa Utang (Rp)"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
                
                st.dataframe(df_utang_v, use_container_width=True)
                
                st.markdown("##### Proses Bayar Bon / Utang ke Supplier")
                no_lunas_utang = st.number_input("Pilih 'No' baris utang:", min_value=1, max_value=len(df_utang_tampil), step=1, key="u_no")
                
                # FITUR BARU: Input tanggal kustom untuk cicilan/bayar utang supplier
                tanggal_bayar_u = st.date_input("Tanggal Pembayaran Cicilan Bon:", datetime.now().date(), key="u_tgl_bayar")
                
                status_baru_u = st.selectbox("Status Pembayaran Sekarang:", ["Bon / Utang Usaha (Dicicil Baru)", "Dibayar Lunas Penuh"], key="u_stat")
                
                if "val_bayar_u" not in st.session_state:
                    st.session_state["val_bayar_u"] = ""

                def format_ribuan_u():
                    teks = st.session_state["u_input_dana"]
                    angka = "".join([c for c in teks if c.isdigit()])
                    if angka:
                        st.session_state["val_bayar_u"] = f"{int(angka):,.0f}".replace(",", ".")
                    else:
                        st.session_state["val_bayar_u"] = ""

                label_u = "Jumlah Uang Cicilan yang Dibayarkan (Rp):"
                input_bayar_u = st.text_input(label_u, value=st.session_state["val_bayar_u"], key="u_input_dana", on_change=format_ribuan_u, placeholder="Contoh: 50.000")
                
                angka_u_polos = "".join([c for c in input_bayar_u if c.isdigit()])
                nominal_u = int(angka_u_polos) if angka_u_polos else 0
                
                if st.button("Simpan Pembayaran Utang", use_container_width=True):
                    if nominal_u <= 0:
                        st.error("Masukkan jumlah uang pembayaran yang valid!")
                    else:
                        id_target = df_utang_tampil.loc[no_lunas_utang, "ID_Asli"]
                        ket_asli_toko = df_utang_tampil.loc[no_lunas_utang, "Keterangan Usaha"]
                        sisa_maksimal_u = df_utang_tampil.loc[no_lunas_utang, "Sisa Utang (Rp)"]
                        
                        if status_baru_u == "Dibayar Lunas Penuh" or nominal_u >= sisa_maksimal_u:
                            df_keuangan.loc[id_target, "Status Pembayaran"] = "Dibayar (Lunas)"
                            prefix_u = "[Pelunasan Total]"
                        else:
                            df_keuangan.loc[id_target, "Status Pembayaran"] = "Bon / Utang Usaha"
                            prefix_u = "[Bayar Cicilan]"
                        
                        new_trans = pd.DataFrame([{
                            "Tanggal": tanggal_bayar_u,  # Menggunakan tanggal input pilihan user
                            "Keterangan Transaksi": f"{prefix_u} {ket_asli_toko} | ID_REF:{id_target}",
                            "Jenis": "Pengeluaran",
                            "Kategori Spesifik": "Bahan Baku / Stok Barang",
                            "Masuk (Rp)": 0,
                            "Keluar (Rp)": nominal_u,
                            "Status Pembayaran": "Dibayar (Lunas)",
                            "Metode Pembayaran": "Tunai"
                        }])
                        
                        df_update = pd.concat([df_keuangan, new_trans], ignore_index=True)
                        df_update.to_excel(nama_file_excel, index=False)
                        
                        st.session_state["val_bayar_u"] = ""
                        st.success("Pembayaran bon ke supplier berhasil dicatat!")
                        st.rerun()
            else:
                st.success("Aman! Toko Anda bebas dari segala jenis tanggungan bon/utang belanja.")
    else:
        st.info("Belum ada data transaksi yang tercatat untuk dipantau.")

# ==========================================
# TAB 3: LAPORAN LABA RUGI & ANALISIS USAHA
# ==========================================
with tab3:
    st.header("Analisis Laba Rugi Toko Anda")
    
    if not df_keuangan.empty:
        hari_ini = datetime.now().date()
        tiga_bulan_lalu = hari_ini - timedelta(days=90)
        
        pilihan_periode = st.selectbox("Pilih Rentang Laporan Keuangan:", ["Semua Periode", "3 Bulan Terakhir", "Bulan Ini Saja"])
        
        if pilihan_periode == "3 Bulan Terakhir":
            tgl_mulai = tiga_bulan_lalu
        elif pilihan_periode == "Bulan Ini Saja":
            tgl_mulai = hari_ini.replace(day=1)
        else:
            tgl_mulai = df_keuangan["Tanggal"].min()
            
        df_filtered = df_keuangan[(df_keuangan["Tanggal"] >= tgl_mulai) & (df_keuangan["Tanggal"] <= hari_ini)]
        
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
        
        laba_bersih_analisis = total_omzet_produk - total_biaya_operasional
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pemasukan (Omzet)", f"Rp {total_omzet_produk:,.0f}".replace(",", "."))
        m2.metric("Total Biaya Pengeluaran", f"Rp {total_biaya_operasional:,.0f}".replace(",", "."))
        if laba_bersih_analisis >= 0:
            m3.metric("LABA BERSIH USAHA", f"Rp {laba_bersih_analisis:,.0f}".replace(",", "."))
        else:
            m3.metric("RUGI BERSIH USAHA", f"Rp {abs(laba_bersih_analisis):,.0f}".replace(",", "."))
            
        st.divider()
        col_kiri, col_kanan = st.columns(2)
        
        with col_kiri:
            st.subheader("Grafik Sumber Pendapatan")
            if total_omzet_produk > 0:
                df_pie_in = pd.DataFrame({
                    "Sumber Pendapatan": ["Produk Utama", "Jasa/Komisi", "Sampingan", "Lain-lain"],
                    "Jumlah (Rp)": [in_utama, in_jasa, in_sampingan, in_lain]
                })
                fig_in = px.pie(df_pie_in, values="Jumlah (Rp)", names="Sumber Pendapatan", hole=0.3)
                st.plotly_chart(fig_in, use_container_width=True)
            else:
                st.info("Belum ada data pendapatan untuk grafik.")

        with col_kanan:
            st.subheader("Alokasi Struktur Biaya")
            if total_biaya_operasional > 0:
                df_pie_out = pd.DataFrame({
                    "Kategori Pengeluaran": ["Bahan/Stok", "Operasional", "Gaji", "Alat Usaha", "Transportasi", "Lain-lain"],
                    "Jumlah (Rp)": [out_bahan, out_operasional, out_gaji, out_alat, out_trans, out_lain]
                })
                fig_out = px.pie(df_pie_out, values="Jumlah (Rp)", names="Kategori Pengeluaran", hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_out, use_container_width=True)
            else:
                st.info("Belum ada data pengeluaran untuk grafik.")
    else:
        st.info("Buku kas kosong. Isi transaksi terlebih dahulu.")