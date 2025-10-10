import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import json

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Retail Sevkiyat Planlama",
    page_icon="📦",
    layout="wide"
)

# Session state başlatma
if 'urun_master' not in st.session_state:
    st.session_state.urun_master = None
if 'magaza_master' not in st.session_state:
    st.session_state.magaza_master = None
if 'yasak_master' not in st.session_state:
    st.session_state.yasak_master = None
if 'depo_stok' not in st.session_state:
    st.session_state.depo_stok = None
if 'anlik_stok_satis' not in st.session_state:
    st.session_state.anlik_stok_satis = None
if 'haftalik_trend' not in st.session_state:
    st.session_state.haftalik_trend = None
if 'kpi' not in st.session_state:
    st.session_state.kpi = None
if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }
if 'target_matrix' not in st.session_state:
    st.session_state.target_matrix = None
if 'sisme_orani' not in st.session_state:
    st.session_state.sisme_orani = None
if 'genlestirme_orani' not in st.session_state:
    st.session_state.genlestirme_orani = None
if 'min_oran' not in st.session_state:
    st.session_state.min_oran = None
if 'siralama_data' not in st.session_state:
    st.session_state.siralama_data = None
if 'sevkiyat_sonuc' not in st.session_state:
    st.session_state.sevkiyat_sonuc = None
if 'yeni_urun_listesi' not in st.session_state:
    st.session_state.yeni_urun_listesi = None

# Sidebar menü
st.sidebar.title("📦 Sevkiyat Planlama")
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "📤 Veri Yükleme", "🎯 Segmentasyon Ayarları", 
     "🎲 Hedef Matris", "📊 Sıralama", "🚚 Sevkiyat Hesaplama", "🆕 Yeni Ürün Sevkiyatı", "📈 Raporlar"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================
if menu == "🏠 Ana Sayfa":
    st.title("🏠 Retail Sevkiyat Planlama Sistemi")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Ürün Master", 
            len(st.session_state.urun_master) if st.session_state.urun_master is not None else 0
        )
    
    with col2:
        st.metric(
            "Mağaza Master", 
            len(st.session_state.magaza_master) if st.session_state.magaza_master is not None else 0
        )
    
    with col3:
        st.metric(
            "Anlık Stok/Satış", 
            "✅" if st.session_state.anlik_stok_satis is not None else "❌"
        )
    
    with col4:
        st.metric(
            "Matris Durumu",
            "✅" if st.session_state.target_matrix is not None else "❌"
        )
    
    st.markdown("### 📋 İşlem Adımları")
    st.info("""
    1. **Veri Yükleme**: Tüm CSV dosyalarını yükleyin (Ürün Master, Mağaza Master, Yasak, Depo Stok, Anlık Stok/Satış, Haftalık Trend, KPI)
    2. **Segmentasyon Ayarları**: Ürün ve mağaza gruplama aralıklarını belirleyin
    3. **Hedef Matris**: Her segment için şişme oranı, genleştirme oranı ve min oranı girin
    4. **Sıralama**: Mağaza ve ürün cluster önceliklerini belirleyin
    5. **Sevkiyat Hesaplama**: Sonuçları görüntüleyin ve export edin
    """)

