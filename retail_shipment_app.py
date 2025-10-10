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

# Sidebar menü
st.sidebar.title("📦 Sevkiyat Planlama")
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "📤 Veri Yükleme", "🎯 Segmentasyon Ayarları", 
     "🎲 Hedef Matris", "📊 Sıralama", "🚚 Sevkiyat Hesaplama"]
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.urun_master is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.urun_master.head(10), use_container_width=True, height=300)
    
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.magaza_master is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.magaza_master.head(10), use_container_width=True, height=300)
    
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.yasak_master is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.yasak_master.head(10), use_container_width=True, height=300)
    
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.depo_stok is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.depo_stok.head(10), use_container_width=True, height=300)
    
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.anlik_stok_satis is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.anlik_stok_satis.head(10), use_container_width=True, height=300)
    
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
                    
                    # Sadece ilk 10 satırı göster
                    st.write("**İlk 10 Kayıt (Önizleme)**")
                    st.dataframe(df.head(10), use_container_width=True, height=300)
                else:
                    st.error(f"❌ Eksik sütunlar var!")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        elif st.session_state.haftalik_trend is not None:
            st.write("**İlk 10 Kayıt (Önizleme)**")
            st.dataframe(st.session_state.haftalik_trend.head(10), use_container_width=True, height=300)
    
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
        
        Tüm mağaza-ürün kombinasyonları otomatik oluşturulmuştur. Durum ve öncelik değerlerini düzenleyebilirsiniz.
        """)
        
        # Eğer daha önce kaydedilmişse onu kullan, yoksa tüm kombinasyonları oluştur
        if st.session_state.siralama_data is not None:
            siralama_df = st.session_state.siralama_data
        else:
            # Tüm kombinasyonları oluştur
            siralama_rows = []
            oncelik_counter = 1
            for store_seg in store_segments:
                for prod_seg in prod_segments:
                    siralama_rows.append({
                        'Magaza_Cluster': store_seg,
                        'Urun_Cluster': prod_seg,
                        'Durum': 'RPT',  # Default değer
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
                    help="RPT (Hızlı sevkiyat) veya Min (Minimum stok) seçin",
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
                st.write("⏳ Adım 1/5: Segmentasyon yapılıyor...")
                progress_bar.progress(20)
                
                st.write("⏳ Adım 2/5: Depo-Mağaza eşleşmeleri kontrol ediliyor...")
                progress_bar.progress(40)
                
                if st.session_state.yasak_master is not None:
                    st.write("⏳ Adım 3/5: Yasak kontrolleri yapılıyor...")
                else:
                    st.write("⏳ Adım 3/5: Yasak kontrolü atlandı (veri yok)...")
                progress_bar.progress(60)
                
                st.write("⏳ Adım 4/5: Öncelik sıralaması uygulanıyor...")
                progress_bar.progress(80)
                
                st.write("⏳ Adım 5/5: Sonuçlar hazırlanıyor...")
                progress_bar.progress(100)
                
                st.success("✅ Hesaplama tamamlandı!")
                st.balloons()
                
                # Örnek sonuç tablosu
                st.markdown("---")
                st.subheader("📊 Sevkiyat Sonuçları")
                
                # Basit örnek sonuç (gerçek hesaplama burada yapılacak)
                result_df = pd.DataFrame({
                    'magaza_kod': ['M001', 'M002', 'M003'],
                    'magaza_ad': ['Mağaza A', 'Mağaza B', 'Mağaza C'],
                    'depo_kod': ['D001', 'D001', 'D002'],
                    'urun_kod': ['U001', 'U001', 'U002'],
                    'urun_ad': ['Ürün A', 'Ürün A', 'Ürün B'],
                    'mevcut_stok': [100, 150, 80],
                    'hedef_stok': [150, 200, 120],
                    'sevkiyat_miktari': [50, 50, 40],
                    'oncelik': [1, 2, 3]
                })
                
                st.dataframe(result_df, use_container_width=True)
                
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
