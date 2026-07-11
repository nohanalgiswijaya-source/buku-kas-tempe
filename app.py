import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import io
import plotly.express as px

# --- SETTING DASHBOARD (Harus paling atas) ---
st.set_page_config(page_title="Buku Kas Digital Multi-UMKM Aman", layout="wide")

st.title("🔐 BUKU KAS DIGITAL MULTI-UMKM (VERSI PRIVAT)")
st.write("✨ **Sistem Arus Kas Riil** — Pencatatan DP dan Pelunasan dilakukan bertahap sesuai tanggal uang masuk agar kas fisik selalu cocok.")

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
# HALAMAN LOG IN / MASUK & DAFTAR (JIKA BELUM LOGIN)
# ==========================================
if st.session_state["login_umkm"] is None:
    
    tab_masuk, tab_daftar = st.tabs(["🔑 Masuk Ke Buku Kas", "➕ Daftar Akun Usaha Baru"])
    
    with tab_masuk:
        st.subheader("Silakan masukkan identitas usaha Anda untuk melihat kas")
        input_nama_masuk = st.text_input("Nama UMKM / Usaha Anda:", placeholder="Ketik nama toko Anda...")
        input_token_masuk = st.text_input("Token / PIN Rahasia Usaha:", type="password", placeholder="Masukkan token Anda...")
        
        tombol_masuk = st.button("Buka & Load Buku Kas 🚀")
        
        if tombol_masuk:
            df_master = load_master_kredensi()
            nama_clean = input_nama_masuk.strip()
            token_clean = input_token_masuk.strip()
            
            user_match = df_master[df_master["Nama UMKM"].str.lower() == nama_clean.lower()]
            
            if user_match.empty:
                st.error("❌ Nama UMKM belum terdaftar! Silakan daftar baru di tab sebelah.")
            else:
                token_tercatat = str(user_match.iloc[0]["Token Rahasia"])
                nama_tercatat = user_match.iloc[0]["Nama UMKM"]
                
                if token_clean == token_tercatat:
                    st.session_state["login_umkm"] = nama_tercatat
                    st.success(f"🎉 Login Sukses! Membuka data {nama_tercatat}...")
                    st.rerun()
                else:
                    st.error("❌ Token Rahasia salah! Akses ditolak.")
                    
    with tab_daftar:
        st.subheader("Pendaftaran Ruang Pembukuan Baru")
        st.write("Daftarkan toko Anda di sini agar mendapatkan file Excel kas terpisah secara otomatis.")
        
        input_nama_daftar = st.text_input("Nama UMKM Baru:", placeholder="Contoh: Warung Berkah, Laundry Wangi")
        input_token_daftar = st.text_input("Buat Token / PIN Rahasia Baru (Bebas Angka/Huruf):", type="password", placeholder="Contoh: 12345 atau rahasiatoko")
        
        tombol_daftar = st.button("Simpan & Daftarkan Toko Sekarang ✨")
        
        if tombol_daftar:
            nama_df_clean = input_nama_daftar.strip()
            token_df_clean = input_token_daftar.strip()
            
            if nama_df_clean == "" or token_df_clean == "":
                st.error("⚠️ Nama UMKM dan Token tidak boleh kosong!")
            else:
                df_master = load_master_kredensi()
                if not df_master.empty and nama_df_clean.lower() in df_master["Nama UMKM"].str.lower().values:
                    st.error("⚠️ Nama UMKM ini sudah terdaftar sebelumnya! Gunakan nama lain atau langsung login.")
                else:
                    daftarkan_umkm_baru(nama_df_clean, token_df_clean)
                    st.success(f"🎉 Berhasil mendaftarkan **{nama_df_clean}**! Silakan masuk menggunakan tab 'Masuk Ke Buku Kas'.")

    st.stop()

# ==========================================
# HALAMAN UTAMA PEMBUKUAN (JIKA SUDAH BERHASIL LOGIN)
# ==========================================
umkm_terpilih = st.session_state["login_umkm"]

col_header, col_logout = st.columns([4, 1])
with col_header:
    st.markdown(f"### 🏪 Selamat Datang Kembali, **{umkm_terpilih}**!")
with col_logout:
    if st.button("❌ Keluar & Kunci Kas", use_container_width=True):
        st.session_state["login_umkm"] = None
        st.rerun()

nama_clean = umkm_terpilih.replace(" ", "_").lower()
nama_file_excel = f"buku_kas_{nama_clean}.xlsx"

st.info(f"📂 **Database Kas Terkunci Aman:** Mengelola file data: `{nama_file_excel}`")

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

df_keuangan["Tanggal"] = pd.to_datetime(df_keuangan["Tanggal"]).dt.date
df_keuangan["Masuk (Rp)"] = pd.to_numeric(df_keuangan["Masuk (Rp)"]).fillna(0)
df_keuangan["Keluar (Rp)"] = pd.to_numeric(df_keuangan["Keluar (Rp)"]).fillna(0)