# ============================================
# 📤 VERİ YÜKLEME (ESKİ KLASMAN PARAMETRELERİ)
# ============================================
elif menu == "📤 Veri Yükleme":
    st.title("📤 Veri Yükleme")
    st.markdown("---")
    
    # Tüm örnek CSV'leri indirme butonu - Gizlenebilir
    with st.expander("📥 Örnek CSV'leri İndir", expanded=False):
        st.info("Tüm örnek CSV dosyalarını aşağıdan indirebilirsiniz.")
        
        # Örnek CSV'ler oluştur
        example_csvs = {
            'urun_master.csv': pd.DataFrame({
                'urun_kod': ['U001', 'U002', 'U003'],
                'urun_ad': ['Ürün A', 'Ürün B', 'Ürün C'],
                'satici_kod': ['S001', 'S002', 'S001'],
                'satici_ad': ['Satıcı 1', 'Satıcı 2', 'Satıcı 1'],
                'kategori_kod': ['K001', 'K002', 'K001'],
                'kategori_ad': ['Kategori 1', 'Kategori 2', 'Kategori 1'],
                'umg': ['UMG1', 'UMG2', 'UMG1'],
                'umg_ad': ['Üst Mal Grubu 1', 'Üst Mal Grubu 2', 'Üst Mal Grubu 1'],
                'mg': ['MG1', 'MG2', 'MG1'],
                'mg_ad': ['Mal Grubu 1', 'Mal Grubu 2', 'Mal Grubu 1'],
                'marka_kod': ['M001', 'M002', 'M001'],
                'marka_ad': ['Marka A', 'Marka B', 'Marka A'],
                'nitelik': ['Nitelik 1', 'Nitelik 2', 'Nitelik 1'],
                'durum': ['Aktif', 'Aktif', 'Pasif'],
                'ithal': [1, 0, 1],
                'ithal_ad': ['İthal', 'Yerli', 'İthal'],
                'tanim': ['Tanım 1', 'Tanım 2', 'Tanım 3']
            }),
            'magaza_master.csv': pd.DataFrame({
                'magaza_kod': ['M001', 'M002', 'M003'],
                'magaza_ad': ['Mağaza A', 'Mağaza B', 'Mağaza C'],
                'il': ['İstanbul', 'Ankara', 'İzmir'],
                'bolge': ['Marmara', 'İç Anadolu', 'Ege'],
                'tip': ['Hipermarket', 'Süpermarket', 'Hipermarket'],
                'adres_kod': ['ADR001', 'ADR002', 'ADR003'],
                'sm': [5000, 3000, 4500],
                'bs': ['BS1', 'BS2', 'BS1'],
                'depo_kod': ['D001', 'D001', 'D002']
            }),
            'yasak.csv': pd.DataFrame({
                'urun_kod': ['U001', 'U002'],
                'urun_ad': ['Ürün A', 'Ürün B'],
                'magaza_kod': ['M002', 'M001'],
                'magaza_ad': ['Mağaza B', 'Mağaza A'],
                'yasak_durum': ['Yasak', 'Yasak']
            }),
            'depo_stok.csv': pd.DataFrame({
                'depo_kod': ['D001', 'D001', 'D002'],
                'depo_ad': ['Depo Merkez', 'Depo Merkez', 'Depo Bölge'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'urun_ad': ['Ürün A', 'Ürün B', 'Ürün A'],
                'stok': [1000, 1500, 800]
            }),
            'anlik_stok_satis.csv': pd.DataFrame({
                'magaza_kod': ['M001', 'M001', 'M002'],
                'magaza_ad': ['Mağaza A', 'Mağaza A', 'Mağaza B'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'urun_ad': ['Ürün A', 'Ürün B', 'Ürün A'],
                'klasman_kod': ['K1', 'K2', 'K1'],
                'klasman_ad': ['Klasman A', 'Klasman B', 'Klasman A'],
                'marka_kod': ['M001', 'M002', 'M001'],
                'marka_ad': ['Marka A', 'Marka B', 'Marka A'],
                'stok': [100, 150, 120],
                'yol': [20, 30, 25],
                'satis': [50, 40, 45],
                'ciro': [5000, 6000, 5500],
                'smm': [2.0, 3.75, 2.67]
            }),
            'haftalik_trend.csv': pd.DataFrame({
                'klasman_kod': ['K1', 'K1', 'K2'],
                'klasman_ad': ['Klasman A', 'Klasman A', 'Klasman B'],
                'marka_kod': ['M001', 'M001', 'M002'],
                'marka_ad': ['Marka A', 'Marka A', 'Marka B'],
                'yil': [2025, 2025, 2025],
                'hafta': [40, 41, 40],
                'stok': [10000, 9500, 15000],
                'satis': [2000, 2100, 1800],
                'ciro': [200000, 210000, 270000],
                'smm': [5.0, 4.52, 8.33],
                'iftutar': [1000000, 950000, 1500000]
            }),
            'kpi.csv': pd.DataFrame({
                'mg_id': ['MG1', 'MG2', 'MG3'],
                'mg_ad': ['Mal Grubu 1', 'Mal Grubu 2', 'Mal Grubu 3'],
                'min_deger': [0, 100, 500],
                'max_deger': [99, 499, 999],
                'forward_cover': [1.5, 2.0, 2.5]
            })
        }
        
        # Her CSV için ayrı indirme butonu
        cols = st.columns(4)
        for idx, (filename, df) in enumerate(example_csvs.items()):
            with cols[idx % 4]:
                st.download_button(
                    label=f"📥 {filename}",
                    data=df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name=filename,
                    mime="text/csv",
                    key=f"download_{filename}"
                )
    
    st.markdown("---")
    
    # CSV Yükleme Bölümleri
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Ürün Master", "Mağaza Master", "Yasak", "Depo Stok", 
        "Anlık Stok/Satış", "Haftalık Trend", "KPI"
    ])
    
    # 1. ÜRÜN MASTER
    with tab1:
        st.subheader("📦 Ürün Master")
        st.info("Kolonlar: urun_kod, urun_ad, satici_kod, satici_ad, kategori_kod, kategori_ad, umg, umg_ad, mg, mg_ad, marka_kod, marka_ad, nitelik, durum, ithal, ithal_ad, tanim")
        
        uploaded = st.file_uploader("Ürün Master CSV yükle", type=['csv'], key="urun_master_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['urun_kod', 'urun_ad', 'satici_kod', 'satici_ad', 'kategori_kod', 
                                'kategori_ad', 'umg', 'umg_ad', 'mg', 'mg_ad', 'marka_kod', 
                                'marka_ad', 'nitelik', 'durum', 'ithal', 'ithal_ad', 'tanim']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.urun_master = df
                    st.success(f"✅ {len(df)} ürün yüklendi!")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.urun_master is not None:
            st.dataframe(st.session_state.urun_master.head(10), use_container_width=True, height=400)
    
    # 2. MAĞAZA MASTER
    with tab2:
        st.subheader("🏪 Mağaza Master")
        st.info("Kolonlar: magaza_kod, magaza_ad, il, bolge, tip, adres_kod, sm, bs, depo_kod")
        
        uploaded = st.file_uploader("Mağaza Master CSV yükle", type=['csv'], key="magaza_master_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['magaza_kod', 'magaza_ad', 'il', 'bolge', 'tip', 'adres_kod', 'sm', 'bs', 'depo_kod']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.magaza_master = df
                    st.success(f"✅ {len(df)} mağaza yüklendi!")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.magaza_master is not None:
            st.dataframe(st.session_state.magaza_master.head(10), use_container_width=True, height=400)
    
    # 3. YASAK
    with tab3:
        st.subheader("🚫 Yasak Master")
        st.info("Kolonlar: urun_kod, urun_ad, magaza_kod, magaza_ad, yasak_durum")
        
        uploaded = st.file_uploader("Yasak CSV yükle", type=['csv'], key="yasak_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['urun_kod', 'urun_ad', 'magaza_kod', 'magaza_ad', 'yasak_durum']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.yasak_master = df
                    st.success(f"✅ {len(df)} yasak kaydı yüklendi!")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.yasak_master is not None:
            st.dataframe(st.session_state.yasak_master.head(10), use_container_width=True, height=400)
    
    # 4. DEPO STOK
    with tab4:
        st.subheader("📦 Depo Stok")
        st.info("Kolonlar: depo_kod, depo_ad, urun_kod, urun_ad, stok")
        
        uploaded = st.file_uploader("Depo Stok CSV yükle", type=['csv'], key="depo_stok_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['depo_kod', 'depo_ad', 'urun_kod', 'urun_ad', 'stok']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.depo_stok = df
                    st.success(f"✅ {len(df)} depo stok kaydı yüklendi!")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.depo_stok is not None:
            st.dataframe(st.session_state.depo_stok.head(10), use_container_width=True, height=400)
    
    # 5. ANLIK STOK SATIŞ
    with tab5:
        st.subheader("📊 Anlık Stok/Satış")
        st.info("Kolonlar: magaza_kod, magaza_ad, urun_kod, urun_ad, klasman_kod, klasman_ad, marka_kod, marka_ad, stok, yol, satis, ciro, smm")
        
        uploaded = st.file_uploader("Anlık Stok/Satış CSV yükle", type=['csv'], key="anlik_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['magaza_kod', 'magaza_ad', 'urun_kod', 'urun_ad', 'klasman_kod', 
                                'klasman_ad', 'marka_kod', 'marka_ad', 'stok', 'yol', 'satis', 'ciro', 'smm']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.anlik_stok_satis = df
                    st.success(f"✅ {len(df)} kayıt yüklendi!")
                    
                    # Özet bilgiler
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Toplam Mağaza", df['magaza_kod'].nunique())
                    with col2:
                        st.metric("Toplam Ürün", df['urun_kod'].nunique())
                    with col3:
                        st.metric("Ortalama SMM", f"{df['smm'].mean():.2f}")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.anlik_stok_satis is not None:
            st.dataframe(st.session_state.anlik_stok_satis.head(10), use_container_width=True, height=400)
    
    # 6. HAFTALIK TREND
    with tab6:
        st.subheader("📈 Haftalık Trend")
        st.info("Kolonlar: klasman_kod, klasman_ad, marka_kod, marka_ad, yil, hafta, stok, satis, ciro, smm, iftutar")
        
        uploaded = st.file_uploader("Haftalık Trend CSV yükle", type=['csv'], key="haftalik_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['klasman_kod', 'klasman_ad', 'marka_kod', 'marka_ad', 'yil', 
                                'hafta', 'stok', 'satis', 'ciro', 'smm', 'iftutar']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.haftalik_trend = df
                    st.success(f"✅ {len(df)} haftalık veri yüklendi!")
                    
                    # İlk 10 satırı tam ekran göster
                    st.dataframe(df.head(10), use_container_width=True, height=400)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.haftalik_trend is not None:
            st.dataframe(st.session_state.haftalik_trend.head(10), use_container_width=True, height=400)
    
    # 7. KPI
    with tab7:
        st.subheader("🎯 KPI Parametreleri")
        st.info("Kolonlar: mg_id, mg_ad, min_deger, max_deger, forward_cover")
        
        uploaded = st.file_uploader("KPI CSV yükle", type=['csv'], key="kpi_upload")
        
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                required_cols = ['mg_id', 'mg_ad', 'min_deger', 'max_deger', 'forward_cover']
                
                if all(col in df.columns for col in required_cols):
                    st.session_state.kpi = df
                    st.success(f"✅ {len(df)} KPI kaydı yüklendi!")
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        
        if st.session_state.kpi is not None:
            edited_df = st.data_editor(
                st.session_state.kpi,
                num_rows="dynamic",
                use_container_width=True,
                height=300,
                column_config={
                    "forward_cover": st.column_config.NumberColumn(
                        "Forward Cover",
                        min_value=0.0,
                        format="%.2f"
                    )
                }
            )
            if st.button("💾 Değişiklikleri Kaydet", key="save_kpi"):
                st.session_state.kpi = edited_df
                st.success("✅ Kaydedildi!")
                st.rerun()

# ============================================
# 🎯 SEGMENTASYON AYARLARI
# ============================================
elif menu == "🎯 Segmentasyon Ayarları":
    st.title("🎯 Segmentasyon Ayarları")
    st.markdown("---")
    
    st.info("**Stok/Satış oranına göre** ürün ve mağazaları gruplandırma (Toplam Stok / Toplam Satış)")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
        st.stop()
    
    # Ürün bazında toplam stok/satış hesapla
    data = st.session_state.anlik_stok_satis.copy()
    
    # Ürün bazında gruplama - Toplam Stok / Toplam Satış
    urun_aggregated = data.groupby('urun_kod').agg({
        'stok': 'sum',
        'satis': 'sum'
    }).reset_index()
    urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
    
    # Mağaza bazında gruplama - Toplam Stok / Toplam Satış
    magaza_aggregated = data.groupby('magaza_kod').agg({
        'stok': 'sum',
        'satis': 'sum'
    }).reset_index()
    magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
    
    st.markdown("### 📊 Hesaplanan Oranlar")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ortalama Ürün Oran", f"{urun_aggregated['stok_satis_orani'].mean():.2f}")
    with col2:
        st.metric("Ortalama Mağaza Oran", f"{magaza_aggregated['stok_satis_orani'].mean():.2f}")
    
    st.markdown("---")
    
    # Ürün segmentasyonu
    st.subheader("🏷️ Ürün Segmentasyonu (Toplam Stok / Toplam Satış)")
    
    use_default_product = st.checkbox("Varsayılan aralıkları kullan (Ürün)", value=True)
    
    if use_default_product:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        product_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6)
        
        product_ranges = []
        for i in range(num_ranges):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"prod_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges-1 else 999, key=f"prod_max_{i}")
            product_ranges.append((min_val, max_val))
    
    # Ürün segmentasyonunu önizle
    if urun_aggregated is not None and len(urun_aggregated) > 0:
        temp_prod = urun_aggregated.copy()
        temp_prod['segment'] = pd.cut(
            temp_prod['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in product_ranges],
            include_lowest=True
        )
        st.write("**Ürün Dağılımı Önizleme:**")
        st.dataframe(temp_prod['segment'].value_counts().sort_index(), use_container_width=True)
    
    st.markdown("---")
    
    # Mağaza segmentasyonu
    st.subheader("🏪 Mağaza Segmentasyonu (Toplam Stok / Toplam Satış)")
    
    use_default_store = st.checkbox("Varsayılan aralıkları kullan (Mağaza)", value=True)
    
    if use_default_store:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        store_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges_store = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6, key="store_ranges")
        
        store_ranges = []
        for i in range(num_ranges_store):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"store_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges_store-1 else 999, key=f"store_max_{i}")
            store_ranges.append((min_val, max_val))
    
    # Mağaza segmentasyonunu önizle
    if magaza_aggregated is not None and len(magaza_aggregated) > 0:
        temp_store = magaza_aggregated.copy()
        temp_store['segment'] = pd.cut(
            temp_store['stok_satis_orani'], 
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in store_ranges],
            include_lowest=True
        )
        st.write("**Mağaza Dağılımı Önizleme:**")
        st.dataframe(temp_store['segment'].value_counts().sort_index(), use_container_width=True)
    
    if st.button("💾 Segmentasyon Ayarlarını Kaydet", type="primary"):
        st.session_state.segmentation_params = {
            'product_ranges': product_ranges,
            'store_ranges': store_ranges
        }
        st.success("✅ Ayarlar kaydedildi!")

# ============================================
# 🎲 HEDEF MATRİS (YENİ TASARIM)
# ============================================
elif menu == "🎲 Hedef Matris":
    st.title("🎲 Hedef Matris Parametreleri")
    st.markdown("---")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
    else:
        # Segmentasyon yap
        data = st.session_state.anlik_stok_satis.copy()
        
        # Ürün bazında toplam stok/satış
        urun_aggregated = data.groupby('urun_kod').agg({
            'stok': 'sum',
            'satis': 'sum'
        }).reset_index()
        urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
        
        # Mağaza bazında toplam stok/satış
        magaza_aggregated = data.groupby('magaza_kod').agg({
            'stok': 'sum',
            'satis': 'sum'
        }).reset_index()
        magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
        
        # Ürün segmentasyonu
        product_ranges = st.session_state.segmentation_params['product_ranges']
        urun_aggregated['urun_segment'] = pd.cut(
            urun_aggregated['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in product_ranges],
            include_lowest=True
        )
        
        # Mağaza segmentasyonu
        store_ranges = st.session_state.segmentation_params['store_ranges']
        magaza_aggregated['magaza_segment'] = pd.cut(
            magaza_aggregated['stok_satis_orani'],
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in store_ranges],
            include_lowest=True
        )
        
        # Segmentasyon sonuçları
        st.subheader("📊 Segmentasyon Sonuçları")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Ürün Dağılımı**")
            prod_dist = urun_aggregated['urun_segment'].value_counts().sort_index()
            st.dataframe(prod_dist, use_container_width=True)
        
        with col2:
            st.write("**Mağaza Dağılımı**")
            store_dist = magaza_aggregated['magaza_segment'].value_counts().sort_index()
            st.dataframe(store_dist, use_container_width=True)
        
        st.markdown("---")
        
        # Matris seçimi ve parametreler
        st.subheader("🎯 Matris Parametreleri")
        
        prod_segments = sorted([str(x) for x in urun_aggregated['urun_segment'].unique() if pd.notna(x)])
        store_segments = sorted([str(x) for x in magaza_aggregated['magaza_segment'].unique() if pd.notna(x)])
        
        # 1. ŞİŞME ORANI MATRİSİ
        st.markdown("### 1️⃣ Şişme Oranı Matrisi (Default: 0.5)")
        
        if st.session_state.sisme_orani is None:
            sisme_data = pd.DataFrame(
                0.5,  # Default değer
                index=prod_segments,
                columns=store_segments
            )
        else:
            sisme_data = st.session_state.sisme_orani
        
        edited_sisme = st.data_editor(
            sisme_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col,
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.2f"
            ) for col in store_segments},
            key="sisme_matrix"
        )
        
        st.markdown("---")
        
        # 2. GENLEŞTİRME ORANI MATRİSİ
        st.markdown("### 2️⃣ Genleştirme Oranı Matrisi (Default: 1.0)")
        
        if st.session_state.genlestirme_orani is None:
            genlestirme_data = pd.DataFrame(
                1.0,  # Default değer
                index=prod_segments,
                columns=store_segments
            )
        else:
            genlestirme_data = st.session_state.genlestirme_orani
        
        edited_genlestirme = st.data_editor(
            genlestirme_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col,
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.2f"
            ) for col in store_segments},
            key="genlestirme_matrix"
        )
        
        st.markdown("---")
        
        # 3. MIN ORAN MATRİSİ
        st.markdown("### 3️⃣ Min Oran Matrisi (Default: 1.0)")
        
        if st.session_state.min_oran is None:
            min_oran_data = pd.DataFrame(
                1.0,  # Default değer
                index=prod_segments,
                columns=store_segments
            )
        else:
            min_oran_data = st.session_state.min_oran
        
        edited_min_oran = st.data_editor(
            min_oran_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col,
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.2f"
            ) for col in store_segments},
            key="min_oran_matrix"
        )
        
        st.markdown("---")
        
        # Kaydet butonu
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Tüm Matrisleri Kaydet", type="primary"):
                st.session_state.sisme_orani = edited_sisme
                st.session_state.genlestirme_orani = edited_genlestirme
                st.session_state.min_oran = edited_min_oran
                st.success("✅ Tüm matrisler kaydedildi!")

