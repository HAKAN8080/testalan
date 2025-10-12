import streamlit as st
import pandas as pd
import numpy as np
import time

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
if 'initial_matris' not in st.session_state:
    st.session_state.initial_matris = None
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
st.sidebar.title("📦 Sevkiyat ve WSSI Alım Sipariş Sistemi")
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "📤 Veri Yükleme", "🫧 Segmentasyon", 
     "🎲 Hedef Matris", "🔢 Sıralama", "📐 Hesaplama", "💵 Alım Sipariş", "📈 Raporlar", "💾 Master Data"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================
if menu == "🏠 Ana Sayfa":
    st.title("🌟 AR4U - Thorius Planlama Sistemi")
    st.markdown("---")
    
   
    st.markdown("### 📋 İşlem Adımları")
    st.info("""
    1. **Veri Yükleme**: Tüm CSV dosyalarını yükleyin
    2. **Segmentasyon**: Ürün ve mağaza gruplama aralıklarını belirleyin (opsiyonel)
    3. **Hedef Matris**: Her segment için parametreleri girin (opsiyonel)
    4. **Sıralama**: Öncelikleri belirleyin (opsiyonel)
    5. **Hesaplama**: Sevkiyat sonuçlarını görüntüleyin
    6. **Alım Sipariş**: Tedarikçiden alınması gereken ürünleri hesaplayın
    7. **Raporlar**: Detaylı analizleri inceleyin
    8. **Master Data**: Tüm verileri tek CSV'de birleştirin
    """)
    
