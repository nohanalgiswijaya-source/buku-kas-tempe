import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import io
import plotly.express as px

# --- CONFIG FILE EXCEL LOKAL (100% OFFLINE AMAN) ---
nama_file_excel = "buku_kas_tempe_umkm.xlsx"

def load_data_offline():
    if os.path.exists(nama_file_excel):
        df = pd.read_excel(nama_file_excel)
        return df
    else:
        kolom = [
            "Tanggal", "Keterangan Transaksi", "Jenis", 
            "Kategori Spesifik", "Masuk (Rp)", "Keluar (Rp)", 
            "Bukti Nota", "Metode Pembayaran"
        ]
        df_baru = pd.DataFrame(columns=kolom)
        df_baru.to_excel(nama_file_excel, index=False)
        return df_baru

df_keuangan = load_data_offline()

# Normalisasi tipe data agar perhitungan matematika lancar
df_keuangan["Tanggal"] = pd.to_datetime(df_keuangan["Tanggal"]).dt.date
df_keuangan["Masuk (Rp)"] = pd.to_numeric(df_keuangan["Masuk (Rp)"]).fillna(0)
df_keuangan["Keluar (Rp)"] = pd.to_numeric(df_keuangan["Keluar (Rp)"]).fillna(0)

# --- SETTING DASHBOARD ---
st.set_page_config(page_title="Buku Kas Tempe Rumahan", layout="wide")
st.title("🧱 BUKU KAS ARUS KEUANGAN - PRODUKSI TEMPE RUMAHAN")
st.write("✨ **Versi Pembaruan** — Ditambahkan fitur Hapus Semua Histori (Clear All History).")

st.divider()

# --- MENU TAB ---
tab1, tab2 = st.tabs(["📝 Input & Histori Buku Kas", "📈 Laporan Laba/Rugi & Analisis Jualan"])