# ============================================
# 📊 SIRALAMA
# ============================================
elif menu == "📊 Sıralama":
    st.title("📊 Sıralama Öncelikleri")
    st.markdown("---")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
    else:
        st.info("Mağaza ve ürün cluster bazında sevkiyat önceliklerini belirleyin")
        
        # Segmentleri al
        data = st.session_state.anlik_stok_satis.copy()
        
        # Ürün bazında toplam stok/satış
        urun_aggregated = data.groupby('urun_kod').agg({
            'stok': 'sum',
            'satis': 'sum'
        }).reset_index()
        urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
        
        # Mağaza bazında toplam stok/satış
        magaza_aggregated = data.groupby('magaza_kod').agg({
            'stok': 'sum',
            'satis': 'sum'
        }).reset_index()
        magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
        
        # Ürün segmentasyonu
        product_ranges = st.session_state.segmentation_params['product_ranges']
        urun_aggregated['urun_segment'] = pd.cut(
            urun_aggregated['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in product_ranges],
            include_lowest=True
        )
        
        # Mağaza segmentasyonu
        store_ranges = st.session_state.segmentation_params['store_ranges']
        magaza_aggregated['magaza_segment'] = pd.cut(
            magaza_aggregated['stok_satis_orani'],
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in store_ranges],
            include_lowest=True
        )
        
        prod_segments = sorted([str(x) for x in urun_aggregated['urun_segment'].unique() if pd.notna(x)])
        store_segments = sorted([str(x) for x in magaza_aggregated['magaza_segment'].unique() if pd.notna(x)])
        
        # Sıralama tablosu oluştur
        st.subheader("🎯 Öncelik Sıralaması")
        
        st.info("""
        **RPT (Rapidity):** Hızlı sevkiyat önceliği - Ürünler hızlı bir şekilde dağıtılır
        **Min:** Minimum stok önceliği - Stok seviyesi düşük olan önceliklendirilir
        
        Her kombinasyon için RPT ve Min öncelikleri sırayla oluşturulur.
        Örnek: Mağaza 0-4, Ürün 0-4 → RPT:1, Min:2
        """)
        
        # Eğer daha önce kaydedilmişse onu kullan, yoksa tüm kombinasyonları oluştur
        if st.session_state.siralama_data is not None:
            siralama_df = st.session_state.siralama_data
        else:
            # Segmentleri doğru sıraya koy
            def sort_segments(segments):
                """Segmentleri sayısal değere göre sırala"""
                def get_sort_key(seg):
                    # "0-4" gibi string'den ilk sayıyı al
                    try:
                        return int(seg.split('-')[0])
                    except:
                        return 999  # inf veya parse edilemeyenler sona
                return sorted(segments, key=get_sort_key)
            
            sorted_store_segments = sort_segments(store_segments)
            sorted_prod_segments = sort_segments(prod_segments)
            
            # Tüm kombinasyonları oluştur - Her kombinasyon için RPT ve Min
            siralama_rows = []
            oncelik_counter = 1
            for store_seg in sorted_store_segments:
                for prod_seg in sorted_prod_segments:
                    # RPT
                    siralama_rows.append({
                        'Magaza_Cluster': store_seg,
                        'Urun_Cluster': prod_seg,
                        'Durum': 'RPT',
                        'Oncelik': oncelik_counter
                    })
                    oncelik_counter += 1
                    
                    # Min
                    siralama_rows.append({
                        'Magaza_Cluster': store_seg,
                        'Urun_Cluster': prod_seg,
                        'Durum': 'Min',
                        'Oncelik': oncelik_counter
                    })
                    oncelik_counter += 1
            
            siralama_df = pd.DataFrame(siralama_rows)
        
        st.markdown("---")
        st.subheader("📋 Tüm Kombinasyonlar (Elle Düzenlenebilir)")
        
        # Düzenlenebilir tablo - Tüm kombinasyonlar
        edited_siralama = st.data_editor(
            siralama_df.sort_values('Oncelik').reset_index(drop=True),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Magaza_Cluster": st.column_config.SelectboxColumn(
                    "Mağaza Cluster",
                    help="Mağaza segmenti seçin",
                    options=store_segments,
                    required=True
                ),
                "Urun_Cluster": st.column_config.SelectboxColumn(
                    "Ürün Cluster",
                    help="Ürün segmenti seçin",
                    options=prod_segments,
                    required=True
                ),
                "Durum": st.column_config.SelectboxColumn(
                    "Durum",
                    help="RPT (Hızlı sevkiyat) veya Min (Minimum stok)",
                    options=["RPT", "Min"],
                    required=True
                ),
                "Oncelik": st.column_config.NumberColumn(
                    "Öncelik",
                    help="Öncelik sırası (1 = en yüksek öncelik)",
                    min_value=1,
                    max_value=1000,
                    step=1,
                    format="%d"
                )
            },
            hide_index=False,
            height=500
        )
        
        # Kaydet
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Sıralamayı Kaydet", type="primary"):
                st.session_state.siralama_data = edited_siralama
                st.success("✅ Sıralama öncelikleri kaydedildi!")
        
        with col2:
            if st.button("🔄 Varsayılana Sıfırla"):
                st.session_state.siralama_data = None
                st.success("✅ Varsayılan değerlere sıfırlandı!")
                st.rerun()