# ============================================
# 📤 VERİ YÜKLEME
# ============================================
elif menu == "📤 Veri Yükleme":
    st.title("📤 Veri Yükleme")
    st.markdown("---")
    
    # Örnek CSV'ler (bu kısım aynı kalıyor, değiştirme)
    with st.expander("📥 Örnek CSV'leri İndir", expanded=False):
        st.info("Tüm örnek CSV dosyalarını aşağıdan indirebilirsiniz.")
        
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
    
    # CSV Yükleme - YENİ SİSTEM
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Ürün Master", "Mağaza Master", "Yasak", "Depo Stok", 
        "Anlık Stok/Satış", "Haftalık Trend", "KPI"
    ])
    
    # 1. ÜRÜN MASTER - YENİ
    with tab1:
        st.subheader("📦 Ürün Master")
        st.info("Kolonlar: urun_kod, urun_ad, satici_kod, satici_ad, kategori_kod, kategori_ad, umg, umg_ad, mg, mg_ad, marka_kod, marka_ad, nitelik, durum, ithal, ithal_ad, tanim")
        
        if st.session_state.urun_master is not None:
            st.success(f"✅ {len(st.session_state.urun_master)} ürün yüklü!")
            st.dataframe(st.session_state.urun_master.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_urun"):
                st.session_state.urun_master = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Ürün Master CSV yükle", type=['csv'], key="urun_master_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.urun_master = df
                    st.success(f"✅ {len(df)} ürün yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 2. MAĞAZA MASTER - YENİ
    with tab2:
        st.subheader("🏪 Mağaza Master")
        st.info("Kolonlar: magaza_kod, magaza_ad, il, bolge, tip, adres_kod, sm, bs, depo_kod")
        
        if st.session_state.magaza_master is not None:
            st.success(f"✅ {len(st.session_state.magaza_master)} mağaza yüklü!")
            st.dataframe(st.session_state.magaza_master.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_magaza"):
                st.session_state.magaza_master = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Mağaza Master CSV yükle", type=['csv'], key="magaza_master_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.magaza_master = df
                    st.success(f"✅ {len(df)} mağaza yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 3. YASAK - YENİ
    with tab3:
        st.subheader("🚫 Yasak Master")
        st.info("Kolonlar: urun_kod, urun_ad, magaza_kod, magaza_ad, yasak_durum")
        
        if st.session_state.yasak_master is not None:
            st.success(f"✅ {len(st.session_state.yasak_master)} yasak kaydı yüklü!")
            st.dataframe(st.session_state.yasak_master.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_yasak"):
                st.session_state.yasak_master = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Yasak CSV yükle", type=['csv'], key="yasak_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.yasak_master = df
                    st.success(f"✅ {len(df)} yasak kaydı yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 4. DEPO STOK - YENİ
    with tab4:
        st.subheader("📦 Depo Stok")
        st.info("Kolonlar: depo_kod, depo_ad, urun_kod, urun_ad, stok")
        
        if st.session_state.depo_stok is not None:
            st.success(f"✅ {len(st.session_state.depo_stok)} depo stok kaydı yüklü!")
            st.dataframe(st.session_state.depo_stok.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_depo"):
                st.session_state.depo_stok = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Depo Stok CSV yükle", type=['csv'], key="depo_stok_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.depo_stok = df
                    st.success(f"✅ {len(df)} depo stok kaydı yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 5. ANLIK STOK SATIŞ - YENİ
    with tab5:
        st.subheader("📊 Anlık Stok/Satış")
        st.info("Kolonlar: magaza_kod, magaza_ad, urun_kod, urun_ad, klasman_kod, klasman_ad, marka_kod, marka_ad, stok, yol, satis, ciro, smm")
        
        if st.session_state.anlik_stok_satis is not None:
            st.success(f"✅ {len(st.session_state.anlik_stok_satis)} kayıt yüklü!")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Toplam Mağaza", st.session_state.anlik_stok_satis['magaza_kod'].nunique())
            with col2:
                st.metric("Toplam Ürün", st.session_state.anlik_stok_satis['urun_kod'].nunique())
            st.dataframe(st.session_state.anlik_stok_satis.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_anlik"):
                st.session_state.anlik_stok_satis = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Anlık Stok/Satış CSV yükle", type=['csv'], key="anlik_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.anlik_stok_satis = df
                    st.success(f"✅ {len(df)} kayıt yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 6. HAFTALIK TREND - YENİ
    with tab6:
        st.subheader("📈 Haftalık Trend")
        st.info("Kolonlar: klasman_kod, klasman_ad, marka_kod, marka_ad, yil, hafta, stok, satis, ciro, smm, iftutar")
        
        if st.session_state.haftalik_trend is not None:
            st.success(f"✅ {len(st.session_state.haftalik_trend)} haftalık veri yüklü!")
            st.dataframe(st.session_state.haftalik_trend.head(10), use_container_width=True, height=400)
            if st.button("🔄 Yeni Dosya Yükle", key="reload_haftalik"):
                st.session_state.haftalik_trend = None
                st.rerun()
        else:
            uploaded = st.file_uploader("Haftalık Trend CSV yükle", type=['csv'], key="haftalik_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.haftalik_trend = df
                    st.success(f"✅ {len(df)} haftalık veri yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
    
    # 7. KPI - YENİ
    with tab7:
        st.subheader("🎯 KPI Parametreleri")
        st.info("Kolonlar: mg_id, mg_ad, min_deger, max_deger, forward_cover")
        
        if st.session_state.kpi is not None:
            st.success(f"✅ {len(st.session_state.kpi)} KPI kaydı yüklü!")
            edited_df = st.data_editor(
                st.session_state.kpi,
                num_rows="dynamic",
                use_container_width=True,
                height=300
            )
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 Değişiklikleri Kaydet", key="save_kpi"):
                    st.session_state.kpi = edited_df
                    st.success("✅ Kaydedildi!")
                    st.rerun()
            with col2:
                if st.button("🔄 Yeni Dosya Yükle", key="reload_kpi"):
                    st.session_state.kpi = None
                    st.rerun()
        else:
            uploaded = st.file_uploader("KPI CSV yükle", type=['csv'], key="kpi_upload")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.session_state.kpi = df
                    st.success(f"✅ {len(df)} KPI kaydı yüklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
                    
# ============================================
# 🎯 SEGMENTASYON AYARLARI
# ============================================
elif menu == "🫧 Segmentasyon":
    st.title("🫧 Segmentasyon")
    st.markdown("---")
    
    st.info("**Stok/Satış oranına göre** ürün ve mağazaları gruplandırma (Toplam Stok / Toplam Satış)")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
        st.stop()
    
    # Ürün bazında toplam stok/satış hesapla
    data = st.session_state.anlik_stok_satis.copy()
    
    # Ürün bazında gruplama
    urun_aggregated = data.groupby('urun_kod').agg({
        'urun_ad': 'first',
        'marka_ad': 'first',
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
    urun_aggregated['cover'] = urun_aggregated['stok_satis_orani']
    
    # Mağaza bazında gruplama
    magaza_aggregated = data.groupby('magaza_kod').agg({
        'magaza_ad': 'first',
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
    magaza_aggregated['cover'] = magaza_aggregated['stok_satis_orani']
    
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
    
    # Ürün segmentasyonunu uygula
    if urun_aggregated is not None and len(urun_aggregated) > 0:
        temp_prod = urun_aggregated.copy()
        
        # Segment labels
        product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
        
        temp_prod['segment'] = pd.cut(
            temp_prod['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=product_labels,
            include_lowest=True
        )
        
        st.write("**Ürün Dağılımı Önizleme:**")
        segment_dist = temp_prod['segment'].value_counts().sort_index()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(segment_dist, use_container_width=True, height=200)
        with col2:
            st.bar_chart(segment_dist)
        
        st.markdown("---")
        
        # DETAYLI ÜRÜN SEGMENTASYON TABLOSU
        st.subheader("📋 Detaylı Ürün Segmentasyon Tablosu")
        
        # Tabloyu hazırla
        urun_detail = temp_prod[['urun_kod', 'urun_ad', 'marka_ad', 'segment', 
                                  'stok', 'yol', 'satis', 'ciro', 'stok_satis_orani']].copy()
        urun_detail = urun_detail.sort_values(['segment', 'stok_satis_orani'], ascending=[True, False])
        urun_detail.columns = ['Ürün Kodu', 'Ürün Adı', 'Marka', 'Segment', 
                               'Toplam Stok', 'Toplam Yol', 'Toplam Satış', 'Toplam Ciro', 'Stok/Satış Oranı']
        
        # Segment bazında filtreleme
        selected_segment_prod = st.multiselect(
            "Segment Seç (Filtre)",
            options=product_labels,
            default=product_labels,
            key="filter_prod_segment"
        )
        
        filtered_urun = urun_detail[urun_detail['Segment'].isin(selected_segment_prod)]
        
        st.write(f"**Toplam {len(filtered_urun)} ürün gösteriliyor**")
        st.dataframe(
            filtered_urun.style.format({
                'Toplam Stok': '{:,.0f}',
                'Toplam Yol': '{:,.0f}',
                'Toplam Satış': '{:,.0f}',
                'Toplam Ciro': '{:,.2f}',
                'Stok/Satış Oranı': '{:.2f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Segment bazında özet
        st.markdown("---")
        st.subheader("📊 Segment Bazında Ürün Özeti")
        
        segment_ozet = urun_detail.groupby('Segment').agg({
            'Ürün Kodu': 'count',
            'Toplam Stok': 'sum',
            'Toplam Satış': 'sum',
            'Toplam Ciro': 'sum',
            'Stok/Satış Oranı': 'mean'
        }).reset_index()
        segment_ozet.columns = ['Segment', 'Ürün Sayısı', 'Toplam Stok', 'Toplam Satış', 'Toplam Ciro', 'Ort. Cover']
        
        st.dataframe(
            segment_ozet.style.format({
                'Toplam Stok': '{:,.0f}',
                'Toplam Satış': '{:,.0f}',
                'Toplam Ciro': '{:,.2f}',
                'Ort. Cover': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # CSV İndir - ÜRÜN
        st.download_button(
            label="📥 Ürün Segmentasyon Detayı İndir (CSV)",
            data=urun_detail.to_csv(index=False, encoding='utf-8-sig'),
            file_name="urun_segmentasyon_detay.csv",
            mime="text/csv",
            key="download_urun_segment"
        )
    
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
    
    # Mağaza segmentasyonunu uygula
    if magaza_aggregated is not None and len(magaza_aggregated) > 0:
        temp_store = magaza_aggregated.copy()
        
        # Segment labels
        store_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
        
        temp_store['segment'] = pd.cut(
            temp_store['stok_satis_orani'], 
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=store_labels,
            include_lowest=True
        )
        
        st.write("**Mağaza Dağılımı Önizleme:**")
        segment_dist_store = temp_store['segment'].value_counts().sort_index()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(segment_dist_store, use_container_width=True, height=200)
        with col2:
            st.bar_chart(segment_dist_store)
        
        st.markdown("---")
        
        # DETAYLI MAĞAZA SEGMENTASYON TABLOSU
        st.subheader("📋 Detaylı Mağaza Segmentasyon Tablosu")
        
        # Tabloyu hazırla
        magaza_detail = temp_store[['magaza_kod', 'magaza_ad', 'segment', 
                                     'stok', 'yol', 'satis', 'ciro', 'stok_satis_orani']].copy()
        magaza_detail = magaza_detail.sort_values(['segment', 'stok_satis_orani'], ascending=[True, False])
        magaza_detail.columns = ['Mağaza Kodu', 'Mağaza Adı', 'Segment', 
                                 'Toplam Stok', 'Toplam Yol', 'Toplam Satış', 'Toplam Ciro', 'Stok/Satış Oranı']
        
        # Segment bazında filtreleme
        selected_segment_store = st.multiselect(
            "Segment Seç (Filtre)",
            options=store_labels,
            default=store_labels,
            key="filter_store_segment"
        )
        
        filtered_magaza = magaza_detail[magaza_detail['Segment'].isin(selected_segment_store)]
        
        st.write(f"**Toplam {len(filtered_magaza)} mağaza gösteriliyor**")
        st.dataframe(
            filtered_magaza.style.format({
                'Toplam Stok': '{:,.0f}',
                'Toplam Yol': '{:,.0f}',
                'Toplam Satış': '{:,.0f}',
                'Toplam Ciro': '{:,.2f}',
                'Stok/Satış Oranı': '{:.2f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Segment bazında özet
        st.markdown("---")
        st.subheader("📊 Segment Bazında Mağaza Özeti")
        
        segment_ozet_magaza = magaza_detail.groupby('Segment').agg({
            'Mağaza Kodu': 'count',
            'Toplam Stok': 'sum',
            'Toplam Satış': 'sum',
            'Toplam Ciro': 'sum',
            'Stok/Satış Oranı': 'mean'
        }).reset_index()
        segment_ozet_magaza.columns = ['Segment', 'Mağaza Sayısı', 'Toplam Stok', 'Toplam Satış', 'Toplam Ciro', 'Ort. Cover']
        
        st.dataframe(
            segment_ozet_magaza.style.format({
                'Toplam Stok': '{:,.0f}',
                'Toplam Satış': '{:,.0f}',
                'Toplam Ciro': '{:,.2f}',
                'Ort. Cover': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # CSV İndir - MAĞAZA
        st.download_button(
            label="📥 Mağaza Segmentasyon Detayı İndir (CSV)",
            data=magaza_detail.to_csv(index=False, encoding='utf-8-sig'),
            file_name="magaza_segmentasyon_detay.csv",
            mime="text/csv",
            key="download_magaza_segment"
        )
    
    st.markdown("---")
    
    # Kaydet butonu
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Segmentasyonu Kaydet", type="primary"):
            st.session_state.segmentation_params = {
                'product_ranges': product_ranges,
                'store_ranges': store_ranges
            }
            st.success("✅ Ayarlar kaydedildi!")
    with col2:
        st.info("ℹ️ Kaydetmeseniz de default değerler kullanılacaktır.")
    
    st.markdown("---")
    
    # HER İKİSİNİ BİRLİKTE İNDİR
    st.subheader("📥 Tüm Segmentasyon Verilerini İndir")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel formatında (iki sheet)
        if st.button("📊 Excel İndir (Ürün + Mağaza)", use_container_width=True):
            try:
                import io
                from io import BytesIO
                
                # Excel writer oluştur
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    urun_detail.to_excel(writer, sheet_name='Ürün Segmentasyon', index=False)
                    magaza_detail.to_excel(writer, sheet_name='Mağaza Segmentasyon', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Excel Dosyasını İndir",
                    data=output.getvalue(),
                    file_name="segmentasyon_tam_detay.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.error("❌ Excel export için 'openpyxl' kütüphanesi gerekli. Lütfen yükleyin: pip install openpyxl")
    
    with col2:
        # ZIP formatında (iki CSV)
        if st.button("📦 ZIP İndir (2 CSV)", use_container_width=True):
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Ürün CSV
                urun_csv = urun_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('urun_segmentasyon.csv', urun_csv.encode('utf-8-sig'))
                
                # Mağaza CSV
                magaza_csv = magaza_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('magaza_segmentasyon.csv', magaza_csv.encode('utf-8-sig'))
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="⬇️ ZIP Dosyasını İndir",
                data=zip_buffer.getvalue(),
                file_name="segmentasyon_detay.zip",
                mime="application/zip"
            )
            
# ============================================
# 🎲 HEDEF MATRİS
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
            sisme_data = pd.DataFrame(0.5, index=prod_segments, columns=store_segments)
        else:
            sisme_data = st.session_state.sisme_orani
        
        edited_sisme = st.data_editor(
            sisme_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col, min_value=0.0, max_value=10.0, step=0.1, format="%.2f"
            ) for col in store_segments},
            key="sisme_matrix"
        )
        
        st.markdown("---")
        
        # 2. GENLEŞTİRME ORANI MATRİSİ
        st.markdown("### 2️⃣ Genleştirme Oranı Matrisi (Default: 1.0)")
        
        if st.session_state.genlestirme_orani is None:
            genlestirme_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            genlestirme_data = st.session_state.genlestirme_orani
        
        edited_genlestirme = st.data_editor(
            genlestirme_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col, min_value=0.0, max_value=10.0, step=0.1, format="%.2f"
            ) for col in store_segments},
            key="genlestirme_matrix"
        )
        
        st.markdown("---")
        
        # 3. MIN ORAN MATRİSİ
        st.markdown("### 3️⃣ Min Oran Matrisi (Default: 1.0)")
        
        if st.session_state.min_oran is None:
            min_oran_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            min_oran_data = st.session_state.min_oran
        
        edited_min_oran = st.data_editor(
            min_oran_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col, min_value=0.0, max_value=10.0, step=0.1, format="%.2f"
            ) for col in store_segments},
            key="min_oran_matrix"
        )
        
        st.markdown("---")
        
        # 4. INITIAL MATRİSİ
        st.markdown("### 4️⃣ Initial Matris (Yeni Ürünler İçin - Default: 1.0)")
        
        if st.session_state.initial_matris is None:
            initial_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            initial_data = st.session_state.initial_matris
        
        edited_initial = st.data_editor(
            initial_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col, min_value=0.0, max_value=10.0, step=0.1, format="%.2f"
            ) for col in store_segments},
            key="initial_matrix"
        )
        
        st.markdown("---")
        
        # Kaydet butonu
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Tüm Matrisleri Kaydet", type="primary"):
                st.session_state.sisme_orani = edited_sisme
                st.session_state.genlestirme_orani = edited_genlestirme
                st.session_state.min_oran = edited_min_oran
                st.session_state.initial_matris = edited_initial
                st.success("✅ Tüm matrisler kaydedildi!")
        with col2:
            st.info("ℹ️ Kaydetmeseniz de default değerler kullanılacaktır.")

# ============================================
# 📊 SIRALAMA
# ============================================
elif menu == "🔢 Sıralama":
    st.title("🔢 Sıralama")
    st.markdown("---")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
    else:
        st.info("Mağaza ve ürün cluster bazında sevkiyat önceliklerini belirleyin")
        
        # Segmentleri al
        data = st.session_state.anlik_stok_satis.copy()
        
        urun_aggregated = data.groupby('urun_kod').agg({'stok': 'sum', 'satis': 'sum'}).reset_index()
        urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
        
        magaza_aggregated = data.groupby('magaza_kod').agg({'stok': 'sum', 'satis': 'sum'}).reset_index()
        magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
        
        product_ranges = st.session_state.segmentation_params['product_ranges']
        urun_aggregated['urun_segment'] = pd.cut(
            urun_aggregated['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in product_ranges],
            include_lowest=True
        )
        
        store_ranges = st.session_state.segmentation_params['store_ranges']
        magaza_aggregated['magaza_segment'] = pd.cut(
            magaza_aggregated['stok_satis_orani'],
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in store_ranges],
            include_lowest=True
        )
        
        prod_segments = sorted([str(x) for x in urun_aggregated['urun_segment'].unique() if pd.notna(x)])
        store_segments = sorted([str(x) for x in magaza_aggregated['magaza_segment'].unique() if pd.notna(x)])
        
        st.subheader("🎯 Öncelik Sıralaması")
        
        st.info("""
        **RPT:** Hızlı sevkiyat önceliği
        **Initial:** Yeni ürün önceliği
        **Min:** Minimum stok önceliği
        """)
        
        if st.session_state.siralama_data is not None:
            siralama_df = st.session_state.siralama_data
        else:
            def sort_segments(segments):
                def get_sort_key(seg):
                    try:
                        return int(seg.split('-')[0])
                    except:
                        return 999
                return sorted(segments, key=get_sort_key)
            
            sorted_store = sort_segments(store_segments)
            sorted_prod = sort_segments(prod_segments)
            
            siralama_rows = []
            oncelik = 1
            for store_seg in sorted_store:
                for prod_seg in sorted_prod:
                    siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'RPT', 'Oncelik': oncelik})
                    oncelik += 1
                    siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'Initial', 'Oncelik': oncelik})
                    oncelik += 1
                    siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'Min', 'Oncelik': oncelik})
                    oncelik += 1
            
            siralama_df = pd.DataFrame(siralama_rows)
        
        st.markdown("---")
        st.subheader("📋 Tüm Kombinasyonlar")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Tabloyu Sıfırla", type="secondary"):
                st.session_state.siralama_data = None
                st.success("✅ Sıfırlandı!")
                st.rerun()
        
        edited_siralama = st.data_editor(
            siralama_df.sort_values('Oncelik').reset_index(drop=True),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Magaza_Cluster": st.column_config.SelectboxColumn("Mağaza Cluster", options=store_segments, required=True),
                "Urun_Cluster": st.column_config.SelectboxColumn("Ürün Cluster", options=prod_segments, required=True),
                "Durum": st.column_config.SelectboxColumn("Durum", options=["RPT", "Initial", "Min"], required=True),
                "Oncelik": st.column_config.NumberColumn("Öncelik", min_value=1, max_value=1000, step=1, format="%d")
            },
            hide_index=False,
            height=500
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Sıralamayı Kaydet", type="primary"):
                st.session_state.siralama_data = edited_siralama
                st.success("✅ Kaydedildi!")
        with col2:
            if st.button("🔄 Varsayılana Sıfırla"):
                st.session_state.siralama_data = None
                st.success("✅ Varsayılana sıfırlandı!")
                st.rerun()
        
        st.info("ℹ️ Kaydetmeseniz de default sıralama kullanılacaktır.")
# ============================================
# 🚚 HESAPLAMA
# ============================================
elif menu == "📐 Hesaplama":
    st.title("📐 Hesaplama")
    st.markdown("---")
    
    required_data = {
        "Ürün Master": st.session_state.urun_master,
        "Mağaza Master": st.session_state.magaza_master,
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi
    }
    
    optional_data = {
        "Haftalık Trend": st.session_state.haftalik_trend,
        "Yasak Master": st.session_state.yasak_master
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    optional_loaded = [name for name, data in optional_data.items() if data is not None]
    
    if missing_data:
        st.warning("⚠️ Tüm zorunlu verileri yükleyin!")
        st.error(f"**Eksik:** {', '.join(missing_data)}")
        st.info("""
        Zorunlu: Ürün Master, Mağaza Master, Depo Stok, Anlık Stok/Satış, KPI
        Opsiyonel: Segmentasyon, Matrisler, Sıralama, Haftalık Trend, Yasak
        """)
        if optional_loaded:
            st.success(f"✅ Yüklü opsiyonel: {', '.join(optional_loaded)}")
    else:
        st.success("✅ Tüm zorunlu veriler hazır!")
        
        if optional_loaded:
            st.info(f"📌 Opsiyonel: {', '.join(optional_loaded)}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Toplam Ürün", st.session_state.anlik_stok_satis['urun_kod'].nunique())
        with col2:
            st.metric("Toplam Mağaza", st.session_state.anlik_stok_satis['magaza_kod'].nunique())
        with col3:
            st.metric("Depo Stok", f"{st.session_state.depo_stok['stok'].sum():,.0f}")
        with col4:
            yasak_count = len(st.session_state.yasak_master) if st.session_state.yasak_master is not None else 0
            st.metric("Yasak", yasak_count)
        
        st.markdown("---")
        st.subheader("🏢 Depo-Mağaza Eşleşmeleri")
        magaza_depo = st.session_state.magaza_master[['magaza_kod', 'magaza_ad', 'depo_kod']].copy()
        st.dataframe(magaza_depo, use_container_width=True, height=200)
        st.info("ℹ️ Her mağaza sadece kendi depo_kod'una atanmış depodan mal alır.")
        st.markdown("---")
        
        if st.button("🚀 Sevkiyat Hesapla", type="primary", use_container_width=True):
            start_time = time.time()
            
            with st.spinner("📊 Hesaplama yapılıyor..."):
                progress_bar = st.progress(0, text="Veri hazırlanıyor...")
                
                anlik_df = st.session_state.anlik_stok_satis.copy()
                magaza_df = st.session_state.magaza_master.copy()
                depo_df = st.session_state.depo_stok.copy()
                kpi_df = st.session_state.kpi.copy()
                
                # Default matrisler
                if st.session_state.sisme_orani is None:
                    st.session_state.sisme_orani = pd.DataFrame(0.5, index=["0-4"], columns=["0-4"])
                if st.session_state.genlestirme_orani is None:
                    st.session_state.genlestirme_orani = pd.DataFrame(1.0, index=["0-4"], columns=["0-4"])
                if st.session_state.min_oran is None:
                    st.session_state.min_oran = pd.DataFrame(1.0, index=["0-4"], columns=["0-4"])
                if st.session_state.initial_matris is None:
                    st.session_state.initial_matris = pd.DataFrame(1.0, index=["0-4"], columns=["0-4"])
                
                progress_bar.progress(10, text="Yeni ürünler tespit ediliyor...")
                
                # YENİ ÜRÜN TESPİTİ
                depo_df_temp = depo_df.copy()
                depo_df_temp['urun_kod'] = depo_df_temp['urun_kod'].astype(str).apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                depo_toplam = depo_df_temp.groupby('urun_kod')['stok'].sum().reset_index()
                depo_toplam.columns = ['urun_kod', 'depo_stok_toplam']
                yeni_urun_adaylari = depo_toplam[depo_toplam['depo_stok_toplam'] > 300]['urun_kod'].tolist()
                
                toplam_magaza_sayisi = anlik_df['magaza_kod'].nunique()
                anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                urun_magaza_stok = anlik_df[anlik_df['urun_kod'].isin(yeni_urun_adaylari)].copy()
                urun_magaza_stok = urun_magaza_stok[urun_magaza_stok['stok'] > 0]
                
                urun_stoklu_magaza = urun_magaza_stok.groupby('urun_kod')['magaza_kod'].nunique().reset_index()
                urun_stoklu_magaza.columns = ['urun_kod', 'stoklu_magaza_sayisi']
                urun_stoklu_magaza['magaza_oran'] = urun_stoklu_magaza['stoklu_magaza_sayisi'] / toplam_magaza_sayisi
                
                yeni_urunler = urun_stoklu_magaza[urun_stoklu_magaza['magaza_oran'] < 0.5].copy()
                yeni_urun_kodlari = yeni_urunler['urun_kod'].tolist()
                
                st.session_state.yeni_urun_listesi = yeni_urunler.merge(depo_toplam, on='urun_kod', how='left')
                
                progress_bar.progress(25, text="Segmentasyon yapılıyor...")
                
                # Segmentasyon
                urun_agg = anlik_df.groupby('urun_kod').agg({'stok': 'sum', 'satis': 'sum'}).reset_index()
                urun_agg['cover'] = urun_agg['stok'] / urun_agg['satis'].replace(0, 1)
                
                magaza_agg = anlik_df.groupby('magaza_kod').agg({'stok': 'sum', 'satis': 'sum'}).reset_index()
                magaza_agg['cover'] = magaza_agg['stok'] / magaza_agg['satis'].replace(0, 1)
                
                product_ranges = st.session_state.segmentation_params['product_ranges']
                store_ranges = st.session_state.segmentation_params['store_ranges']
                
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
                
                anlik_df = anlik_df.merge(urun_agg[['urun_kod', 'segment']], on='urun_kod', how='left').rename(columns={'segment': 'urun_segment'})
                anlik_df = anlik_df.merge(magaza_agg[['magaza_kod', 'segment']], on='magaza_kod', how='left').rename(columns={'segment': 'magaza_segment'})
                
                anlik_df['urun_segment'] = anlik_df['urun_segment'].astype(str)
                anlik_df['magaza_segment'] = anlik_df['magaza_segment'].astype(str)
                
                progress_bar.progress(40, text="KPI verileri hazırlanıyor...")
                
                # KPI
                default_fc = kpi_df['forward_cover'].mean()
                
                if st.session_state.urun_master is not None:
                    urun_master = st.session_state.urun_master[['urun_kod', 'mg']].copy()
                    urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    urun_master['mg'] = urun_master['mg'].fillna(0).astype(float).astype(int).astype(str)
                    
                    anlik_df = anlik_df.merge(urun_master, on='urun_kod', how='left')
                    
                    kpi_data = kpi_df[['mg_id', 'min_deger', 'max_deger']].rename(columns={'mg_id': 'mg'})
                    kpi_data['mg'] = kpi_data['mg'].astype(str)
                    anlik_df['mg'] = anlik_df['mg'].astype(str)
                    
                    anlik_df = anlik_df.merge(kpi_data, on='mg', how='left')
                    anlik_df['min_deger'] = anlik_df['min_deger'].fillna(0)
                    anlik_df['max_deger'] = anlik_df['max_deger'].fillna(999999)
                else:
                    anlik_df['min_deger'] = 0
                    anlik_df['max_deger'] = 999999
                
                progress_bar.progress(55, text="Matris değerleri uygulanıyor...")
                
                # Matris değerleri
                def get_matrix_value(magaza_seg, urun_seg, matrix):
                    try:
                        return matrix.loc[urun_seg, magaza_seg]
                    except:
                        return 1.0
                
                anlik_df['genlestirme'] = anlik_df.apply(
                    lambda row: get_matrix_value(row['magaza_segment'], row['urun_segment'], st.session_state.genlestirme_orani), axis=1
                )
                anlik_df['sisme'] = anlik_df.apply(
                    lambda row: get_matrix_value(row['magaza_segment'], row['urun_segment'], st.session_state.sisme_orani), axis=1
                )
                anlik_df['min_oran'] = anlik_df.apply(
                    lambda row: get_matrix_value(row['magaza_segment'], row['urun_segment'], st.session_state.min_oran), axis=1
                )
                anlik_df['initial_katsayi'] = anlik_df.apply(
                    lambda row: get_matrix_value(row['magaza_segment'], row['urun_segment'], st.session_state.initial_matris), axis=1
                )
                
                progress_bar.progress(70, text="İhtiyaçlar hesaplanıyor...")
                
                # RPT, Initial, Min satırları oluştur
                anlik_rpt = anlik_df.copy()
                anlik_rpt['Durum'] = 'RPT'
                
                anlik_min = anlik_df.copy()
                anlik_min['Durum'] = 'Min'
                
                if len(yeni_urun_kodlari) > 0:
                    anlik_initial = anlik_df[anlik_df['urun_kod'].astype(str).isin(yeni_urun_kodlari)].copy()
                    anlik_initial['Durum'] = 'Initial'
                    anlik_df = pd.concat([anlik_rpt, anlik_initial, anlik_min], ignore_index=True)
                else:
                    anlik_df = pd.concat([anlik_rpt, anlik_min], ignore_index=True)
                
                # Sıralama
                if st.session_state.siralama_data is not None:
                    siralama_df = st.session_state.siralama_data.copy()
                else:
                    prod_segments = sorted([str(x) for x in urun_agg['segment'].unique() if pd.notna(x)])
                    store_segments = sorted([str(x) for x in magaza_agg['segment'].unique() if pd.notna(x)])
                    
                    siralama_rows = []
                    oncelik_counter = 1
                    for store_seg in store_segments:
                        for prod_seg in prod_segments:
                            siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'RPT', 'Oncelik': oncelik_counter})
                            oncelik_counter += 1
                            siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'Initial', 'Oncelik': oncelik_counter})
                            oncelik_counter += 1
                            siralama_rows.append({'Magaza_Cluster': store_seg, 'Urun_Cluster': prod_seg, 'Durum': 'Min', 'Oncelik': oncelik_counter})
                            oncelik_counter += 1
                    
                    siralama_df = pd.DataFrame(siralama_rows)
                
                anlik_df = anlik_df.merge(
                    siralama_df,
                    left_on=['magaza_segment', 'urun_segment', 'Durum'],
                    right_on=['Magaza_Cluster', 'Urun_Cluster', 'Durum'],
                    how='left'
                )
                
                # İhtiyaç hesapla
                anlik_df['ihtiyac_rpt'] = (default_fc * anlik_df['satis'] * anlik_df['genlestirme']) - (anlik_df['stok'] + anlik_df['yol'])
                anlik_df['ihtiyac_min'] = (anlik_df['min_oran'] * anlik_df['min_deger']) - (anlik_df['stok'] + anlik_df['yol'])
                anlik_df['ihtiyac_initial'] = (anlik_df['min_deger'] * anlik_df['initial_katsayi']) - (anlik_df['stok'] + anlik_df['yol'])
                
                anlik_df['ihtiyac'] = anlik_df.apply(
                    lambda row: (row['ihtiyac_rpt'] if row['Durum'] == 'RPT' 
                                else row['ihtiyac_min'] if row['Durum'] == 'Min'
                                else row['ihtiyac_initial']),
                    axis=1
                )
                
                anlik_df['ihtiyac'] = anlik_df['ihtiyac'].clip(lower=0)
                
                # max_deger kontrolü
                anlik_df['max_sevkiyat'] = anlik_df['max_deger'] - (anlik_df['stok'] + anlik_df['yol'])
                anlik_df['max_sevkiyat'] = anlik_df['max_sevkiyat'].clip(lower=0)
                anlik_df['ihtiyac'] = anlik_df.apply(
                    lambda row: min(row['ihtiyac'], row['max_sevkiyat']) if pd.notna(row['max_sevkiyat']) else row['ihtiyac'],
                    axis=1
                )
                
                progress_bar.progress(85, text="Yasak kontrolleri ve depo eşleştirme...")
                
                # Yasak kontrolü
                if st.session_state.yasak_master is not None:
                    yasak_df = st.session_state.yasak_master.copy()
                    yasak_df['urun_kod'] = yasak_df['urun_kod'].astype(str)
                    yasak_df['magaza_kod'] = yasak_df['magaza_kod'].astype(str)
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                    
                    anlik_df = anlik_df.merge(yasak_df[['urun_kod', 'magaza_kod', 'yasak_durum']], on=['urun_kod', 'magaza_kod'], how='left')
                    anlik_df.loc[anlik_df['yasak_durum'] == 'Yasak', 'ihtiyac'] = 0
                
                # Depo eşleşmesi
                magaza_df['magaza_kod'] = magaza_df['magaza_kod'].astype(str)
                anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                anlik_df = anlik_df.merge(magaza_df[['magaza_kod', 'depo_kod']], on='magaza_kod', how='left')
                
                progress_bar.progress(95, text="Depo stok kontrolleri yapılıyor...")
                
                # Önceliğe göre sırala
                result_df = anlik_df[anlik_df['ihtiyac'] > 0].copy()
                result_df_max = result_df.loc[result_df.groupby(['magaza_kod', 'urun_kod'])['ihtiyac'].idxmax()].copy()
                result_df_max = result_df_max.sort_values('Oncelik').reset_index(drop=True)
                
                # Depo stok kontrolü
                depo_stok_dict = {}
                for _, row in depo_df.iterrows():
                    depo_kod_str = str(row['depo_kod'])
                    urun_kod_raw = str(row['urun_kod'])
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
                
                result_df_max['urun_kod_clean'] = result_df_max['urun_kod'].astype(str).apply(
                    lambda x: str(int(float(x))) if ('.' in str(x)) else str(x)
                )
                result_df_max['depo_kod_clean'] = result_df_max['depo_kod'].astype(str)
                
                # Sevkiyat hesapla
                sevkiyat_gercek = []
                for idx, row in result_df_max.iterrows():
                    depo_kod = str(row['depo_kod'])
                    urun_kod_raw = str(row['urun_kod'])
                    try:
                        if '.' in urun_kod_raw:
                            urun_kod = str(int(float(urun_kod_raw)))
                        else:
                            urun_kod = urun_kod_raw
                    except:
                        urun_kod = urun_kod_raw
                    
                    ihtiyac = float(row['ihtiyac'])
                    key = (depo_kod, urun_kod)
                    
                    if key in depo_stok_dict:
                        kalan_stok = depo_stok_dict[key]
                        if kalan_stok >= ihtiyac:
                            sevkiyat = ihtiyac
                            depo_stok_dict[key] -= ihtiyac
                        else:
                            sevkiyat = kalan_stok
                            depo_stok_dict[key] = 0
                    else:
                        sevkiyat = 0
                    
                    sevkiyat_gercek.append(sevkiyat)
                
                result_df_max['sevkiyat_gercek'] = sevkiyat_gercek
                result_df_max['stok_yoklugu_kaybi'] = result_df_max['ihtiyac'] - result_df_max['sevkiyat_gercek']
                result_df_max = result_df_max[result_df_max['ihtiyac'] > 0].copy()
                
                # Sonuç tablosu
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
                
                result_final['stok_yoklugu_satis_kaybi'] = result_final['ihtiyac_miktari'] - result_final['sevkiyat_miktari']
                result_final.insert(0, 'sira_no', range(1, len(result_final) + 1))
                
                st.session_state.sevkiyat_sonuc = result_final
                
                end_time = time.time()
                calculation_time = end_time - start_time
                
                progress_bar.progress(100, text="Tamamlandı!")
                
                st.success("✅ Hesaplama tamamlandı!")
                st.balloons()
                
                # Sonuç tablosu
                st.markdown("---")
                st.subheader("📊 Sevkiyat Sonuçları")
                
                # Metrikler - İlk satır (KÜÇÜLTÜLMÜŞ - %60 boyut)
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
                
                with col1:
                    st.metric("⏱️", f"{calculation_time:.1f}s", "Süre")
                with col2:
                    ihtiyac_val = result_final['ihtiyac_miktari'].sum()
                    if ihtiyac_val >= 1000:
                        st.metric("📦", f"{ihtiyac_val/1000:.0f}K", "İhtiyaç")
                    else:
                        st.metric("📦", f"{ihtiyac_val:.0f}", "İhtiyaç")
                with col3:
                    sevk_val = result_final['sevkiyat_miktari'].sum()
                    if sevk_val >= 1000:
                        st.metric("✅", f"{sevk_val/1000:.0f}K", "Sevk")
                    else:
                        st.metric("✅", f"{sevk_val:.0f}", "Sevk")
                with col4:
                    sku_count = result_final[result_final['sevkiyat_miktari'] > 0]['urun_kod'].nunique()
                    st.metric("🏷️", f"{sku_count}", "SKU")
                with col5:
                    magaza_count = result_final[result_final['sevkiyat_miktari'] > 0]['magaza_kod'].nunique()
                    st.metric("🏪", f"{magaza_count}", "Mağaza")
                with col6:
                    sevk_per_magaza = result_final['sevkiyat_miktari'].sum() / magaza_count if magaza_count > 0 else 0
                    if sevk_per_magaza >= 1000:
                        st.metric("📊", f"{sevk_per_magaza/1000:.1f}K", "Sevk/Mğz")
                    else:
                        st.metric("📊", f"{sevk_per_magaza:.0f}", "Sevk/Mğz")
                with col7:
                    sk_val = result_final['stok_yoklugu_satis_kaybi'].sum()
                    if sk_val >= 1000:
                        st.metric("⚠️", f"{sk_val/1000:.0f}K", "SK")
                    else:
                        st.metric("⚠️", f"{sk_val:.0f}", "SK")
                with col8:
                    sk_oran = (result_final['stok_yoklugu_satis_kaybi'].sum() / result_final['ihtiyac_miktari'].sum() * 100) if result_final['ihtiyac_miktari'].sum() > 0 else 0
                    st.metric("📉", f"{sk_oran:.1f}%", "SK%")
                
                # Metrikler - İkinci satır (KÜÇÜLTÜLMÜŞ - %60 boyut)
                st.markdown("---")
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                rpt_sevk = result_final[result_final['durum'] == 'RPT']['sevkiyat_miktari'].sum()
                initial_sevk = result_final[result_final['durum'] == 'Initial']['sevkiyat_miktari'].sum()
                min_sevk = result_final[result_final['durum'] == 'Min']['sevkiyat_miktari'].sum()
                toplam_sevk = result_final['sevkiyat_miktari'].sum()
                
                with col1:
                    if rpt_sevk >= 1000:
                        st.metric("🚀", f"{rpt_sevk/1000:.0f}K", "RPT")
                    else:
                        st.metric("🚀", f"{rpt_sevk:.0f}", "RPT")
                with col2:
                    rpt_oran = (rpt_sevk / toplam_sevk * 100) if toplam_sevk > 0 else 0
                    st.metric("", f"{rpt_oran:.1f}%", "RPT %")
                with col3:
                    if initial_sevk >= 1000:
                        st.metric("🆕", f"{initial_sevk/1000:.0f}K", "Initial")
                    else:
                        st.metric("🆕", f"{initial_sevk:.0f}", "Initial")
                with col4:
                    initial_oran = (initial_sevk / toplam_sevk * 100) if toplam_sevk > 0 else 0
                    st.metric("", f"{initial_oran:.1f}%", "Init %")
                with col5:
                    if min_sevk >= 1000:
                        st.metric("📌", f"{min_sevk/1000:.0f}K", "Min")
                    else:
                        st.metric("📌", f"{min_sevk:.0f}", "Min")
                with col6:
                    min_oran = (min_sevk / toplam_sevk * 100) if toplam_sevk > 0 else 0
                    st.metric("", f"{min_oran:.1f}%", "Min %")
                
                st.markdown("---")
                
                # Stok yokluğu raporu
                st.markdown("---")
                st.subheader("⚠️ Stok Yokluğu Kaynaklı Satış Kaybı Raporu")
                
                stok_yoklugu_df = result_final[result_final['stok_yoklugu_satis_kaybi'] > 0].copy()
                
                if len(stok_yoklugu_df) > 0:
                    st.warning(f"⚠️ {len(stok_yoklugu_df)} satırda stok yokluğu var!")
                    
                    # Marka bilgisi ekle
                    if st.session_state.urun_master is not None:
                        urun_marka = st.session_state.urun_master[['urun_kod', 'marka_ad']].copy()
                        urun_marka['urun_kod'] = urun_marka['urun_kod'].astype(str).apply(
                            lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                        )
                        stok_yoklugu_df = stok_yoklugu_df.merge(urun_marka, on='urun_kod', how='left')
                    else:
                        stok_yoklugu_df['marka_ad'] = 'Bilinmiyor'
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**En Fazla Kayıp Olan 10 Satır:**")
                        top_kayip = stok_yoklugu_df.nlargest(10, 'stok_yoklugu_satis_kaybi')[[
                            'magaza_ad', 'urun_ad', 'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi'
                        ]]
                        st.dataframe(top_kayip, use_container_width=True)
                    
                    with col2:
                        st.write("**Marka Bazlı SK - En Yüksek 10 Ürün:**")
                        marka_kayip = stok_yoklugu_df.groupby(['marka_ad', 'urun_ad']).agg({
                            'ihtiyac_miktari': 'sum',
                            'sevkiyat_miktari': 'sum',
                            'stok_yoklugu_satis_kaybi': 'sum'
                        }).reset_index()
                        marka_kayip['SK %'] = (marka_kayip['stok_yoklugu_satis_kaybi'] / 
                                               marka_kayip['ihtiyac_miktari'] * 100).round(2)
                        marka_kayip = marka_kayip.nlargest(10, 'stok_yoklugu_satis_kaybi')[[
                            'marka_ad', 'urun_ad', 'ihtiyac_miktari', 'sevkiyat_miktari', 
                            'stok_yoklugu_satis_kaybi', 'SK %'
                        ]]
                        marka_kayip.columns = ['Marka', 'Ürün', 'İhtiyaç', 'Sevk', 'SK', 'SK %']
                        st.dataframe(marka_kayip, use_container_width=True)
                    
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
                        data=result_final.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sevkiyat_sonuclari.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Excel İndir",
                        data=result_final.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sevkiyat_sonuclari.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col3:
                    st.download_button(
                        label="📥 JSON İndir",
                        data=result_final.to_json(orient='records', force_ascii=False),
                        file_name="sevkiyat_sonuclari.json",
                        mime="application/json"
                    )


            # 🛒 ALIM SİPARİŞ HAZIRLA - DÜZELTİLMİŞ VERSİYON
            # ============================================
# 🛒 ALIM SİPARİŞ HAZIRLA - DÜZELTİLMİŞ VERSİYON
# ============================================
elif menu == "💵 Alım Sipariş":
    st.title("🛒 Alım Sipariş Hazırlama")
    st.markdown("---")
    
    # Veri kontrolü
    required_data = {
        "Ürün Master": st.session_state.urun_master,
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "Sevkiyat Sonucu": st.session_state.sevkiyat_sonuc,
        "KPI": st.session_state.kpi
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.warning("⚠️ Alım sipariş hesaplaması için gerekli veriler eksik!")
        st.error(f"**Eksik veriler:** {', '.join(missing_data)}")
        
        if "Sevkiyat Sonucu" in missing_data:
            st.markdown("---")
            st.error("🚨 **ÖNEMLİ:** Alım sipariş hesaplaması için **önce sevkiyat hesaplaması yapılmalıdır!**")
            st.info("""
            **Neden?**
            
            Alım sipariş mantığı şu şekilde çalışır:
            
            1. **Hesaplama** menüsünden sevkiyat hesaplanır
            2. İhtiyaçlar belirlenir ve depodan karşılanır
            3. **Kalan İhtiyaç** = Toplam İhtiyaç - Gerçekleşen Sevkiyat
            4. **Alım Sipariş** = Kalan İhtiyaç - Depo Stok
            """)
        st.stop()
    
    # Hesaplama butonu
    if st.button("🚀 Alım Sipariş Hesapla", type="primary", use_container_width=True):
        with st.spinner("📊 Karşılanamayan ihtiyaçlar hesaplanıyor..."):
            
            # Verileri hazırla
            anlik_df = st.session_state.anlik_stok_satis.copy()
            sevkiyat_df = st.session_state.sevkiyat_sonuc.copy()
            depo_df = st.session_state.depo_stok.copy()
            urun_master = st.session_state.urun_master.copy()
            kpi_df = st.session_state.kpi.copy()
            
            # Veri tiplerini düzelt
            anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
            sevkiyat_df['urun_kod'] = sevkiyat_df['urun_kod'].astype(str)
            depo_df['urun_kod'] = depo_df['urun_kod'].astype(str).apply(
                lambda x: str(int(float(x))) if '.' in str(x) else str(x)
            )
            urun_master['urun_kod'] = urun_master['urun_kod'].astype(str).apply(
                lambda x: str(int(float(x))) if '.' in str(x) else str(x)
            )
            
            # 1. TÜM ÜRÜNLER İÇİN İHTİYAÇ HESAPLA
            st.info("📦 **Adım 1:** Tüm ürünler için ihtiyaç hesaplanıyor...")
            
            # Ürün bazında toplam stok/satış
            urun_ihtiyac = anlik_df.groupby('urun_kod').agg({
                'stok': 'sum',
                'yol': 'sum',
                'satis': 'sum'
            }).reset_index()
            
            # KPI'dan forward cover al
            if 'mg' in urun_master.columns:
                urun_master['mg'] = urun_master['mg'].fillna(0).astype(float).astype(int).astype(str)
                urun_ihtiyac = urun_ihtiyac.merge(urun_master[['urun_kod', 'mg']], on='urun_kod', how='left')
                
                kpi_data = kpi_df[['mg_id', 'forward_cover']].rename(columns={'mg_id': 'mg'})
                kpi_data['mg'] = kpi_data['mg'].astype(str)
                urun_ihtiyac['mg'] = urun_ihtiyac['mg'].astype(str)
                urun_ihtiyac = urun_ihtiyac.merge(kpi_data, on='mg', how='left')
            
            default_fc = kpi_df['forward_cover'].mean() if len(kpi_df) > 0 else 2.0
            urun_ihtiyac['forward_cover'] = urun_ihtiyac.get('forward_cover', default_fc).fillna(default_fc)
            
            # Toplam ihtiyaç hesapla
            urun_ihtiyac['toplam_ihtiyac'] = (
                urun_ihtiyac['forward_cover'] * urun_ihtiyac['satis']
            ).clip(lower=0)
            
            # 2. GERÇEKLEŞEN SEVKİYATI EKLE
            st.info("📦 **Adım 2:** Gerçekleşen sevkiyatlar birleştiriliyor...")
            
            gerceklesen_sevkiyat = sevkiyat_df.groupby('urun_kod').agg({
                'sevkiyat_miktari': 'sum'
            }).reset_index()
            gerceklesen_sevkiyat.columns = ['urun_kod', 'gerceklesen_sevkiyat']
            
            urun_ihtiyac = urun_ihtiyac.merge(gerceklesen_sevkiyat, on='urun_kod', how='left')
            urun_ihtiyac['gerceklesen_sevkiyat'] = urun_ihtiyac['gerceklesen_sevkiyat'].fillna(0)
            
            # 3. KALAN İHTİYAÇ HESAPLA
            urun_ihtiyac['kalan_ihtiyac'] = (
                urun_ihtiyac['toplam_ihtiyac'] - 
                (urun_ihtiyac['stok'] + urun_ihtiyac['yol'] + urun_ihtiyac['gerceklesen_sevkiyat'])
            ).clip(lower=0)
            
            # 4. DEPO STOĞU EKLE - HATA DÜZELTME BURADA
            st.info("📦 **Adım 3:** Depo stok durumu kontrol ediliyor...")
            
            depo_stok_toplam = depo_df.groupby('urun_kod')['stok'].sum().reset_index()
            depo_stok_toplam.columns = ['urun_kod', 'depo_stok']
            
            # Merge işlemini düzgün yap
            urun_ihtiyac = urun_ihtiyac.merge(depo_stok_toplam, on='urun_kod', how='left')
            urun_ihtiyac['depo_stok'] = urun_ihtiyac['depo_stok'].fillna(0)
            
            # 5. ALIM SİPARİŞ HESAPLA
            urun_ihtiyac['alim_siparis_miktari'] = (
                urun_ihtiyac['kalan_ihtiyac'] - urun_ihtiyac['depo_stok']
            ).clip(lower=0)
            
            # 6. FİLTRELE: Sadece kalan ihtiyacı > 0 olanlar
            urun_ihtiyac_filtered = urun_ihtiyac[urun_ihtiyac['kalan_ihtiyac'] > 0].copy()
            
            # 7. ÜRÜN DETAYLARINI EKLE
            available_cols = ['urun_kod']
            for col in ['urun_ad', 'marka_ad', 'mg_ad']:
                if col in urun_master.columns:
                    available_cols.append(col)

            urun_ihtiyac_filtered = urun_ihtiyac_filtered.merge(
                urun_master[available_cols], 
                on='urun_kod', 
                how='left'
            )

            if 'urun_ad' not in urun_ihtiyac_filtered.columns:
                urun_ihtiyac_filtered['urun_ad'] = "Ürün " + urun_ihtiyac_filtered['urun_kod']

            # 8. DEBUG BİLGİLERİ
            st.markdown("---")
            st.write("🔍 **Debug Bilgileri:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ürün Sayısı", len(urun_ihtiyac_filtered))
            with col2:
                toplam_kalan = urun_ihtiyac_filtered['kalan_ihtiyac'].sum()
                st.metric("Toplam Kalan İhtiyaç", f"{toplam_kalan:,.0f}")
            with col3:
                toplam_depo = urun_ihtiyac_filtered['depo_stok'].sum()
                st.metric("Toplam Depo Stok", f"{toplam_depo:,.0f}")
            with col4:
                toplam_alim = urun_ihtiyac_filtered['alim_siparis_miktari'].sum()
                st.metric("Toplam Alım Sipariş", f"{toplam_alim:,.0f}")
            
            # DEVAM EDEN KOD... (kalan kısım aynı)
            
           
            
            # ✅ DEPO DURUMU ANALİZİ
            depo_yeter = urun_ihtiyac_filtered[urun_ihtiyac_filtered['depo_stok'] >= urun_ihtiyac_filtered['kalan_ihtiyac']]
            depo_yetmez = urun_ihtiyac_filtered[
                (urun_ihtiyac_filtered['depo_stok'] > 0) & 
                (urun_ihtiyac_filtered['depo_stok'] < urun_ihtiyac_filtered['kalan_ihtiyac'])
            ]
            depo_yok = urun_ihtiyac_filtered[urun_ihtiyac_filtered['depo_stok'] == 0]
            alim_gereken = urun_ihtiyac_filtered[urun_ihtiyac_filtered['alim_siparis_miktari'] > 0]
            
            st.write("📊 **Depo Durumu Analizi:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🟢 Depo Yeterli", len(depo_yeter))
                if len(depo_yeter) > 0:
                    st.caption(f"({depo_yeter['kalan_ihtiyac'].sum():,.0f} adet)")
            with col2:
                st.metric("🟡 Depo Kısmi", len(depo_yetmez))
                if len(depo_yetmez) > 0:
                    st.caption(f"Alım: {depo_yetmez['alim_siparis_miktari'].sum():,.0f}")
            with col3:
                st.metric("🔴 Depo Yok", len(depo_yok))
                if len(depo_yok) > 0:
                    st.caption(f"Alım: {depo_yok['alim_siparis_miktari'].sum():,.0f}")
            with col4:
                st.metric("✅ Alım Gerekli", len(alim_gereken))
                st.caption(f"Toplam: {alim_gereken['alim_siparis_miktari'].sum():,.0f}")
            
            st.markdown("---")
            
            # ✅ MANTIK KONTROLÜ
            if len(depo_yok) == 0 and len(alim_gereken) > 0:
                st.warning("⚠️ **Dikkat:** Depo yok ürün yok ama alım sipariş var!")
                st.info("Bu durumda tüm alım siparişler 'Depo Kısmi' kategorisinden geliyor (depoda kısmi stok var).")
            
            if len(alim_gereken) == 0:
                st.success("✅ Tüm karşılanamayan ihtiyaçlar depo stoğundan karşılanabilir!")
                st.info("ℹ️ Alım sipariş verilmesine gerek yok.")
                
                # Detaylı tablo
                st.markdown("---")
                st.subheader("📋 Depo Durumu Detayı")
                
                detay_tablo = urun_ihtiyac_filtered.copy()
                detay_tablo['durum'] = detay_tablo.apply(
                    lambda x: '🟢 Depo Yeterli' if x['depo_stok'] >= x['kalan_ihtiyac'] 
                    else '🔴 Depo Yok' if x['depo_stok'] == 0
                    else '🟡 Depo Kısmi',
                    axis=1
                )
                
                display_cols = ['urun_kod', 'urun_ad']
                if 'marka_ad' in detay_tablo.columns:
                    display_cols.append('marka_ad')
                display_cols.extend(['toplam_ihtiyac', 'gerceklesen_sevkiyat', 'kalan_ihtiyac', 'depo_stok', 'alim_siparis_miktari', 'durum'])
                
                st.dataframe(
                    detay_tablo[display_cols].style.format({
                        'toplam_ihtiyac': '{:,.0f}',
                        'gerceklesen_sevkiyat': '{:,.0f}',
                        'kalan_ihtiyac': '{:,.0f}',
                        'depo_stok': '{:,.0f}',
                        'alim_siparis_miktari': '{:,.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                st.download_button(
                    label="📥 Depo Durum Raporu İndir",
                    data=detay_tablo.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="depo_durum_raporu.csv",
                    mime="text/csv"
                )
                
                st.stop()
            
            # Alım sipariş var - devam et
            alim_siparis_df = alim_gereken.copy()
            
            st.success("✅ Alım sipariş hesaplaması tamamlandı!")
            st.balloons()
            
            # Cover hesapla
            alim_siparis_df['alim_cover'] = (
                alim_siparis_df['alim_siparis_miktari'] / 
                alim_siparis_df['satis'].replace(0, 1)
            ).round(1)
            
            # Öncelik kategorisi
            def kategorize_alim(row):
                miktar = row['alim_siparis_miktari']
                if miktar > 5000:
                    return '🔴 Kritik (>5000)'
                elif miktar > 1000:
                    return '🟡 Yüksek (>1000)'
                else:
                    return '🟢 Normal'
            
            alim_siparis_df['oncelik'] = alim_siparis_df.apply(kategorize_alim, axis=1)
            
            # Sırala
            alim_siparis_df = alim_siparis_df.sort_values('alim_siparis_miktari', ascending=False).reset_index(drop=True)
            alim_siparis_df.insert(0, 'sira_no', range(1, len(alim_siparis_df) + 1))
            
            # Kolonları düzenle
            final_cols = ['sira_no', 'urun_kod', 'urun_ad']
            if 'marka_ad' in alim_siparis_df.columns:
                final_cols.append('marka_ad')
            if 'mg_ad' in alim_siparis_df.columns:
                final_cols.append('mg_ad')
            
            final_cols.extend([
                'oncelik', 'alim_siparis_miktari', 'kalan_ihtiyac', 'depo_stok',
                'toplam_ihtiyac', 'gerceklesen_sevkiyat', 'satis', 'alim_cover'
            ])
            
            alim_final = alim_siparis_df[final_cols].copy()
            
            # Kolon isimlerini düzenle
            col_rename = {
                'sira_no': 'Sıra',
                'urun_kod': 'Ürün Kodu',
                'urun_ad': 'Ürün Adı',
                'oncelik': 'Öncelik',
                'alim_siparis_miktari': 'Alım Sipariş',
                'kalan_ihtiyac': 'Kalan İhtiyaç',
                'depo_stok': 'Depo Stok',
                'toplam_ihtiyac': 'Toplam İhtiyaç',
                'gerceklesen_sevkiyat': 'Gerçekleşen Sevkiyat',
                'satis': 'Toplam Satış',
                'alim_cover': 'Alım Cover'
            }
            
            if 'marka_ad' in alim_final.columns:
                col_rename['marka_ad'] = 'Marka'
            if 'mg_ad' in alim_final.columns:
                col_rename['mg_ad'] = 'Mal Grubu'
            
            alim_final = alim_final.rename(columns=col_rename)
            
            # SONUÇLAR
            st.markdown("---")
            st.subheader("📊 Alım Sipariş Özeti")
            
            # Metrikler
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            kritik_df = alim_final[alim_final['Öncelik'] == '🔴 Kritik (>5000)']
            yuksek_df = alim_final[alim_final['Öncelik'] == '🟡 Yüksek (>1000)']
            normal_df = alim_final[alim_final['Öncelik'] == '🟢 Normal']
            
            with col1:
                st.metric("📦 Toplam Ürün", len(alim_final))
            with col2:
                st.metric("🔴 Kritik", len(kritik_df))
            with col3:
                st.metric("🟡 Yüksek", len(yuksek_df))
            with col4:
                st.metric("🟢 Normal", len(normal_df))
            with col5:
                toplam_alim = alim_final['Alım Sipariş'].sum()
                if toplam_alim >= 1000000:
                    st.metric("💰 Toplam", f"{toplam_alim/1000000:.1f}M")
                elif toplam_alim >= 1000:
                    st.metric("💰 Toplam", f"{toplam_alim/1000:.0f}K")
                else:
                    st.metric("💰 Toplam", f"{toplam_alim:.0f}")
            with col6:
                karsilama_orani = (alim_final['Gerçekleşen Sevkiyat'].sum() / alim_final['Toplam İhtiyaç'].sum() * 100) if alim_final['Toplam İhtiyaç'].sum() > 0 else 0
                st.metric("✅ Karşılama", f"{karsilama_orani:.1f}%")
            
            st.markdown("---")
            
            # Açıklama
            st.info("""
            **💡 Alım Sipariş Mantığı:**
            - **Toplam İhtiyaç** = Forward Cover × Satış
            - **Kalan İhtiyaç** = Toplam İhtiyaç - (Stok + Yol + Sevkiyat)
            - **Alım Sipariş** = MAX(0, Kalan İhtiyaç - Depo Stok)
            
            **Öncelik Seviyeleri:**
            - **🔴 Kritik**: 5000'den fazla alım gereken
            - **🟡 Yüksek**: 1000-5000 arası alım gereken
            - **🟢 Normal**: 1000'den az alım gereken
            """)
            
            st.markdown("---")
            
            # Tablo
            st.subheader("📋 Alım Sipariş Listesi")
            
            oncelik_filtre = st.multiselect(
                "Önceliğe Göre Filtrele",
                options=['🔴 Kritik (>5000)', '🟡 Yüksek (>1000)', '🟢 Normal'],
                default=['🔴 Kritik (>5000)', '🟡 Yüksek (>1000)']
            )
            
            filtered_alim = alim_final[alim_final['Öncelik'].isin(oncelik_filtre)]
            
            st.write(f"**Gösterilen: {len(filtered_alim)} / {len(alim_final)} ürün**")
            st.dataframe(
                filtered_alim.style.format({
                    'Alım Sipariş': '{:,.0f}',
                    'Kalan İhtiyaç': '{:,.0f}',
                    'Depo Stok': '{:,.0f}',
                    'Toplam İhtiyaç': '{:,.0f}',
                    'Gerçekleşen Sevkiyat': '{:,.0f}',
                    'Toplam Satış': '{:,.0f}',
                    'Alım Cover': '{:.1f}'
                }),
                use_container_width=True,
                height=400
            )
            
            st.markdown("---")
            
            # Detaylı Analiz
            st.subheader("📈 Detaylı Analiz")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "🔴 Kritik Öncelik",
                "🟡 Yüksek Öncelik",
                "🟢 Normal Öncelik",
                "📊 Depo Durumu"
            ])
            
            with tab1:
                st.write(f"**{len(kritik_df)} ürün kritik öncelikli (>5000)**")
                if len(kritik_df) > 0:
                    st.warning("⚠️ Bu ürünler için acil tedarik gerekiyor!")
                    display_cols_kritik = ['Ürün Adı']
                    if 'Marka' in kritik_df.columns:
                        display_cols_kritik.append('Marka')
                    display_cols_kritik.extend(['Alım Sipariş', 'Kalan İhtiyaç', 'Depo Stok', 'Alım Cover'])
                    
                    st.dataframe(
                        kritik_df[display_cols_kritik].style.format({
                            'Alım Sipariş': '{:,.0f}',
                            'Kalan İhtiyaç': '{:,.0f}',
                            'Depo Stok': '{:,.0f}',
                            'Alım Cover': '{:.1f}'
                        }),
                        use_container_width=True
                    )
                else:
                    st.success("✅ Kritik öncelikli ürün yok")
            
            with tab2:
                st.write(f"**{len(yuksek_df)} ürün yüksek öncelikli (1000-5000)**")
                if len(yuksek_df) > 0:
                    display_cols_yuksek = ['Ürün Adı']
                    if 'Marka' in yuksek_df.columns:
                        display_cols_yuksek.append('Marka')
                    display_cols_yuksek.extend(['Alım Sipariş', 'Kalan İhtiyaç', 'Depo Stok', 'Alım Cover'])
                    
                    st.dataframe(
                        yuksek_df[display_cols_yuksek].style.format({
                            'Alım Sipariş': '{:,.0f}',
                            'Kalan İhtiyaç': '{:,.0f}',
                            'Depo Stok': '{:,.0f}',
                            'Alım Cover': '{:.1f}'
                        }),
                        use_container_width=True
                    )
            
            with tab3:
                st.write(f"**{len(normal_df)} ürün normal öncelikli (<1000)**")
                if len(normal_df) > 0:
                    display_cols_normal = ['Ürün Adı']
                    if 'Marka' in normal_df.columns:
                        display_cols_normal.append('Marka')
                    display_cols_normal.extend(['Alım Sipariş', 'Kalan İhtiyaç', 'Depo Stok', 'Alım Cover'])
                    
                    st.dataframe(
                        normal_df[display_cols_normal].style.format({
                            'Alım Sipariş': '{:,.0f}',
                            'Kalan İhtiyaç': '{:,.0f}',
                            'Depo Stok': '{:,.0f}',
                            'Alım Cover': '{:.1f}'
                        }),
                        use_container_width=True
                    )
            
            with tab4:
                st.write("**Tüm Ürünler - Depo Durumu**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🟢 Depo Yeterli**")
                    st.write(f"{len(depo_yeter)} ürün")
                    if len(depo_yeter) > 0:
                        st.write(f"Toplam: {depo_yeter['kalan_ihtiyac'].sum():,.0f}")
                
                with col2:
                    st.markdown("**🟡 Depo Kısmi**")
                    st.write(f"{len(depo_yetmez)} ürün")
                    if len(depo_yetmez) > 0:
                        st.write(f"Alım Gerek: {depo_yetmez['alim_siparis_miktari'].sum():,.0f}")
                
                with col3:
                    st.markdown("**🔴 Depo Yok**")
                    st.write(f"{len(depo_yok)} ürün")
                    if len(depo_yok) > 0:
                        st.write(f"Alım Gerek: {depo_yok['alim_siparis_miktari'].sum():,.0f}")
            
            st.markdown("---")
            
            # Export
            st.subheader("📥 Alım Sipariş Listesini Dışa Aktar")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📥 Tüm Liste",
                    data=alim_final.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="alim_siparisi_tum.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                if len(kritik_df) > 0:
                    st.download_button(
                        label="📥 Sadece Kritik",
                        data=kritik_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="alim_kritik.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col3:
                yuksek_kritik = alim_final[alim_final['Öncelik'].isin(['🔴 Kritik (>5000)', '🟡 Yüksek (>1000)'])]
                if len(yuksek_kritik) > 0:
                    st.download_button(
                        label="📥 Kritik + Yüksek",
                        data=yuksek_kritik.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="alim_oncelikli.csv",
                        mime="text/csv",
                        use_container_width=True
                    )



# ============================================
# 📈 RAPORLAR
# ============================================
elif menu == "📈 Raporlar":
    st.title("📈 Raporlar ve Analizler")
    st.markdown("---")
    
    if st.session_state.sevkiyat_sonuc is None:
        st.warning("⚠️ Henüz hesaplama yapılmadı!")
        st.info("Lütfen önce 'Hesaplama' menüsünden hesaplama yapın.")
    else:
        result_df = st.session_state.sevkiyat_sonuc.copy()
        
        tab1, tab2, tab3 = st.tabs([
            "📦 Ürün Analizi",
            "🏪 Mağaza Analizi",
            "⚠️ Satış Kaybı Analizi"
        ])
        
        # ============================================
        # ÜRÜN ANALİZİ
        # ============================================
        with tab1:
            st.subheader("📦 En Yüksek Sevkiyatlı 10 Ürün")
            
            if st.session_state.urun_master is not None:
                urun_detay = st.session_state.urun_master[['urun_kod', 'urun_ad', 'marka_ad', 'mg_ad']].copy()
                urun_detay['urun_kod'] = urun_detay['urun_kod'].astype(str).apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                
                result_df['urun_kod'] = result_df['urun_kod'].astype(str)
                
                urun_sevkiyat = result_df.groupby('urun_kod').agg({
                    'ihtiyac_miktari': 'sum',
                    'sevkiyat_miktari': 'sum',
                    'magaza_kod': 'nunique'
                }).reset_index()
                
                urun_sevkiyat.columns = ['urun_kod', 'İhtiyaç', 'Sevkiyat', 'Mağaza Sayısı']
                
                urun_sevkiyat['Sevkiyat/İhtiyaç %'] = (
                    (urun_sevkiyat['Sevkiyat'] / urun_sevkiyat['İhtiyaç'] * 100)
                    .fillna(0)
                    .round(2)
                )
                
                urun_sevkiyat = urun_sevkiyat.merge(urun_detay, on='urun_kod', how='left')
                
                urun_sevkiyat = urun_sevkiyat[[
                    'urun_kod', 'urun_ad', 'marka_ad', 'mg_ad', 
                    'İhtiyaç', 'Sevkiyat', 'Sevkiyat/İhtiyaç %', 'Mağaza Sayısı'
                ]]
                
                urun_sevkiyat.columns = [
                    'Ürün Kodu', 'Ürün Adı', 'Marka', 'Mal Grubu', 
                    'İhtiyaç', 'Sevkiyat', 'Sevkiyat/İhtiyaç %', 'Mağaza Sayısı'
                ]
                
                top_10_urun = urun_sevkiyat.nlargest(10, 'Sevkiyat')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Toplam Ürün", len(urun_sevkiyat))
                with col2:
                    st.metric("Top 10 Toplam İhtiyaç", f"{top_10_urun['İhtiyaç'].sum():,.0f}")
                with col3:
                    st.metric("Top 10 Toplam Sevkiyat", f"{top_10_urun['Sevkiyat'].sum():,.0f}")
                with col4:
                    ortalama_oran = top_10_urun['Sevkiyat/İhtiyaç %'].mean()
                    st.metric("Top 10 Ort. Sevk/İhtiyaç", f"{ortalama_oran:.1f}%")
                
                st.markdown("---")
                
                st.write("**En Yüksek Sevkiyatlı 10 Ürün:**")
                st.dataframe(
                    top_10_urun.style.format({
                        'İhtiyaç': '{:,.0f}',
                        'Sevkiyat': '{:,.0f}',
                        'Sevkiyat/İhtiyaç %': '{:.2f}%',
                        'Mağaza Sayısı': '{:.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                st.markdown("---")
                
                st.write("**Top 10 Ürün - Sevkiyat Miktarı:**")
                grafik_df = top_10_urun.set_index('Ürün Adı')[['Sevkiyat']]
                st.bar_chart(grafik_df)
                
                st.markdown("---")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.download_button(
                        label="📥 Top 10 İndir (CSV)",
                        data=top_10_urun.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="top_10_urun_analizi.csv",
                        mime="text/csv"
                    )
                with col2:
                    st.download_button(
                        label="📥 Tüm Ürünler İndir (CSV)",
                        data=urun_sevkiyat.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="tum_urun_analizi.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("⚠️ Ürün Master yüklenmediği için ürün analizi yapılamıyor.")
        
        # ============================================
        # MAĞAZA ANALİZİ
        # ============================================
        with tab2:
            st.subheader("🏪 Mağaza Bazında Analiz")
            
            magaza_ozet = result_df.groupby(['magaza_kod', 'magaza_ad']).agg({
                'ihtiyac_miktari': 'sum',
                'sevkiyat_miktari': 'sum',
                'stok_yoklugu_satis_kaybi': 'sum',
                'urun_kod': 'nunique'
            }).reset_index()
            
            magaza_ozet.columns = ['Mağaza Kod', 'Mağaza Adı', 'Toplam İhtiyaç', 
                                   'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']
            
            magaza_ozet['Gerçekleşme %'] = (
                magaza_ozet['Toplam Sevkiyat'] / magaza_ozet['Toplam İhtiyaç'] * 100
            ).round(2)
            
            magaza_ozet = magaza_ozet.sort_values('Toplam İhtiyaç', ascending=False)
            
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
            
            st.dataframe(magaza_ozet, use_container_width=True, height=400)
            
            st.download_button(
                label="📥 Mağaza Analizi İndir (CSV)",
                data=magaza_ozet.to_csv(index=False, encoding='utf-8-sig'),
                file_name="magaza_analizi.csv",
                mime="text/csv"
            )
        
        # ============================================
        # SATIŞ KAYBI ANALİZİ
        # ============================================
        with tab3:
            st.subheader("⚠️ Stok Yokluğu Kaynaklı Satış Kaybı Analizi")
            
            kayip_df = result_df[result_df['stok_yoklugu_satis_kaybi'] > 0].copy()
            
            if len(kayip_df) > 0:
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
                
                st.write("**En Fazla Kayıp Olan 20 Satır:**")
                top_kayip = kayip_df.nlargest(20, 'stok_yoklugu_satis_kaybi')[[
                    'magaza_ad', 'urun_ad', 'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi'
                ]]
                st.dataframe(top_kayip, use_container_width=True)
                
                st.markdown("---")
                
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
                
                st.download_button(
                    label="📥 Detaylı Satış Kaybı Raporu İndir (CSV)",
                    data=kayip_df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="satis_kaybi_detay.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ Hiç stok yokluğu kaynaklı satış kaybı yok!")
# ============================================
# 💾 MASTER DATA OLUŞTURMA
# ============================================
elif menu == "💾 Master Data":
    st.title("💾 Master Data Oluşturma")
    st.markdown("---")
    
    st.info("""
    **Master Data Nedir?**
    
    Anlık Stok/Satış CSV'sine aşağıdaki kolonları ekleyerek tek bir master dosya oluşturur:
    - **ihtiyac:** Hesaplanan sevkiyat ihtiyacı
    - **sevkiyat:** Gerçekleşen sevkiyat miktarı
    - **tip:** Sevkiyat tipi (RPT, Initial, Min)
    - **alim_ihtiyaci:** Tedarikçiden alınması gereken miktar
    - **depo_stok:** İlgili depodaki ürün stoku
    - **oncelik:** Sevkiyat öncelik sırası
    
    Bu dosya ile tüm verilerinizi tek CSV'de tutabilirsiniz.
    """)
    
    st.markdown("---")
    
    # Veri kontrolü
    if st.session_state.anlik_stok_satis is None:
        st.error("❌ Anlık Stok/Satış verisi yüklenmemiş!")
        st.info("Lütfen önce 'Veri Yükleme' bölümünden Anlık Stok/Satış CSV'sini yükleyin.")
    else:
        # Hesaplama ve Alım Sipariş durumunu kontrol et
        hesaplama_yapildi = st.session_state.sevkiyat_sonuc is not None
        
        col1, col2 = st.columns(2)
        with col1:
            if hesaplama_yapildi:
                st.success("✅ Sevkiyat hesaplaması yapılmış")
            else:
                st.warning("⚠️ Sevkiyat hesaplaması yapılmamış")
        
        with col2:
            if st.session_state.depo_stok is not None:
                st.success("✅ Depo stok verisi mevcut")
            else:
                st.warning("⚠️ Depo stok verisi yok")
        
        st.markdown("---")
        
        if st.button("🚀 Master Data Oluştur", type="primary", use_container_width=True):
            with st.spinner("📊 Master data hazırlanıyor..."):
                
                # Base data
                master_df = st.session_state.anlik_stok_satis.copy()
                
                # Veri tiplerini düzelt
                master_df['urun_kod'] = master_df['urun_kod'].astype(str)
                master_df['magaza_kod'] = master_df['magaza_kod'].astype(str)
                
                # Yeni kolonları başlat
                master_df['ihtiyac'] = 0
                master_df['sevkiyat'] = 0
                master_df['tip'] = ''
                master_df['oncelik'] = 0
                master_df['alim_ihtiyaci'] = 0
                master_df['depo_stok'] = 0
                
                # 1. SEVKIYAT VERİLERİNİ EKLE
                if hesaplama_yapildi:
                    sevkiyat_df = st.session_state.sevkiyat_sonuc.copy()
                    sevkiyat_df['urun_kod'] = sevkiyat_df['urun_kod'].astype(str)
                    sevkiyat_df['magaza_kod'] = sevkiyat_df['magaza_kod'].astype(str)
                    
                    # Sevkiyat verilerini merge et
                    master_df = master_df.merge(
                        sevkiyat_df[['magaza_kod', 'urun_kod', 'ihtiyac_miktari', 'sevkiyat_miktari', 'durum', 'oncelik']],
                        on=['magaza_kod', 'urun_kod'],
                        how='left',
                        suffixes=('', '_sevk')
                    )
                    
                    # Kolonları güncelle
                    master_df['ihtiyac'] = master_df['ihtiyac_miktari'].fillna(0)
                    master_df['sevkiyat'] = master_df['sevkiyat_miktari'].fillna(0)
                    master_df['tip'] = master_df['durum'].fillna('')
                    master_df['oncelik'] = master_df['oncelik'].fillna(0)
                    
                    # Gereksiz kolonları sil
                    master_df = master_df.drop(['ihtiyac_miktari', 'sevkiyat_miktari', 'durum'], axis=1, errors='ignore')
                
                # 2. DEPO STOK VERİSİNİ EKLE
                if st.session_state.depo_stok is not None:
                    depo_df = st.session_state.depo_stok.copy()
                    depo_df['urun_kod'] = depo_df['urun_kod'].astype(str).apply(
                        lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                    )
                    
                    # Ürün bazında toplam depo stok
                    depo_toplam = depo_df.groupby('urun_kod')['stok'].sum().reset_index()
                    depo_toplam.columns = ['urun_kod', 'depo_stok_toplam']
                    
                    master_df = master_df.merge(depo_toplam, on='urun_kod', how='left')
                    master_df['depo_stok'] = master_df['depo_stok_toplam'].fillna(0)
                    master_df = master_df.drop('depo_stok_toplam', axis=1, errors='ignore')
                
                # 3. ALIM İHTİYACI HESAPLA (Ürün bazında)
                # Ürün bazında toplamlar
                urun_toplam = master_df.groupby('urun_kod').agg({
                    'stok': 'sum',
                    'yol': 'sum',
                    'satis': 'sum',
                    'ihtiyac': 'sum',
                    'depo_stok': 'first'  # Her satırda aynı olacak
                }).reset_index()
                
                # Alım ihtiyacı formülü: İhtiyaç + (2×Satış) - (Stok+Yol+Depo)
                urun_toplam['alim_ihtiyaci_hesap'] = (
                    urun_toplam['ihtiyac'] + 
                    (2 * urun_toplam['satis']) - 
                    (urun_toplam['stok'] + urun_toplam['yol'] + urun_toplam['depo_stok'])
                ).clip(lower=0)  # Negatif değerleri 0 yap
                
                # Master'a merge et
                master_df = master_df.merge(
                    urun_toplam[['urun_kod', 'alim_ihtiyaci_hesap']],
                    on='urun_kod',
                    how='left'
                )
                master_df['alim_ihtiyaci'] = master_df['alim_ihtiyaci_hesap'].fillna(0)
                master_df = master_df.drop('alim_ihtiyaci_hesap', axis=1, errors='ignore')
                
                # Kolonları yeniden düzenle (orijinal sıra + yeni kolonlar)
                original_cols = [col for col in st.session_state.anlik_stok_satis.columns if col in master_df.columns]
                new_cols = ['ihtiyac', 'sevkiyat', 'tip', 'oncelik', 'depo_stok', 'alim_ihtiyaci']
                
                final_cols = original_cols + new_cols
                master_df = master_df[final_cols]
                
                st.success("✅ Master Data oluşturuldu!")
                st.balloons()
                
                # Sonuçlar
                st.markdown("---")
                st.subheader("📊 Master Data Özeti")
                
                # Metrikler
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Toplam Satır", f"{len(master_df):,}")
                with col2:
                    sevkiyat_var = (master_df['sevkiyat'] > 0).sum()
                    st.metric("✅ Sevkiyatlı Satır", f"{sevkiyat_var:,}")
                with col3:
                    alim_gereken = master_df.groupby('urun_kod')['alim_ihtiyaci'].first()
                    alim_var = (alim_gereken > 0).sum()
                    st.metric("🛒 Alım Gereken Ürün", f"{alim_var:,}")
                with col4:
                    if hesaplama_yapildi:
                        tip_sayisi = master_df['tip'].nunique()
                        st.metric("🎯 Sevkiyat Tipi", f"{tip_sayisi}")
                    else:
                        st.metric("🎯 Sevkiyat Tipi", "N/A")
                
                st.markdown("---")
                
                # Tip dağılımı (eğer hesaplama yapıldıysa)
                if hesaplama_yapildi:
                    st.subheader("📈 Sevkiyat Tipi Dağılımı")
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        tip_dist = master_df[master_df['tip'] != '']['tip'].value_counts()
                        st.dataframe(tip_dist, use_container_width=True)
                    
                    with col2:
                        st.bar_chart(tip_dist)
                
                st.markdown("---")
                
                # Önizleme
                st.subheader("🔍 Master Data Önizleme (İlk 20 Satır)")
                
                # Yeni kolonları vurgula
                def highlight_new_cols(s):
                    return ['background-color: #e8f4f8' if s.name in new_cols else '' for _ in s]
                
                preview_df = master_df.head(20).style.apply(highlight_new_cols, axis=0)
                st.dataframe(preview_df, use_container_width=True, height=400)
                
                st.markdown("---")
                
                # İstatistikler
                st.subheader("📊 Detaylı İstatistikler")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Sevkiyat İstatistikleri**")
                    if master_df['sevkiyat'].sum() > 0:
                        st.write(f"- Toplam Sevkiyat: {master_df['sevkiyat'].sum():,.0f}")
                        st.write(f"- Ortalama Sevkiyat: {master_df[master_df['sevkiyat']>0]['sevkiyat'].mean():,.0f}")
                        st.write(f"- Max Sevkiyat: {master_df['sevkiyat'].max():,.0f}")
                    else:
                        st.write("- Sevkiyat hesaplaması yok")
                
                with col2:
                    st.markdown("**Alım Sipariş İstatistikleri**")
                    alim_urun = master_df.groupby('urun_kod')['alim_ihtiyaci'].first()
                    if alim_urun.sum() > 0:
                        st.write(f"- Toplam Alım: {alim_urun.sum():,.0f}")
                        st.write(f"- Ortalama Alım/Ürün: {alim_urun[alim_urun>0].mean():,.0f}")
                        st.write(f"- Max Alım: {alim_urun.max():,.0f}")
                    else:
                        st.write("- Alım ihtiyacı yok")
                
                with col3:
                    st.markdown("**Genel İstatistikler**")
                    st.write(f"- Toplam Ürün: {master_df['urun_kod'].nunique():,}")
                    st.write(f"- Toplam Mağaza: {master_df['magaza_kod'].nunique():,}")
                    st.write(f"- Toplam Satış: {master_df['satis'].sum():,.0f}")
                
                st.markdown("---")
                
                # Export butonları
                st.subheader("📥 Master Data'yı Dışa Aktar")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.download_button(
                        label="📥 CSV İndir",
                        data=master_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="master_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Excel İndir",
                        data=master_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="master_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col3:
                    st.download_button(
                        label="📥 JSON İndir",
                        data=master_df.to_json(orient='records', force_ascii=False),
                        file_name="master_data.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col4:
                    # Parquet formatı için
                    import io
                    buffer = io.BytesIO()
                    master_df.to_parquet(buffer, index=False)
                    st.download_button(
                        label="📥 Parquet İndir",
                        data=buffer.getvalue(),
                        file_name="master_data.parquet",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                
                st.markdown("---")
                
                # Filtreleme ve arama
                st.subheader("🔎 Master Data'da Arama ve Filtreleme")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtre_tip = st.multiselect(
                        "Sevkiyat Tipine Göre Filtrele",
                        options=['RPT', 'Initial', 'Min'],
                        default=[]
                    )
                
                with col2:
                    filtre_magaza = st.text_input("Mağaza Kodu Ara", "")
                
                with col3:
                    filtre_urun = st.text_input("Ürün Kodu Ara", "")
                
                # Filtreleri uygula
                filtered_df = master_df.copy()
                
                if filtre_tip:
                    filtered_df = filtered_df[filtered_df['tip'].isin(filtre_tip)]
                
                if filtre_magaza:
                    filtered_df = filtered_df[filtered_df['magaza_kod'].str.contains(filtre_magaza, case=False, na=False)]
                
                if filtre_urun:
                    filtered_df = filtered_df[filtered_df['urun_kod'].str.contains(filtre_urun, case=False, na=False)]
                
                if len(filtered_df) > 0:
                    st.write(f"**Filtre Sonucu:** {len(filtered_df)} satır bulundu")
                    st.dataframe(filtered_df, use_container_width=True, height=300)
                    
                    # Filtrelenmiş veriyi indir
                    st.download_button(
                        label="📥 Filtrelenmiş Veriyi İndir (CSV)",
                        data=filtered_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="master_data_filtered.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ Filtre kriterlerine uyan kayıt bulunamadı.")