# ==========================================
# TAB 1: INPUT BUKU KAS & HISTORI
# ==========================================
with tab1:
    st.header("📝 Catat Transaksi Baru")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tanggal = st.date_input("Tanggal Transaksi", datetime.now().date(), key="tgl_kas")
        jenis = st.selectbox("Jenis (Pemasukan/Pengeluaran/Modal)", ["Pemasukan", "Pengeluaran", "Modal"])
        
        if jenis == "Pemasukan":
            kategori_opsi = ["Tempe Mentah Biasa", "Pendapatan Kripik Tempe", "Pendapatan Tempe Koro", "Lain-lain (Pemasukan)"]
        elif jenis == "Modal":
            kategori_opsi = ["Modal Awal Kas Tempe"]
        else:
            kategori_opsi = ["Bahan Baku", "Operasional Dapur", "Transportasi", "Peralatan", "Kemasan & Daun Pisang", "Lain-lain (Pengeluaran)"]
            
        kategori_spesifik = st.selectbox("Kategori Spesifik", kategori_opsi)

    with col2:
        keterangan = st.text_area("Keterangan Transaksi / Catatan Pembeli / Detail Pesanan")
        bukti_nota = st.selectbox("Bukti Nota", ["Kas masuk", "Diterima", "Pending"])
        metode_bayar = st.selectbox("Metode Pembayaran", ["Tunai", "Transfer"])

    with col3:
        jumlah_dana = st.number_input("Jumlah Uang (Rp)", min_value=0, step=1000, format="%d")
        submit_kas = st.button("Simpan Ke Buku Kas", use_container_width=True)

    if submit_kas:
        if jumlah_dana == 0:
            st.error("Jumlah uang tidak boleh Rp 0!")
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
                "Bukti Nota": bukti_nota,
                "Metode Pembayaran": metode_bayar
            }])
            
            df_update = pd.concat([df_keuangan, new_row], ignore_index=True)
            df_update.to_excel(nama_file_excel, index=False)
            st.success("Transaksi berhasil dicatat!")
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
        
        st.subheader("📋 Ringkasan Otomatis Hasil Penjualan & Biaya Produksi")
        total_uang_masuk = df_master["Masuk (Rp)"].sum()
        total_biaya_keluar = df_master["Keluar (Rp)"].sum()
        sisa_kas_bersih = total_uang_masuk - total_biaya_keluar
        
        data_ringkasan = {
            "Total Uang Masuk": [f"Rp {total_uang_masuk:,.0f}"],
            "Total Biaya Keluar": [f"Rp {total_biaya_keluar:,.0f}"],
            "Sisa Uang Kas Bersih": [f"Rp {sisa_kas_bersih:,.0f}"]
        }
        df_ringkasan_tabel = pd.DataFrame(data_ringkasan)
        st.table(df_ringkasan_tabel)
        
        st.write("### 🟢 HISTORI PEMASUKAN & MODAL MASUK")
        df_pemasukan = df_master[df_master["Jenis"].isin(["Pemasukan", "Modal"])].copy()
        if not df_pemasukan.empty:
            df_pemasukan.index = range(1, len(df_pemasukan) + 1)
            df_pemasukan.index.name = "No"
            kolom_in = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Masuk (Rp)", "Saldo Sisa (Rp)", "Bukti Nota", "Metode Pembayaran"]
            
            df_pemasukan_v = df_pemasukan[kolom_in].copy()
            df_pemasukan_v["Tanggal"] = df_pemasukan_v["Tanggal"].astype(str)
            st.dataframe(df_pemasukan_v, use_container_width=True)
        else:
            st.info("Belum ada data pemasukan tercatat.")
            
        st.write("### 🔴 HISTORI PENGELUARAN BEBAN OPERASIONAL")
        df_pengeluaran = df_master[df_master["Jenis"] == "Pengeluaran"].copy()
        if not df_pengeluaran.empty:
            df_pengeluaran.index = range(1, len(df_pengeluaran) + 1)
            df_pengeluaran.index.name = "No"
            kolom_out = ["Tanggal", "Keterangan Transaksi", "Kategori Spesifik", "Keluar (Rp)", "Saldo Sisa (Rp)", "Bukti Nota", "Metode Pembayaran"]
            
            df_pengeluaran_v = df_pengeluaran[kolom_out].copy()
            df_pengeluaran_v["Tanggal"] = df_pengeluaran_v["Tanggal"].astype(str)
            st.dataframe(df_pengeluaran_v, use_container_width=True)
        else:
            st.info("Belum ada data pengeluaran tercatat.")

        st.markdown("---")
        st.markdown("### 🗑️ Panel Hapus Transaksi")
        
        # Pilihan hapus satu per satu
        pilihan_tabel_hapus = st.radio("Pilih dari tabel mana data yang mau dihapus:", ["Tabel Pemasukan", "Tabel Pengeluaran"], horizontal=True)
        
        if pilihan_tabel_hapus == "Tabel Pemasukan" and not df_pemasukan.empty:
            no_hapus = st.number_input("Masukkan angka 'No' dari Tabel Pemasukan:", min_value=1, max_value=len(df_pemasukan), step=1)
            if st.button("Hapus Transaksi Pemasukan"):
                id_target = df_pemasukan.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_keuangan.drop(id_target).reset_index(drop=True)
                df_keuangan_baru.to_excel(nama_file_excel, index=False)
                st.success("Transaksi pemasukan berhasil dihapus!")
                st.rerun()
                
        elif pilihan_tabel_hapus == "Tabel Pengeluaran" and not df_pengeluaran.empty:
            no_hapus = st.number_input("Masukkan angka 'No' dari Tabel Pengeluaran:", min_value=1, max_value=len(df_pengeluaran), step=1)
            if st.button("Hapus Transaksi Pengeluaran"):
                id_target = df_pengeluaran.loc[no_hapus, "ID_Asli"]
                df_keuangan_baru = df_keuangan.drop(id_target).reset_index(drop=True)
                df_keuangan_baru.to_excel(nama_file_excel, index=False)
                st.success("Transaksi pengeluaran berhasil dihapus!")
                st.rerun()
        
        # 🌟 BAGIAN BARU: TOMBOL UTK CLEAR ALL HISTORY 🌟
        st.markdown("⚠️ **Zona Bahaya**")
        if st.button("❌ HAPUS SEMUA HISTORI TRANSAKSI (RESET TOTAL)", use_container_width=True):
            # Membuat dataframe kosong sesuai struktur awal
            kolom_kosong = ["Tanggal", "Keterangan Transaksi", "Jenis", "Kategori Spesifik", "Masuk (Rp)", "Keluar (Rp)", "Bukti Nota", "Metode Pembayaran"]
            df_kosong = pd.DataFrame(columns=kolom_kosong)
            df_kosong.to_excel(nama_file_excel, index=False)
            st.success("Semua histori berhasil dibersihkan! Buku kas kembali kosong.")
            st.rerun()
                
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_master.drop(columns=["ID_Asli"]).to_excel(writer, index=False, sheet_name='Buku_Kas_Total')
        buffer.seek(0)
        st.download_button(
            label="📥 Download Semua Histori Gabungan ke Excel (.xlsx)",
            data=buffer,
            file_name=f"Buku_Kas_Tempe_Gabungan_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Buku kas masih kosong.")