elif menu == "🚚 Sevkiyat Hesaplama":
    st.title("🚚 Sevkiyat Hesaplama")
    st.markdown("---")
    
    # Tüm verilerin yüklenip yüklenmediğini kontrol et
    required_data = {
        "Ürün Master": st.session_state.urun_master,
        "Mağaza Master": st.session_state.magaza_master,
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi,
        "Şişme Oranı": st.session_state.sisme_orani,
        "Genleştirme Oranı": st.session_state.genlestirme_orani,
        "Min Oran": st.session_state.min_oran,
        "Sıralama": st.session_state.siralama_data
    }
    
    # Haftalık trend opsiyonel
    optional_data = {
        "Haftalık Trend": st.session_state.haftalik_trend,
        "Yasak Master": st.session_state.yasak_master
    }    
    
    missing_data = [name for name, data in required_data.items() if data is None]
    optional_loaded = [name for name, data in optional_data.items() if data is not None]
    
    if missing_data:
        st.warning("⚠️ Tüm zorunlu adımları tamamlayın!")
        st.error(f"**Eksik veriler:** {', '.join(missing_data)}")
        st.info("""
        Tamamlanması gereken zorunlu adımlar:
        - ✅ Veri Yükleme (Ürün Master, Mağaza Master, Depo Stok, Anlık Stok/Satış, KPI)
        - ✅ Segmentasyon Ayarları
        - ✅ Hedef Matris (Tüm 3 matris)
        - ✅ Sıralama Öncelikleri
        
        Opsiyonel veriler:
        - Haftalık Trend (zorunlu değil)
        - Yasak Master (zorunlu değil)
        """)
        
        if optional_loaded:
            st.success(f"✅ Yüklenmiş opsiyonel veriler: {', '.join(optional_loaded)}")
    else:
        st.success("✅ Tüm zorunlu veriler hazır! Hesaplama yapılabilir.")
        
        if optional_loaded:
            st.info(f"📌 Yüklenmiş opsiyonel veriler: {', '.join(optional_loaded)}")
        
        # Hesaplama özet bilgileri
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Toplam Ürün", st.session_state.anlik_stok_satis['urun_kod'].nunique())
        with col2:
            st.metric("Toplam Mağaza", st.session_state.anlik_stok_satis['magaza_kod'].nunique())
        with col3:
            st.metric("Toplam Depo Stok", f"{st.session_state.depo_stok['stok'].sum():,.0f}")
        with col4:
            yasak_count = len(st.session_state.yasak_master) if st.session_state.yasak_master is not None else 0
            st.metric("Yasak Kombinasyon", yasak_count)
        
        # Depo-Mağaza eşleşme kontrolü
        st.markdown("---")
        st.subheader("🏢 Depo-Mağaza Eşleşmeleri")
        
        magaza_depo = st.session_state.magaza_master[['magaza_kod', 'magaza_ad', 'depo_kod']].copy()
        st.dataframe(magaza_depo, use_container_width=True, height=200)
        st.info("ℹ️ Her mağaza sadece kendi depo_kod'una atanmış depodan mal alabilir.")
        
        st.markdown("---")
        
        # Hesaplama butonu
        if st.button("🚀 Sevkiyat Hesapla", type="primary", use_container_width=True):
            with st.spinner("📊 Hesaplama yapılıyor... Bu işlem birkaç dakika sürebilir."):
                
                progress_bar = st.progress(0)
                st.write("⏳ Adım 1/6: Veri hazırlanıyor...")
                progress_bar.progress(15)
                
                # Veri hazırlama
                anlik_df = st.session_state.anlik_stok_satis.copy()
                magaza_df = st.session_state.magaza_master.copy()
                depo_df = st.session_state.depo_stok.copy()
                kpi_df = st.session_state.kpi.copy()
                siralama_df = st.session_state.siralama_data.copy()
                
                st.write("⏳ Adım 2/6: Segmentasyon yapılıyor...")
                progress_bar.progress(30)
                
                # Mağaza ve ürün bazında toplam stok/satış hesapla
                urun_agg = anlik_df.groupby('urun_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                urun_agg['cover'] = urun_agg['stok'] / urun_agg['satis'].replace(0, 1)
                
                magaza_agg = anlik_df.groupby('magaza_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                magaza_agg['cover'] = magaza_agg['stok'] / magaza_agg['satis'].replace(0, 1)
                
                # Segmentlere ata
                product_ranges = st.session_state.segmentation_params['product_ranges']
                store_ranges = st.session_state.segmentation_params['store_ranges']
                
                # Segment etiketlerini string olarak oluştur
                product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
                store_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
                
                urun_agg['segment'] = pd.cut(
                    urun_agg['cover'],
                    bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
                    labels=product_labels,
                    include_lowest=True
                )
                
                magaza_agg['segment'] = pd.cut(
                    magaza_agg['cover'],
                    bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
                    labels=store_labels,
                    include_lowest=True
                )
                
                # Ana veri ile birleştir
                anlik_df = anlik_df.merge(
                    urun_agg[['urun_kod', 'segment']], 
                    on='urun_kod', 
                    how='left'
                ).rename(columns={'segment': 'urun_segment'})
                
                anlik_df = anlik_df.merge(
                    magaza_agg[['magaza_kod', 'segment']], 
                    on='magaza_kod', 
                    how='left'
                ).rename(columns={'segment': 'magaza_segment'})
                
                # Segment değerlerini string'e çevir
                anlik_df['urun_segment'] = anlik_df['urun_segment'].astype(str)
                anlik_df['magaza_segment'] = anlik_df['magaza_segment'].astype(str)
                
                # KPI'dan forward_cover ve min_deger al (mg bazında)
                # Basitleştirme: Ortalama forward_cover kullan
                default_fc = kpi_df['forward_cover'].mean()
                
                # Ürün master'dan mg bilgisi al ve KPI ile birleştir
                if st.session_state.urun_master is not None:
                    urun_master = st.session_state.urun_master[['urun_kod', 'mg']].copy()
                    
                    # Veri tiplerini uyumlu hale getir
                    urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    
                    # mg'yi int'e çevir (float'tan gelebilir: 110101.0 -> 110101)
                    urun_master['mg'] = urun_master['mg'].fillna(0).astype(float).astype(int).astype(str)
                    
                    st.write(f"🔍 Debug: Ürün master kayıt sayısı: {len(urun_master)}")
                    st.write(f"🔍 Debug: Ürün master örnek mg (düzeltilmiş): {urun_master['mg'].head(3).tolist()}")
                    
                    anlik_df = anlik_df.merge(urun_master, on='urun_kod', how='left')
                    
                    st.write(f"🔍 Debug: Merge sonrası mg null sayısı: {anlik_df['mg'].isna().sum()}")
                    
                    # KPI ile birleştir - min_deger için
                    kpi_data = kpi_df[['mg_id', 'min_deger', 'max_deger']].rename(columns={'mg_id': 'mg'})
                    
                    # KPI mg'yi de string'e çevir
                    kpi_data['mg'] = kpi_data['mg'].astype(str)
                    anlik_df['mg'] = anlik_df['mg'].astype(str)
                    
                    st.write(f"🔍 Debug: KPI kayıt sayısı: {len(kpi_data)}")
                    st.write(f"🔍 Debug: KPI örnek mg: {kpi_data['mg'].head(5).tolist()}")
                    st.write(f"🔍 Debug: Anlik örnek mg: {anlik_df['mg'].head(5).tolist()}")
                    
                    anlik_df = anlik_df.merge(kpi_data, on='mg', how='left')
                    
                    st.write(f"🔍 Debug: KPI merge sonrası min_deger null sayısı: {anlik_df['min_deger'].isna().sum()}")
                    st.write(f"🔍 Debug: KPI merge sonrası min_deger > 0 sayısı: {(anlik_df['min_deger'] > 0).sum()}")
                    
                    # min_deger yoksa default 0
                    anlik_df['min_deger'] = anlik_df['min_deger'].fillna(0)
                    anlik_df['max_deger'] = anlik_df['max_deger'].fillna(999999)
                else:
                    st.warning("⚠️ Ürün Master yüklenmediği için KPI min/max değerleri kullanılamadı")
                    anlik_df['min_deger'] = 0
                    anlik_df['max_deger'] = 999999
                
                st.write("⏳ Adım 3/6: Matris değerleri getiriliyor...")
                progress_bar.progress(45)
                
                # Matris değerlerini al
                def get_matrix_value(magaza_seg, urun_seg, matrix):
                    try:
                        return matrix.loc[urun_seg, magaza_seg]
                    except:
                        return 1.0  # Default
                
                anlik_df['genlestirme'] = anlik_df.apply(
                    lambda row: get_matrix_value(
                        row['magaza_segment'], 
                        row['urun_segment'], 
                        st.session_state.genlestirme_orani
                    ), axis=1
                )
                
                anlik_df['sisme'] = anlik_df.apply(
                    lambda row: get_matrix_value(
                        row['magaza_segment'], 
                        row['urun_segment'], 
                        st.session_state.sisme_orani
                    ), axis=1
                )
                
                anlik_df['min_oran'] = anlik_df.apply(
                    lambda row: get_matrix_value(
                        row['magaza_segment'], 
                        row['urun_segment'], 
                        st.session_state.min_oran
                    ), axis=1
                )
                
                st.write("⏳ Adım 4/6: İhtiyaç hesaplanıyor...")
                progress_bar.progress(60)
                
                # Debug: Veri kontrolü
                st.write(f"🔍 Debug: Toplam kayıt sayısı: {len(anlik_df)}")
                st.write(f"🔍 Debug: Benzersiz mağaza segment: {anlik_df['magaza_segment'].nunique()}")
                st.write(f"🔍 Debug: Benzersiz ürün segment: {anlik_df['urun_segment'].nunique()}")
                
                # RPT ve Min için ayrı satırlar oluştur
                # Her kayıt için hem RPT hem Min hesaplanacak
                anlik_rpt = anlik_df.copy()
                anlik_rpt['Durum'] = 'RPT'
                
                anlik_min = anlik_df.copy()
                anlik_min['Durum'] = 'Min'
                
                # Yeni ürün kontrolü - Initial olarak işaretle
                if st.session_state.yeni_urun_listesi is not None:
                    yeni_urun_kodlari = st.session_state.yeni_urun_listesi['urun_kod'].astype(str).tolist()
                    
                    # Initial satırları oluştur (sadece yeni ürünler için)
                    anlik_initial = anlik_df[anlik_df['urun_kod'].astype(str).isin(yeni_urun_kodlari)].copy()
                    anlik_initial['Durum'] = 'Initial'
                    
                    # Üç dataframe'i birleştir
                    anlik_df = pd.concat([anlik_rpt, anlik_min, anlik_initial], ignore_index=True)
                    
                    st.write(f"🔍 Debug: Yeni ürün sayısı: {len(yeni_urun_kodlari)}")
                    st.write(f"🔍 Debug: Initial satır sayısı: {len(anlik_initial)}")
                else:
                    # Sadece RPT ve Min
                    anlik_df = pd.concat([anlik_rpt, anlik_min], ignore_index=True)
                
                st.write(f"🔍 Debug: RPT+Min birleştirme sonrası kayıt: {len(anlik_df)}")
                
                # Öncelik sıralaması ekle
                st.write(f"🔍 Debug: Sıralama tablosu satır sayısı: {len(siralama_df)}")
                
                anlik_df = anlik_df.merge(
                    siralama_df,
                    left_on=['magaza_segment', 'urun_segment', 'Durum'],
                    right_on=['Magaza_Cluster', 'Urun_Cluster', 'Durum'],
                    how='left'
                )
                
                st.write(f"🔍 Debug: Merge sonrası kayıt sayısı: {len(anlik_df)}")
                st.write(f"🔍 Debug: Merge sonrası öncelik olan kayıt: {anlik_df['Oncelik'].notna().sum()}")
                
                # İhtiyaç hesapla
                anlik_df['ihtiyac_rpt'] = (
                    default_fc * anlik_df['satis'] * anlik_df['genlestirme']
                ) - (anlik_df['stok'] + anlik_df['yol'])
                
                # Min için: (min_oran * min_deger) - stok - yol
                anlik_df['ihtiyac_min'] = (
                    anlik_df['min_oran'] * anlik_df['min_deger']
                ) - (anlik_df['stok'] + anlik_df['yol'])
                
                # Initial için: min_deger × genlestirme_orani - stok - yol
                anlik_df['ihtiyac_initial'] = (
                    anlik_df['min_deger'] * anlik_df['genlestirme']
                ) - (anlik_df['stok'] + anlik_df['yol'])
                
                st.write(f"🔍 Debug: RPT ihtiyaç > 0: {(anlik_df['ihtiyac_rpt'] > 0).sum()}")
                st.write(f"🔍 Debug: Min ihtiyaç > 0: {(anlik_df['ihtiyac_min'] > 0).sum()}")
                st.write(f"🔍 Debug: Initial ihtiyaç > 0: {(anlik_df['ihtiyac_initial'] > 0).sum()}")
                
                # Min hesaplama örnek kontrol
                min_rows = anlik_df[anlik_df['Durum'] == 'Min'].head(3)
                st.write("🔍 Debug: Min örnek hesaplama:")
                for idx, row in min_rows.iterrows():
                    st.write(f"  min_oran={row['min_oran']}, min_deger={row['min_deger']}, stok={row['stok']}, yol={row['yol']}, ihtiyac_min={row['ihtiyac_min']}")
                
                # Initial hesaplama örnek kontrol
                initial_rows = anlik_df[anlik_df['Durum'] == 'Initial'].head(3)
                if len(initial_rows) > 0:
                    st.write("🔍 Debug: Initial örnek hesaplama:")
                    for idx, row in initial_rows.iterrows():
                        st.write(f"  min_deger={row['min_deger']}, genlestirme={row['genlestirme']}, stok={row['stok']}, yol={row['yol']}, ihtiyac_initial={row['ihtiyac_initial']}")
                
                # Durum'a göre final ihtiyacı belirle
                anlik_df['ihtiyac'] = anlik_df.apply(
                    lambda row: (row['ihtiyac_rpt'] if row['Durum'] == 'RPT' 
                                else row['ihtiyac_min'] if row['Durum'] == 'Min'
                                else row['ihtiyac_initial']),
                    axis=1
                )
                
                # Negatif ihtiyaçları 0 yap (min için: <=0 ise 0)
                anlik_df['ihtiyac'] = anlik_df['ihtiyac'].clip(lower=0)
                
                st.write(f"🔍 Debug: İhtiyaç > 0 olan kayıt (tüm): {(anlik_df['ihtiyac'] > 0).sum()}")
                st.write(f"🔍 Debug: İhtiyaç > 0 olan RPT: {((anlik_df['ihtiyac'] > 0) & (anlik_df['Durum'] == 'RPT')).sum()}")
                st.write(f"🔍 Debug: İhtiyaç > 0 olan Min: {((anlik_df['ihtiyac'] > 0) & (anlik_df['Durum'] == 'Min')).sum()}")
                st.write(f"🔍 Debug: İhtiyaç > 0 olan Initial: {((anlik_df['ihtiyac'] > 0) & (anlik_df['Durum'] == 'Initial')).sum()}")
                
                # max_deger kontrolü - sevkiyat + stok + yol toplamı max_deger'i geçemesin
                anlik_df['max_sevkiyat'] = anlik_df['max_deger'] - (anlik_df['stok'] + anlik_df['yol'])
                anlik_df['max_sevkiyat'] = anlik_df['max_sevkiyat'].clip(lower=0)
                
                # İhtiyacı max_sevkiyat ile sınırla
                anlik_df['ihtiyac'] = anlik_df.apply(
                    lambda row: min(row['ihtiyac'], row['max_sevkiyat']) if pd.notna(row['max_sevkiyat']) else row['ihtiyac'],
                    axis=1
                )
                
                st.write(f"🔍 Debug: Max kontrol sonrası ihtiyaç > 0: {(anlik_df['ihtiyac'] > 0).sum()}")
                
                st.write("⏳ Adım 5/6: Yasak kontrolleri yapılıyor...")
                progress_bar.progress(75)
                
                # Yasak kontrolü
                if st.session_state.yasak_master is not None:
                    yasak_df = st.session_state.yasak_master.copy()
                    
                    # Veri tiplerini uyumlu hale getir
                    yasak_df['urun_kod'] = yasak_df['urun_kod'].astype(str)
                    yasak_df['magaza_kod'] = yasak_df['magaza_kod'].astype(str)
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                    
                    anlik_df = anlik_df.merge(
                        yasak_df[['urun_kod', 'magaza_kod', 'yasak_durum']],
                        on=['urun_kod', 'magaza_kod'],
                        how='left'
                    )
                    # Yasak olanların ihtiyacını 0 yap
                    anlik_df.loc[anlik_df['yasak_durum'] == 'Yasak', 'ihtiyac'] = 0
                
                # Depo eşleşmesi
                magaza_df['magaza_kod'] = magaza_df['magaza_kod'].astype(str)
                anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                
                anlik_df = anlik_df.merge(
                    magaza_df[['magaza_kod', 'depo_kod']],
                    on='magaza_kod',
                    how='left'
                )
                
                st.write("⏳ Adım 6/6: Öncelik sıralaması uygulanıyor ve depo stok kontrolü yapılıyor...")
                progress_bar.progress(90)
                
                # Önceliğe göre sırala ve sadece ihtiyacı olanları al
                result_df = anlik_df[anlik_df['ihtiyac'] > 0].copy()
                
                # ÖNEMLI: Aynı mağaza-ürün için birden fazla durum varsa (RPT, Min, Initial)
                # Maksimum ihtiyacı olanı al
                result_df_max = result_df.loc[
                    result_df.groupby(['magaza_kod', 'urun_kod'])['ihtiyac'].idxmax()
                ].copy()
                
                st.write(f"🔍 Debug: Tüm ihtiyaç kayıtları: {len(result_df)}")
                st.write(f"🔍 Debug: Maksimum alındıktan sonra: {len(result_df_max)}")
                st.write(f"🔍 Debug: RPT sayısı: {(result_df_max['Durum'] == 'RPT').sum()}")
                st.write(f"🔍 Debug: Min sayısı: {(result_df_max['Durum'] == 'Min').sum()}")
                st.write(f"🔍 Debug: Initial sayısı: {(result_df_max['Durum'] == 'Initial').sum()}")
                
                # Önceliğe göre sırala
                result_df_max = result_df_max.sort_values('Oncelik').reset_index(drop=True)
                
                st.write(f"🔍 Debug: Öncelik sıralaması sonrası kayıt: {len(result_df)}")
                
                # Depo stok kontrolü - öncelik sırasına göre
                # Her ürün-depo kombinasyonu için kalan stok takibi
                depo_stok_dict = {}
                
                # Depo stok bilgisini dictionary'e al - veri tiplerini string'e çevir
                # ÖNEMLİ: Ürün kodlarındaki .0 sorununu çöz
                for _, row in depo_df.iterrows():
                    depo_kod_str = str(row['depo_kod'])
                    urun_kod_raw = str(row['urun_kod'])
                    
                    # Float string ise düzelt: '1000036.0' -> '1000036'
                    try:
                        if '.' in urun_kod_raw:
                            urun_kod_str = str(int(float(urun_kod_raw)))
                        else:
                            urun_kod_str = urun_kod_raw
                    except:
                        urun_kod_str = urun_kod_raw
                    
                    key = (depo_kod_str, urun_kod_str)
                    if key not in depo_stok_dict:
                        depo_stok_dict[key] = float(row['stok'])
                
                st.write(f"🔍 Debug: Depo stok dictionary boyutu: {len(depo_stok_dict)}")
                
                # İlk birkaç depo stok key'ini göster
                if len(depo_stok_dict) > 0:
                    sample_keys = list(depo_stok_dict.keys())[:5]
                    st.write(f"🔍 Debug: Örnek depo key'leri (düzeltilmiş): {sample_keys}")
                
                # İlk birkaç result_df satırının depo_kod ve urun_kod'unu göster
                if len(result_df_max) > 0:
                    # Result_df'deki ürün kodlarını da düzelt
                    result_df_max['urun_kod_clean'] = result_df_max['urun_kod'].astype(str).apply(
                        lambda x: str(int(float(x))) if ('.' in str(x)) else str(x)
                    )
                    result_df_max['depo_kod_clean'] = result_df_max['depo_kod'].astype(str)
                    
                    sample_result = result_df_max[['depo_kod_clean', 'urun_kod', 'urun_kod_clean', 'Durum', 'ihtiyac']].head(5)
                    st.write("🔍 Debug: Örnek result_df depo-ürün (düzeltilmiş):")
                    st.write(sample_result)
                
                # Her satır için depo stoğuna göre sevkiyat miktarını ayarla
                sevkiyat_gercek = []
                eslesme_sayisi = 0
                
                for idx, row in result_df_max.iterrows():
                    depo_kod = str(row['depo_kod'])
                    urun_kod_raw = str(row['urun_kod'])
                    
                    # Float string ise düzelt
                    try:
                        if '.' in urun_kod_raw:
                            urun_kod = str(int(float(urun_kod_raw)))
                        else:
                            urun_kod = urun_kod_raw
                    except:
                        urun_kod = urun_kod_raw
                    
                    ihtiyac = float(row['ihtiyac'])
                    
                    key = (depo_kod, urun_kod)
                    
                    # Depo stoğu var mı kontrol et
                    if key in depo_stok_dict:
                        eslesme_sayisi += 1
                        kalan_stok = depo_stok_dict[key]
                        
                        # İhtiyaç kadar verilebilirse ver, yoksa kalanı ver
                        if kalan_stok >= ihtiyac:
                            sevkiyat = ihtiyac
                            depo_stok_dict[key] -= ihtiyac
                        else:
                            sevkiyat = kalan_stok
                            depo_stok_dict[key] = 0
                    else:
                        # Depoda bu ürün yok
                        sevkiyat = 0
                    
                    sevkiyat_gercek.append(sevkiyat)
                
                st.write(f"🔍 Debug: Depo-ürün eşleşme sayısı: {eslesme_sayisi} / {len(result_df_max)}")
                
                result_df_max['sevkiyat_gercek'] = sevkiyat_gercek
                
                # Stok yokluğu kaybını hesapla
                result_df_max['stok_yoklugu_kaybi'] = result_df_max['ihtiyac'] - result_df_max['sevkiyat_gercek']
                
                # ÖNEMLİ: Sadece sevkiyat > 0 olanları DEĞİL, ihtiyaç > 0 olanların HEPSİNİ al
                # Böylece stok olmayan ama ihtiyaç olan kayıtlar da rapora girer
                result_df_max = result_df_max[result_df_max['ihtiyac'] > 0].copy()
                
                st.write(f"🔍 Debug: İhtiyaç > 0 olan tüm kayıtlar (sevkiyat=0 dahil): {len(result_df_max)}")
                st.write(f"🔍 Debug: Sevkiyat > 0 olan kayıt: {(result_df_max['sevkiyat_gercek'] > 0).sum()}")
                st.write(f"🔍 Debug: Sevkiyat = 0 olan kayıt: {(result_df_max['sevkiyat_gercek'] == 0).sum()}")
                
                # Sonuç tablosunu oluştur
                result_final = result_df_max[[
                    'Oncelik', 'magaza_kod', 'magaza_ad', 'urun_kod', 'urun_ad',
                    'magaza_segment', 'urun_segment', 'Durum',
                    'stok', 'yol', 'satis', 'ihtiyac', 'sevkiyat_gercek', 'depo_kod'
                ]].rename(columns={
                    'Oncelik': 'oncelik',
                    'Durum': 'durum',
                    'ihtiyac': 'ihtiyac_miktari',
                    'sevkiyat_gercek': 'sevkiyat_miktari'
                })
                
                # Stok yokluğu kaynaklı satış kaybını hesapla
                result_final['stok_yoklugu_satis_kaybi'] = result_final['ihtiyac_miktari'] - result_final['sevkiyat_miktari']
                
                # Sıra numarası ekle
                result_final.insert(0, 'sira_no', range(1, len(result_final) + 1))
                
                # Sonucu session state'e kaydet (raporlar için)
                st.session_state.sevkiyat_sonuc = result_final
                
                progress_bar.progress(100)
                
                st.success("✅ Hesaplama tamamlandı!")
                st.balloons()
                
                # Sonuç tablosu
                st.markdown("---")
                st.subheader("📊 Sevkiyat Sonuçları")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Toplam Sevkiyat Satırı", len(result_final))
                with col2:
                    st.metric("Toplam İhtiyaç", f"{result_final['ihtiyac_miktari'].sum():,.0f}")
                with col3:
                    st.metric("Gerçekleşen Sevkiyat", f"{result_final['sevkiyat_miktari'].sum():,.0f}")
                with col4:
                    st.metric("Stok Yokluğu Satış Kaybı", f"{result_final['stok_yoklugu_satis_kaybi'].sum():,.0f}")
                
                st.dataframe(result_final, use_container_width=True, height=400)
                
                # Stok yokluğu özet raporu
                st.markdown("---")
                st.subheader("⚠️ Stok Yokluğu Kaynaklı Satış Kaybı Raporu")
                
                # Sadece stok yokluğu olanları göster
                stok_yoklugu_df = result_final[result_final['stok_yoklugu_satis_kaybi'] > 0].copy()
                
                if len(stok_yoklugu_df) > 0:
                    st.warning(f"⚠️ {len(stok_yoklugu_df)} satırda stok yokluğu nedeniyle satış kaybı var!")
                    
                    # Özet tablo
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**En Fazla Kayıp Olan 10 Satır:**")
                        top_kayip = stok_yoklugu_df.nlargest(10, 'stok_yoklugu_satis_kaybi')[[
                            'magaza_ad', 'urun_ad', 'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi'
                        ]]
                        st.dataframe(top_kayip, use_container_width=True)
                    
                    with col2:
                        st.write("**Ürün Bazında Toplam Kayıp:**")
                        urun_kayip = stok_yoklugu_df.groupby('urun_ad')['stok_yoklugu_satis_kaybi'].sum().sort_values(ascending=False).head(10)
                        st.dataframe(urun_kayip, use_container_width=True)
                    
                    # Detaylı raporu indir
                    st.download_button(
                        label="📥 Stok Yokluğu Raporu İndir (CSV)",
                        data=stok_yoklugu_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="stok_yoklugu_satis_kaybi.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("✅ Tüm ihtiyaçlar depo stoğundan karşılanabildi!")
                
                # Export butonları
                st.markdown("---")
                st.subheader("📥 Sonuçları Dışa Aktar")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        label="📥 CSV İndir",
                        data=result_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sevkiyat_sonuclari.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Excel İndir",
                        data=result_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sevkiyat_sonuclari.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col3:
                    st.download_button(
                        label="📥 JSON İndir",
                        data=result_df.to_json(orient='records', force_ascii=False),
                        file_name="sevkiyat_sonuclari.json",
                        mime="application/json"
                    )

# ============================================
# 🆕 YENİ ÜRÜN SEVKİYATI
# ============================================
elif menu == "🆕 Yeni Ürün Sevkiyatı":
    st.title("🆕 Yeni Ürün Sevkiyatı (Initial Distribution)")
    st.markdown("---")
    
    # Veri kontrolü
    if (st.session_state.anlik_stok_satis is None or 
        st.session_state.magaza_master is None or 
        st.session_state.depo_stok is None):
        st.warning("⚠️ Gerekli veriler yüklenmemiş!")
        st.info("Lütfen önce: Anlık Stok/Satış, Mağaza Master ve Depo Stok verilerini yükleyin.")
    else:
        st.info("""
        **Yeni Ürün Kriterleri:**
        1. **Depo stoğu > 500** (Depoya yeni gelmiş, henüz dağıtılmamış)
        2. **Stok + yol > 1 olan mağaza sayısı < %30** (Az sayıda mağazaya dağıtılmış)
        3. **Yasak olmayan mağazalar** (Yasak mağazalar hesaba katılmaz)
        
        Bu kriterleri sağlayan ürünler "Initial" olarak işaretlenir ve öncelikli dağıtılır.
        """)
        
        if st.button("🔍 Yeni Ürünleri Tespit Et", type="primary"):
            with st.spinner("🔍 Yeni ürünler tespit ediliyor..."):
                
                anlik_df = st.session_state.anlik_stok_satis.copy()
                magaza_df = st.session_state.magaza_master.copy()
                depo_df = st.session_state.depo_stok.copy()
                
                # Yasak kontrolü
                if st.session_state.yasak_master is not None:
                    yasak_df = st.session_state.yasak_master.copy()
                    yasak_df['urun_kod'] = yasak_df['urun_kod'].astype(str)
                    yasak_df['magaza_kod'] = yasak_df['magaza_kod'].astype(str)
                    
                    # Yasak kombinasyonları işaretle
                    anlik_df['urun_kod_str'] = anlik_df['urun_kod'].astype(str)
                    anlik_df['magaza_kod_str'] = anlik_df['magaza_kod'].astype(str)
                    
                    anlik_df = anlik_df.merge(
                        yasak_df[['urun_kod', 'magaza_kod', 'yasak_durum']],
                        left_on=['urun_kod_str', 'magaza_kod_str'],
                        right_on=['urun_kod', 'magaza_kod'],
                        how='left',
                        suffixes=('', '_yasak')
                    )
                    
                    # Yasak olanları filtrele
                    anlik_df_temiz = anlik_df[anlik_df['yasak_durum'] != 'Yasak'].copy()
                    
                    st.write(f"📊 Yasak filtresi: {len(anlik_df)} → {len(anlik_df_temiz)} kayıt")
                else:
                    anlik_df_temiz = anlik_df.copy()
                
                # Yasak olmayan toplam benzersiz mağaza sayısı
                toplam_magaza = anlik_df_temiz['magaza_kod'].nunique()
                esik_magaza = int(toplam_magaza * 0.30)
                
                st.write(f"📊 Yasak olmayan toplam mağaza: {toplam_magaza}")
                st.write(f"📊 %30 eşik değeri: {esik_magaza} mağaza")
                
                # Önce depo stoğu > 500 olan ürünleri filtrele
                # Veri tipi düzeltme
                depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                depo_df['urun_kod'] = depo_df['urun_kod'].apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                
                # Depo stok toplamı
                depo_toplam = depo_df.groupby('urun_kod')['stok'].sum().reset_index()
                depo_toplam.columns = ['urun_kod', 'depo_stok_toplam']
                
                # Kriter 1: Depo stoğu > 500 (yeni gelmiş ürünler)
                yeni_urun_adaylari = depo_toplam[depo_toplam['depo_stok_toplam'] > 500]['urun_kod'].tolist()
                
                st.write(f"🔍 Depo stok > 500 olan ürün: {len(yeni_urun_adaylari)}")
                
                # Bu ürünler için mağaza dağılımına bak
                anlik_df_temiz['urun_kod'] = anlik_df_temiz['urun_kod'].astype(str)
                yeni_urun_df = anlik_df_temiz[anlik_df_temiz['urun_kod'].isin(yeni_urun_adaylari)].copy()
                
                # Stok + yol > 1 olanlar (girmiş sayılır)
                yeni_urun_df['toplam_eldeki'] = yeni_urun_df['stok'] + yeni_urun_df['yol']
                urun_stoklu = yeni_urun_df[yeni_urun_df['toplam_eldeki'] > 1].groupby('urun_kod')['magaza_kod'].nunique().reset_index()
                urun_stoklu.columns = ['urun_kod', 'stoklu_magaza_sayisi']
                
                # Depo stok bilgisi ile birleştir
                urun_analiz = urun_stoklu.merge(depo_toplam, on='urun_kod', how='left')
                
                # Kriter 2: %30'dan az mağazaya dağıtılmış (veya hiç dağıtılmamış)
                yeni_urunler = urun_analiz[
                    (urun_analiz['stoklu_magaza_sayisi'] < esik_magaza) &
                    (urun_analiz['depo_stok_toplam'] > 500)
                ].copy()
                
                st.write(f"✅ Her iki kriteri sağlayan ürün: {len(yeni_urunler)}")
                
                if len(yeni_urunler) > 0:
                    # Ürün bilgilerini ekle
                    if st.session_state.urun_master is not None:
                        urun_master = st.session_state.urun_master[['urun_kod', 'urun_ad', 'marka_ad']].copy()
                        urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                        urun_master['urun_kod'] = urun_master['urun_kod'].apply(
                            lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                        )
                        yeni_urunler = yeni_urunler.merge(urun_master, on='urun_kod', how='left')
                    
                    # Yüzde hesapla
                    yeni_urunler['dagilim_orani'] = (yeni_urunler['stoklu_magaza_sayisi'] / toplam_magaza * 100).round(2)
                    
                    # Sırala
                    yeni_urunler = yeni_urunler.sort_values('depo_stok_toplam', ascending=False)
                    
                    # Session state'e kaydet
                    st.session_state.yeni_urun_listesi = yeni_urunler
                    
                    st.success(f"✅ {len(yeni_urunler)} yeni ürün tespit edildi!")
                    
                    # Özet metrikler
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Yeni Ürün Sayısı", len(yeni_urunler))
                    with col2:
                        st.metric("Toplam Depo Stok", f"{yeni_urunler['depo_stok_toplam'].sum():,.0f}")
                    with col3:
                        ortalama_dagilim = yeni_urunler['dagilim_orani'].mean()
                        st.metric("Ortalama Dağılım", f"{ortalama_dagilim:.1f}%")
                    
                    st.markdown("---")
                    
                    # Tablo göster
                    st.subheader("📋 Tespit Edilen Yeni Ürünler")
                    
                    display_cols = ['urun_kod', 'urun_ad', 'marka_ad', 'stoklu_magaza_sayisi', 
                                   'dagilim_orani', 'depo_stok_toplam']
                    
                    if 'urun_ad' not in yeni_urunler.columns:
                        display_cols = [c for c in display_cols if c in yeni_urunler.columns]
                    
                    st.dataframe(yeni_urunler[display_cols], use_container_width=True, height=400)
                    
                    # İndir
                    st.download_button(
                        label="📥 Yeni Ürün Listesi İndir (CSV)",
                        data=yeni_urunler.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="yeni_urun_listesi.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("ℹ️ Kriterleri sağlayan yeni ürün bulunamadı.")
        
        # Eğer liste varsa göster
        if st.session_state.yeni_urun_listesi is not None:
            st.markdown("---")
            st.subheader("💾 Kayıtlı Yeni Ürün Listesi")
            st.info(f"Son tespit: {len(st.session_state.yeni_urun_listesi)} ürün")
            
            if st.button("🗑️ Listeyi Temizle"):
                st.session_state.yeni_urun_listesi = None
                st.rerun()

# ============================================
# 📈 RAPORLAR
# ============================================
elif menu == "📈 Raporlar":
    st.title("📈 Raporlar ve Analizler")
    st.markdown("---")
    
    # Sevkiyat sonucu var mı kontrol et
    if st.session_state.sevkiyat_sonuc is None:
        st.warning("⚠️ Henüz sevkiyat hesaplaması yapılmadı!")
        st.info("Lütfen önce 'Sevkiyat Hesaplama' menüsünden hesaplama yapın.")
    else:
        result_df = st.session_state.sevkiyat_sonuc.copy()
        
        # Tab'lar oluştur
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏷️ Marka Analizi",
            "📦 Mal Grubu Analizi", 
            "🏪 Mağaza Analizi",
            "⚠️ Satış Kaybı Analizi",
            "🆕 Yeni Ürün Dağılım Raporu"
        ])
        
        # ============================================
        # MARKA ANALİZİ
        # ============================================
        with tab1:
            st.subheader("🏷️ Marka Bazında Analiz")
            
            # Ürün master ile birleştir (marka bilgisi için)
            if st.session_state.urun_master is not None:
                urun_marka = st.session_state.urun_master[['urun_kod', 'marka_ad']].copy()
                urun_marka['urun_kod'] = urun_marka['urun_kod'].astype(str)
                
                # Float string düzelt
                urun_marka['urun_kod'] = urun_marka['urun_kod'].apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                
                result_marka = result_df.merge(urun_marka, on='urun_kod', how='left')
                
                # Marka bazında özet
                marka_ozet = result_marka.groupby('marka_ad').agg({
                    'ihtiyac_miktari': 'sum',
                    'sevkiyat_miktari': 'sum',
                    'stok_yoklugu_satis_kaybi': 'sum',
                    'magaza_kod': 'nunique',
                    'urun_kod': 'nunique'
                }).reset_index()
                
                marka_ozet.columns = ['Marka', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 
                                      'Satış Kaybı', 'Mağaza Sayısı', 'Ürün Sayısı']
                
                # Gerçekleşme oranı hesapla
                marka_ozet['Gerçekleşme %'] = (
                    marka_ozet['Toplam Sevkiyat'] / marka_ozet['Toplam İhtiyaç'] * 100
                ).round(2)
                
                # Sırala
                marka_ozet = marka_ozet.sort_values('Toplam İhtiyaç', ascending=False)
                
                # Özet metrikler
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Toplam Marka", len(marka_ozet))
                with col2:
                    st.metric("Toplam İhtiyaç", f"{marka_ozet['Toplam İhtiyaç'].sum():,.0f}")
                with col3:
                    st.metric("Toplam Sevkiyat", f"{marka_ozet['Toplam Sevkiyat'].sum():,.0f}")
                with col4:
                    st.metric("Toplam Kayıp", f"{marka_ozet['Satış Kaybı'].sum():,.0f}")
                
                st.markdown("---")
                
                # Tablo
                st.dataframe(marka_ozet, use_container_width=True, height=400)
                
                # İndir
                st.download_button(
                    label="📥 Marka Analizi İndir (CSV)",
                    data=marka_ozet.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="marka_analizi.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Ürün Master yüklenmediği için marka analizi yapılamıyor.")
        
        # ============================================
        # MAL GRUBU ANALİZİ
        # ============================================
        with tab2:
            st.subheader("📦 Mal Grubu (MG) Bazında Analiz")
            
            # Ürün master ile birleştir (mg bilgisi için)
            if st.session_state.urun_master is not None:
                urun_mg = st.session_state.urun_master[['urun_kod', 'mg', 'mg_ad']].copy()
                urun_mg['urun_kod'] = urun_mg['urun_kod'].astype(str)
                
                # Float string düzelt
                urun_mg['urun_kod'] = urun_mg['urun_kod'].apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                
                result_mg = result_df.merge(urun_mg, on='urun_kod', how='left')
                
                # MG bazında özet
                mg_ozet = result_mg.groupby(['mg', 'mg_ad']).agg({
                    'ihtiyac_miktari': 'sum',
                    'sevkiyat_miktari': 'sum',
                    'stok_yoklugu_satis_kaybi': 'sum',
                    'magaza_kod': 'nunique',
                    'urun_kod': 'nunique'
                }).reset_index()
                
                mg_ozet.columns = ['MG Kod', 'MG Adı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 
                                   'Satış Kaybı', 'Mağaza Sayısı', 'Ürün Sayısı']
                
                # Gerçekleşme oranı hesapla
                mg_ozet['Gerçekleşme %'] = (
                    mg_ozet['Toplam Sevkiyat'] / mg_ozet['Toplam İhtiyaç'] * 100
                ).round(2)
                
                # Sırala
                mg_ozet = mg_ozet.sort_values('Toplam İhtiyaç', ascending=False)
                
                # Özet metrikler
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Toplam MG", len(mg_ozet))
                with col2:
                    st.metric("Toplam İhtiyaç", f"{mg_ozet['Toplam İhtiyaç'].sum():,.0f}")
                with col3:
                    st.metric("Toplam Sevkiyat", f"{mg_ozet['Toplam Sevkiyat'].sum():,.0f}")
                with col4:
                    st.metric("Toplam Kayıp", f"{mg_ozet['Satış Kaybı'].sum():,.0f}")
                
                st.markdown("---")
                
                # Tablo
                st.dataframe(mg_ozet, use_container_width=True, height=400)
                
                # İndir
                st.download_button(
                    label="📥 MG Analizi İndir (CSV)",
                    data=mg_ozet.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="mg_analizi.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Ürün Master yüklenmediği için MG analizi yapılamıyor.")
        
        # ============================================
        # MAĞAZA ANALİZİ
        # ============================================
        with tab3:
            st.subheader("🏪 Mağaza Bazında Analiz")
            
            # Mağaza bazında özet
            magaza_ozet = result_df.groupby(['magaza_kod', 'magaza_ad']).agg({
                'ihtiyac_miktari': 'sum',
                'sevkiyat_miktari': 'sum',
                'stok_yoklugu_satis_kaybi': 'sum',
                'urun_kod': 'nunique'
            }).reset_index()
            
            magaza_ozet.columns = ['Mağaza Kod', 'Mağaza Adı', 'Toplam İhtiyaç', 
                                   'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']
            
            # Gerçekleşme oranı hesapla
            magaza_ozet['Gerçekleşme %'] = (
                magaza_ozet['Toplam Sevkiyat'] / magaza_ozet['Toplam İhtiyaç'] * 100
            ).round(2)
            
            # Sırala
            magaza_ozet = magaza_ozet.sort_values('Toplam İhtiyaç', ascending=False)
            
            # Özet metrikler
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Toplam Mağaza", len(magaza_ozet))
            with col2:
                st.metric("Toplam İhtiyaç", f"{magaza_ozet['Toplam İhtiyaç'].sum():,.0f}")
            with col3:
                st.metric("Toplam Sevkiyat", f"{magaza_ozet['Toplam Sevkiyat'].sum():,.0f}")
            with col4:
                st.metric("Toplam Kayıp", f"{magaza_ozet['Satış Kaybı'].sum():,.0f}")
            
            st.markdown("---")
            
            # Tablo
            st.dataframe(magaza_ozet, use_container_width=True, height=400)
            
            # İndir
            st.download_button(
                label="📥 Mağaza Analizi İndir (CSV)",
                data=magaza_ozet.to_csv(index=False, encoding='utf-8-sig'),
                file_name="magaza_analizi.csv",
                mime="text/csv"
            )
        
        # ============================================
        # SATIŞ KAYBI ANALİZİ
        # ============================================
        with tab4:
            st.subheader("⚠️ Stok Yokluğu Kaynaklı Satış Kaybı Analizi")
            
            # Sadece kayıp olanları al
            kayip_df = result_df[result_df['stok_yoklugu_satis_kaybi'] > 0].copy()
            
            if len(kayip_df) > 0:
                # Özet metrikler
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Kayıp Olan Satır", len(kayip_df))
                with col2:
                    st.metric("Toplam Satış Kaybı", f"{kayip_df['stok_yoklugu_satis_kaybi'].sum():,.0f}")
                with col3:
                    kayip_oran = (kayip_df['stok_yoklugu_satis_kaybi'].sum() / 
                                 result_df['ihtiyac_miktari'].sum() * 100)
                    st.metric("Kayıp Oranı", f"{kayip_oran:.2f}%")
                
                st.markdown("---")
                
                # En fazla kayıp olan 20 satır
                st.write("**En Fazla Kayıp Olan 20 Satır:**")
                top_kayip = kayip_df.nlargest(20, 'stok_yoklugu_satis_kaybi')[[
                    'magaza_ad', 'urun_ad', 'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi'
                ]]
                st.dataframe(top_kayip, use_container_width=True)
                
                st.markdown("---")
                
                # Ürün bazında kayıp
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Ürün Bazında Toplam Kayıp (Top 10):**")
                    urun_kayip = kayip_df.groupby('urun_ad')['stok_yoklugu_satis_kaybi'].sum().sort_values(ascending=False).head(10)
                    st.dataframe(urun_kayip, use_container_width=True)
                
                with col2:
                    st.write("**Mağaza Bazında Toplam Kayıp (Top 10):**")
                    magaza_kayip = kayip_df.groupby('magaza_ad')['stok_yoklugu_satis_kaybi'].sum().sort_values(ascending=False).head(10)
                    st.dataframe(magaza_kayip, use_container_width=True)
                
                st.markdown("---")
                
                # Detaylı rapor indir
                st.download_button(
                    label="📥 Detaylı Satış Kaybı Raporu İndir (CSV)",
                    data=kayip_df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="satis_kaybi_detay.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ Hiç stok yokluğu kaynaklı satış kaybı yok!")
        
        # ============================================
        # YENİ ÜRÜN DAĞILIM RAPORU
        # ============================================
        with tab5:
            st.subheader("🆕 Yeni Ürün Dağılım Raporu")
            
            # Yeni ürün listesi var mı kontrol et
            if st.session_state.yeni_urun_listesi is None:
                st.warning("⚠️ Henüz yeni ürün tespiti yapılmadı!")
                st.info("Lütfen önce 'Yeni Ürün Sevkiyatı' menüsünden yeni ürünleri tespit edin.")
            else:
                yeni_urun_kodlari = st.session_state.yeni_urun_listesi['urun_kod'].astype(str).tolist()
                
                # Sadece Initial (yeni ürün) sevkiyatlarını filtrele
                initial_df = result_df[result_df['durum'] == 'Initial'].copy()
                
                if len(initial_df) > 0:
                    st.success(f"✅ {len(yeni_urun_kodlari)} yeni ürün için sevkiyat yapıldı!")
                    
                    # Ürün bazında analiz
                    yeni_urun_analiz = []
                    
                    for urun_kod in yeni_urun_kodlari:
                        # Bu ürünün Initial sevkiyatları
                        urun_sevk = initial_df[initial_df['urun_kod'].astype(str) == str(urun_kod)]
                        
                        if len(urun_sevk) > 0:
                            # Başlangıç durumu (yeni ürün listesinden)
                            baslangic = st.session_state.yeni_urun_listesi[
                                st.session_state.yeni_urun_listesi['urun_kod'].astype(str) == str(urun_kod)
                            ]
                            
                            onceki_magaza = baslangic['stoklu_magaza_sayisi'].values[0] if len(baslangic) > 0 else 0
                            depo_stok = baslangic['depo_stok_toplam'].values[0] if len(baslangic) > 0 else 0
                            
                            # Sevkiyat sonrası
                            sonraki_magaza = urun_sevk['magaza_kod'].nunique()
                            toplam_sevkiyat = urun_sevk['sevkiyat_miktari'].sum()
                            
                            # Ürün bilgisi
                            urun_ad = urun_sevk['urun_ad'].iloc[0] if 'urun_ad' in urun_sevk.columns else urun_kod
                            
                            yeni_urun_analiz.append({
                                'Ürün Kodu': urun_kod,
                                'Ürün Adı': urun_ad,
                                'Önceki Mağaza': int(onceki_magaza),
                                'Sevkiyat Yapılan Mağaza': sonraki_magaza,
                                'Artış': sonraki_magaza - int(onceki_magaza),
                                'Toplam Sevkiyat': int(toplam_sevkiyat),
                                'Depo Stok': int(depo_stok),
                                'Kalan Depo': int(depo_stok - toplam_sevkiyat)
                            })
                    
                    if len(yeni_urun_analiz) > 0:
                        analiz_df = pd.DataFrame(yeni_urun_analiz)
                        analiz_df = analiz_df.sort_values('Artış', ascending=False)
                        
                        # Özet metrikler
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Yeni Ürün Sayısı", len(analiz_df))
                        with col2:
                            st.metric("Toplam Sevkiyat", f"{analiz_df['Toplam Sevkiyat'].sum():,.0f}")
                        with col3:
                            ortalama_artis = analiz_df['Artış'].mean()
                            st.metric("Ortalama Mağaza Artışı", f"{ortalama_artis:.0f}")
                        with col4:
                            toplam_magaza = analiz_df['Sevkiyat Yapılan Mağaza'].sum()
                            st.metric("Toplam Dağıtım Noktası", toplam_magaza)
                        
                        st.markdown("---")
                        
                        # Detaylı tablo
                        st.write("**Ürün Bazında Dağılım Detayı:**")
                        st.dataframe(analiz_df, use_container_width=True, height=400)
                        
                        st.markdown("---")
                        
                        # Örnekler
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**En Çok Dağıtılan 5 Ürün:**")
                            top_dagilim = analiz_df.nlargest(5, 'Artış')[['Ürün Adı', 'Önceki Mağaza', 'Sevkiyat Yapılan Mağaza', 'Artış']]
                            st.dataframe(top_dagilim, use_container_width=True)
                        
                        with col2:
                            st.write("**En Fazla Sevkiyat Yapılan 5 Ürün:**")
                            top_sevkiyat = analiz_df.nlargest(5, 'Toplam Sevkiyat')[['Ürün Adı', 'Toplam Sevkiyat', 'Kalan Depo']]
                            st.dataframe(top_sevkiyat, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # İndir
                        st.download_button(
                            label="📥 Yeni Ürün Dağılım Raporu İndir (CSV)",
                            data=analiz_df.to_csv(index=False, encoding='utf-8-sig'),
                            file_name="yeni_urun_dagilim_raporu.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("ℹ️ Initial sevkiyatı yapılan ürün bulunamadı.")
                else:
                    st.info("ℹ️ Henüz yeni ürünler için sevkiyat yapılmamış.")
                    st.write("Lütfen 'Sevkiyat Hesaplama' menüsünden hesaplama yapın.")