# --- MENU TAB ---
tab1, tab2 = st.tabs(["📝 Input & Histori Buku Kas", "📈 Laporan Laba/Rugi & Analisis Usaha"])

with tab1:
    st.subheader(f"📝 Catat Transaksi Baru")
    
    # Panduan Ringkas Alur DP & Pelunasan
    st.info("💡 **Panduan Pencatatan Pembayaran Bertahap (DP):** \n"
            "1. **Saat Terima DP:** Masukkan nominal DP yang diterima hari ini, beri keterangan nama pelanggan, set status ke `DP / Uang Muka`.\n"
            "2. **Saat Pelunasan:** Input baris transaksi baru, masukkan nominal sisa pelunasannya, beri keterangan pelunasan atas nama siapa, lalu set status ke `Lunas`.")
    
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
        keterangan = st.text_area("Keterangan Transaksi / Nama Pelanggan", placeholder="Contoh awal: DP Order Kue Bu Jono\nContoh pelunasan: Pelunasan Sisa Order Kue Bu Jono")
        
        if jenis == "Pemasukan":
            status_opsi = ["Lunas", "DP / Uang Muka", "Belum Lunas / Piutang"]
        elif jenis == "Modal":
            status_opsi = ["Lunas / Masuk Kas"]
        else:
            status_opsi = ["Dibayar (Lunas)", "Bon / Utang Usaha"]
            
        status_bayar = st.selectbox("Status Transaksi", status_opsi)
        metode_bayar = st.selectbox("Metode Pembayaran", ["Tunai", "Transfer / QRIS", "Metode Lain"])

    with col3:
        jumlah_dana = st.number_input("Jumlah Uang Riil (Rp)", min_value=0, step=1000, format="%d", help="Masukkan jumlah uang yang benar-benar berpindah tangan hari ini.")
        submit_kas = st.button("Simpan Ke Buku Kas", use_container_width=True)

    if submit_kas:
        if jumlah_dana == 0:
            st.error("Jumlah uang tidak boleh Rp 0!")
        elif keterangan.strip() == "":
            st.error("Harap isi Keterangan Transaksi/Nama Pelanggan agar tidak bingung saat pelunasan!")
        else:
            masuk = jumlah_dana if jenis in ["Pemasukan", "Modal"] else 0
            keluar = jumlah_dana if jenis == "Pengeluaran" else 0
            
            new_row = pd.DataFrame([{
                "Tanggal": tanggal,
                "Keterangan Transaksi": keterangan,
                "Jenis": jenis,
                "Kategori Spesifik": kategori_spesifik,
                "Masuk (Rp)": masuk,
                "Keluar (Rp)": keluar,
                "Status Pembayaran": status_bayar,
                "Metode Pembayaran": metode_bayar
            }])
            
            df_update = pd.concat([df_keuangan, new_row], ignore_index=True)
            df_update.to_excel(nama_file_excel, index=False)
            st.success("Transaksi berhasil dicatat ke sistem!")
            st.rerun()

    st.divider()
    
    if not df_keuangan.empty:
        df_master = df_keuangan.copy()
        saldo_kumulatif = []
        saldo_sekarang = 0
        
        for idx, row in df_master.iterrows():
            saldo_sekarang += float(row["Masuk (Rp)"]) - float(row["Keluar (Rp)"])
            saldo_kumulatif.append(saldo_sekarang)
            
        df_master["Saldo Sisa (Rp)"] = saldo_kumulatif
        df_master["ID_Asli"] = df_master.index
        
        st.subheader("📋 Ringkasan Saldo Buku Kas Anda")
        total_uang_masuk = df_master["Masuk (Rp)"].sum()
        total_biaya_keluar = df_master["Keluar (Rp)"].sum()
        sisa_kas_bersih = total_uang_masuk - total_biaya_keluar
        
        data_ringkasan = {
            "Total Arus Uang Masuk": [f"Rp {total_uang_masuk:,.0f}"],
            "Total Pengeluaran": [f"Rp {total_biaya_keluar:,.0f}"],
            "Saldo Kas Usaha Saat Ini (Fisik)": [f"Rp {sisa_kas_bersih:,.0f}"]
        }
        st.table(pd.DataFrame(data_ringkasan))

        # --- FITUR TAMBAHAN: TABEL MONITORING DP & PIUTANG BELUM LUNAS ---
        st.markdown("### 🔍 📌 Daftar Pantau DP & Piutang Belum Lunas")
        df_belum_lunas = df_master[df_master["Status Pembayaran"].isin(["DP / Uang Muka", "Belum Lunas / Piutang"])].copy()
        
        if not df_belum_lunas.empty:
            st.warning(f"Ada {len(df_belum_lunas)} transaksi pesanan/penjualan yang statusnya belum lunas penuh. Gunakan ini sebagai pengingat tagihan.")
            df_belum_lunas.index = range(1, len(df_belum_lunas) + 1)
            df_belum_lunas_v = df_belum_lunas[["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Masuk (Rp)", "Status Pembayaran"]].copy()
            df_belum_lunas_v["Tanggal"] = df_belum_lunas_v["Tanggal"].astype(str)
            st.dataframe(df_belum_lunas_v, use_container_width=True)
        else:
            st.container()
            st.success("✅ Semua transaksi aman, tidak ada tumpukan DP/Piutang yang menggantung saat ini.")
            
        st.write("### 🟢 HISTORI DATA PEMASUKAN & MODAL")
        df_pemasukan = df_master[df_master["Jenis"].isin(["Pemasukan", "Modal"])].copy()
        if not df_pemasukan.empty:
            df_pemasukan.index = range(1, len(df_pemasukan) + 1)
            df_pemasukan.index.name = "No"
            kolom_in = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Masuk (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pemasukan_v = df_pemasukan[kolom_in].copy()
            df_pemasukan_v["Tanggal"] = df_pemasukan_v["Tanggal"].astype(str)
            st.dataframe(df_pemasukan_v, use_container_width=True)
            
        st.write("### 🔴 HISTORI DATA PENGELUARAN & BEBAN NYATA")
        df_pengeluaran = df_master[df_master["Jenis"] == "Pengeluaran"].copy()
        if not df_pengeluaran.empty:
            df_pengeluaran.index = range(1, len(df_pengeluaran) + 1)
            df_pengeluaran.index.name = "No"
            kolom_out = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Keluar (Rp)", "Saldo Sisa (Rp)", "Status Pembayaran", "Metode Pembayaran"]
            df_pengeluaran_v = df_pengeluaran[kolom_out].copy()
            df_pengeluaran_v["Tanggal"] = df_pengeluaran_v["Tanggal"].astype(str)
            st.dataframe(df_pengeluaran_v, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🗑️ Panel Hapus Transaksi")
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
        
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_master.drop(columns=["ID_Asli"]).to_excel(writer, index=False, sheet_name='Laporan_Buku_Kas')
        buffer.seek(0)
        st.download_button(
            label="📥 Download File Pembukuan Excel Toko Anda (.xlsx)",
            data=buffer,
            file_name=f"Laporan_Kas_{nama_clean}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Buku pembukuan kas Anda masih kosong.")

# ==========================================
# TAB 2: LAPORAN LABA RUGI & ANALISIS USAHA
# ==========================================
with tab2:
    st.header("📈 Analisis Laba Rugi Toko Anda")
    
    hari_ini = datetime.now().date()
    tiga_bulan_lalu = hari_ini - timedelta(days=90)
    
    pilihan_periode = st.selectbox("Pilih Rentang Laporan Keuangan:", ["Semua Periode", "3 Bulan Terakhir", "Bulan Ini Saja"])
    
    if pilihan_periode == "3 Bulan Terakhir":
        tgl_mulai = tiga_bulan_lalu
    elif pilihan_periode == "Bulan Ini Saja":
        tgl_mulai = hari_ini.replace(day=1)
    else:
        tgl_mulai = df_keuangan["Tanggal"].min() if not df_keuangan.empty else tiga_bulan_lalu
        
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
    m1.metric("Total Pemasukan (Omzet)", f"Rp {total_omzet_produk:,.0f}")
    m2.metric("Total Biaya Pengeluaran", f"Rp {total_biaya_operasional:,.0f}")
    if laba_bersih_analisis >= 0:
        m3.metric("🟢 LABA BERSIH USAHA", f"Rp {laba_bersih_analisis:,.0f}")
    else:
        m3.metric("🔴 RUGI BERSIH USAHA", f"Rp {abs(laba_bersih_analisis):,.0f}")
        
    st.divider()
    col_kiri, col_kanan = st.columns(2)
    
    with col_kiri:
        st.subheader("📊 Grafik Sumber Pendapatan")
        if total_omzet_produk > 0:
            df_pie_in = pd.DataFrame({
                "Sumber Pendapatan": ["Produk Utama", "Jasa/Komisi", "Sampingan", "Lain-lain"],
                "Jumlah (Rp)": [in_utama, in_jasa, in_sampingan, in_lain]
            })
            fig_in = px.pie(df_pie_in, values="Jumlah (Rp)", names="Sumber Pendapatan", hole=0.3)
            st.plotly_chart(fig_in, use_container_width=True)
        else:
            st.info("Belum ada data pendapatan.")

    with col_kanan:
        st.subheader("📊 Alokasi Struktur Biaya")
        if total_biaya_operasional > 0:
            df_pie_out = pd.DataFrame({
                "Kategori Pengeluaran": ["Bahan/Stok", "Operasional", "Gaji", "Alat Usaha", "Transportasi", "Lain-lain"],
                "Jumlah (Rp)": [out_bahan, out_operasional, out_gaji, out_alat, out_trans, out_lain]
            })
            fig_out = px.pie(df_pie_out, values="Jumlah (Rp)", names="Kategori Pengeluaran", hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_out, use_container_width=True)
        else:
            st.info("Belum ada data pengeluaran.")