# ==========================================
# TAB 2: LAPORAN LABA RUGI & ANALISIS JUALAN
# ==========================================
with tab2:
    st.header("📈 Laporan Laba/Rugi & Kontribusi Produk")
    
    hari_ini = datetime.now().date()
    tiga_bulan_lalu = hari_ini - timedelta(days=90)
    
    pilihan_periode = st.selectbox("Pilih Rentang Analisis Laporan:", ["3 Bulan Terakhir", "Semua Periode", "Bulan Ini Saja"])
    
    if pilihan_periode == "3 Bulan Terakhir":
        tgl_mulai = tiga_bulan_lalu
    elif pilihan_periode == "Bulan Ini Saja":
        tgl_mulai = hari_ini.replace(day=1)
    else:
        tgl_mulai = df_keuangan["Tanggal"].min() if not df_keuangan.empty else tiga_bulan_lalu
        
    df_filtered = df_keuangan[(df_keuangan["Tanggal"] >= tgl_mulai) & (df_keuangan["Tanggal"] <= hari_ini)]
    
    # Perhitungan Omzet Produk Spesifik UMKM
    jual_mentah = df_filtered[df_filtered["Kategori Spesifik"] == "Tempe Mentah Biasa"]["Masuk (Rp)"].sum()
    jual_kripik = df_filtered[df_filtered["Kategori Spesifik"] == "Pendapatan Kripik Tempe"]["Masuk (Rp)"].sum()
    jual_koro = df_filtered[df_filtered["Kategori Spesifik"] == "Pendapatan Tempe Koro"]["Masuk (Rp)"].sum()
    jual_lain = df_filtered[df_filtered["Kategori Spesifik"] == "Lain-lain (Pemasukan)"]["Masuk (Rp)"].sum()
    
    total_omzet_produk = jual_mentah + jual_kripik + jual_koro + jual_lain
    
    # Perhitungan Biaya Operasional
    cost_bahan = df_filtered[df_filtered["Kategori Spesifik"] == "Bahan Baku"]["Keluar (Rp)"].sum()
    cost_dapur = df_filtered[df_filtered["Kategori Spesifik"] == "Operasional Dapur"]["Keluar (Rp)"].sum()
    cost_trans = df_filtered[df_filtered["Kategori Spesifik"] == "Transportasi"]["Keluar (Rp)"].sum()
    cost_alat = df_filtered[df_filtered["Kategori Spesifik"] == "Peralatan"]["Keluar (Rp)"].sum()
    cost_kemas = df_filtered[df_filtered["Kategori Spesifik"] == "Kemasan & Daun Pisang"]["Keluar (Rp)"].sum()
    cost_lain = df_filtered[df_filtered["Kategori Spesifik"] == "Lain-lain (Pengeluaran)"]["Keluar (Rp)"].sum()
    
    total_biaya_operasional = cost_bahan + cost_dapur + cost_trans + cost_alat + cost_kemas + cost_lain
    laba_bersih_analisis = total_omzet_produk - total_biaya_operasional
    
    # Ringkasan Angka Metrik di Laporan
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Pemasukan (Omzet)", f"Rp {total_omzet_produk:,.0f}")
    m2.metric("Total Pengeluaran Beban", f"Rp {total_biaya_operasional:,.0f}")
    if laba_bersih_analisis >= 0:
        m3.metric("🟢 LABA BERSIH", f"Rp {laba_bersih_analisis:,.0f}")
    else:
        m3.metric("🔴 RUGI BERSIH", f"Rp {abs(laba_bersih_analisis):,.0f}")
        
    st.divider()
    col_kiri, col_kanan = st.columns(2)
    
    with col_kiri:
        st.subheader("📊 Analisis Hasil Jualan Tempe")
        p_mentah = (jual_mentah / total_omzet_produk * 100) if total_omzet_produk > 0 else 0
        p_kripik = (jual_kripik / total_omzet_produk * 100) if total_omzet_produk > 0 else 0
        p_koro = (jual_koro / total_omzet_produk * 100) if total_omzet_produk > 0 else 0
        p_lain_in = (jual_lain / total_omzet_produk * 100) if total_omzet_produk > 0 else 0
        
        tabel_produk = {
            "Kategori Produk Tempe": ["Tempe Mentah Biasa", "Pendapatan Kripik Tempe", "Pendapatan Tempe Koro", "Lain-lain (Pemasukan)", "Total Penghasilan"],
            "Total Omzet Penjualan (Rp)": [f"Rp {jual_mentah:,.0f}", f"Rp {jual_kripik:,.0f}", f"Rp {jual_koro:,.0f}", f"Rp {jual_lain:,.0f}", f"Rp {total_omzet_produk:,.0f}"],
            "Persentase Kontribusi": [f"{p_mentah:.1f}%", f"{p_kripik:.1f}%", f"{p_koro:.1f}%", f"{p_lain_in:.1f}%", "100%"]
        }
        st.table(pd.DataFrame(tabel_produk))
        
        if total_omzet_produk > 0:
            df_pie_in = pd.DataFrame({
                "Produk": ["Tempe Mentah Biasa", "Pendapatan Kripik Tempe", "Pendapatan Tempe Koro", "Lain-lain"],
                "Nilai": [jual_mentah, jual_kripik, jual_koro, jual_lain]
            })
            fig_in = px.pie(df_pie_in, values="Nilai", names="Produk", title="Bagan Lingkaran Kontribusi Pendapatan", hole=0.2)
            st.plotly_chart(fig_in, use_container_width=True)
        else:
            st.info("Belum ada omzet untuk menampilkan bagan lingkaran jualan.")

    with col_kanan:
        st.subheader("🍕 Alokasi Biaya Produksi")
        p_bahan = (cost_bahan / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        p_dapur = (cost_dapur / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        p_trans = (cost_trans / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        p_alat = (cost_alat / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        p_kemas = (cost_kemas / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        p_lain_out = (cost_lain / total_biaya_operasional * 100) if total_biaya_operasional > 0 else 0
        
        tabel_biaya = {
            "Kategori Biaya Operasional": ["Bahan Baku", "Operasional Dapur", "Transportasi", "Peralatan", "Kemasan & Daun Pisang", "Lain-lain (Pengeluaran)", "Total Beban"],
            "Total Biaya (Rp)": [f"Rp {cost_bahan:,.0f}", f"Rp {cost_dapur:,.0f}", f"Rp {cost_trans:,.0f}", f"Rp {cost_alat:,.0f}", f"Rp {cost_kemas:,.0f}", f"Rp {cost_lain:,.0f}", f"Rp {total_biaya_operasional:,.0f}"],
            "Persentase Beban": [f"{p_bahan:.1f}%", f"{p_dapur:.1f}%", f"{p_trans:.1f}%", f"{p_alat:.1f}%", f"{p_kemas:.1f}%", f"{p_lain_out:.1f}%", "100%"]
        }
        st.table(pd.DataFrame(tabel_biaya))
        
        if total_biaya_operasional > 0:
            df_pie_out = pd.DataFrame({
                "Biaya": ["Bahan Baku", "Operasional Dapur", "Transportasi", "Peralatan", "Kemasan & Daun Pisang", "Lain-lain"],
                "Nilai": [cost_bahan, cost_dapur, cost_trans, cost_alat, cost_kemas, cost_lain]
            })
            fig_out = px.pie(df_pie_out, values="Nilai", names="Biaya", title="Bagan Lingkaran Alokasi Pengeluaran", hole=0.2)
            st.plotly_chart(fig_out, use_container_width=True)
        else:
            st.info("Belum ada pengeluaran untuk menampilkan bagan lingkaran biaya.")