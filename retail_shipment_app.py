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
# 📤 VERİ YÜKLEME - YENİ TASARIM
# ============================================
elif menu == "📤 Veri Yükleme":
    st.title("📤 Veri Yükleme")
    st.markdown("---")
    
    # Örnek CSV'ler indirme bölümü
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
                'klasman_kod': ['K1', 'K2', 'K1'],
                'klasman_ad': ['Klasman A', 'Klasman B', 'Klasman A'],
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
                'magaza_kod': ['M002', 'M001'],
                'yasak_durum': [1, 1]
            }),
            'depo_stok.csv': pd.DataFrame({
                'depo_kod': ['D001', 'D001', 'D002'],
                'depo_ad': ['Depo Merkez', 'Depo Merkez', 'Depo Bölge'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'stok': [1000, 1500, 800]
            }),
            'anlik_stok_satis.csv': pd.DataFrame({
                'magaza_kod': ['M001', 'M001', 'M002'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'stok': [100, 150, 120],
                'yol': [20, 30, 25],
                'satis': [50, 40, 45],
                'ciro': [5000, 6000, 5500],
                'smm': [2.0, 3.75, 2.67]
            }),
            'haftalik_trend.csv': pd.DataFrame({
                'klasman_kod': ['K1', 'K1', 'K2'],
                'marka_kod': ['M001', 'M001', 'M002'],
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
    
    # Veri tanımları
    data_definitions = {
        'urun_master': {
            'name': 'Ürün Master',
            'required': True,
            'columns': ['urun_kod', 'urun_ad', 'satici_kod', 'satici_ad', 'kategori_kod', 'kategori_ad', 
                       'umg', 'umg_ad', 'mg', 'mg_ad', 'marka_kod', 'marka_ad', 'klasman_kod', 'klasman_ad',
                       'nitelik', 'durum', 'ithal', 'ithal_ad', 'tanim'],
            'state_key': 'urun_master',
            'icon': '📦'
        },
        'magaza_master': {
            'name': 'Mağaza Master',
            'required': True,
            'columns': ['magaza_kod', 'magaza_ad', 'il', 'bolge', 'tip', 'adres_kod', 'sm', 'bs', 'depo_kod'],
            'state_key': 'magaza_master',
            'icon': '🏪'
        },
        'depo_stok': {
            'name': 'Depo Stok',
            'required': True,
            'columns': ['depo_kod', 'depo_ad', 'urun_kod', 'stok'],
            'state_key': 'depo_stok',
            'icon': '📦'
        },
        'anlik_stok_satis': {
            'name': 'Anlık Stok/Satış',
            'required': True,
            'columns': ['magaza_kod', 'urun_kod', 'stok', 'yol', 'satis', 'ciro', 'smm'],
            'state_key': 'anlik_stok_satis',
            'icon': '📊'
        },
        'kpi': {
            'name': 'KPI',
            'required': True,
            'columns': ['mg_id', 'min_deger', 'max_deger', 'forward_cover'],
            'state_key': 'kpi',
            'icon': '🎯'
        },
        'yasak_master': {
            'name': 'Yasak',
            'required': False,
            'columns': ['urun_kod', 'magaza_kod', 'yasak_durum'],
            'state_key': 'yasak_master',
            'icon': '🚫'
        },
        'haftalik_trend': {
            'name': 'Haftalık Trend',
            'required': False,
            'columns': ['klasman_kod', 'marka_kod', 'yil', 'hafta', 'stok', 'satis', 'ciro', 'smm', 'iftutar'],
            'state_key': 'haftalik_trend',
            'icon': '📈'
        }
    }
    
    # ÇOKLU DOSYA YÜKLEME
    st.subheader("📤 Çoklu Dosya Yükleme")
    
    uploaded_files = st.file_uploader(
        "CSV dosyalarını seçin (birden fazla seçebilirsiniz)",
        type=['csv'],
        accept_multiple_files=True,
        key="multi_upload"
    )
    
    if uploaded_files:
        st.write(f"**{len(uploaded_files)} dosya seçildi**")
        
        if st.button("🚀 Tüm Dosyaları Yükle", type="primary", use_container_width=True):
            upload_results = []
            
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name.lower()
                
                # Dosya adından veri tipini bul
                matched_key = None
                for key, definition in data_definitions.items():
                    if key in filename or definition['name'].lower().replace(' ', '_') in filename:
                        matched_key = key
                        break
                
                if not matched_key:
                    upload_results.append({
                        'Dosya': uploaded_file.name,
                        'Veri Tipi': '❓ Bilinmiyor',
                        'Durum': '❌ Eşleştirilemedi',
                        'Detay': 'Dosya adı tanımlı veri tiplerine uymuyor'
                    })
                    continue
                
                definition = data_definitions[matched_key]
                
                try:
                    df = pd.read_csv(uploaded_file)
                    
                    # Kolon kontrolü
                    existing_cols = set(df.columns)
                    required_cols = set(definition['columns'])
                    missing_cols = required_cols - existing_cols
                    extra_cols = existing_cols - required_cols
                    
                    if missing_cols:
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Veri Tipi': f"{definition['icon']} {definition['name']}",
                            'Durum': '❌ Başarısız',
                            'Detay': f"Eksik kolonlar: {', '.join(list(missing_cols)[:3])}"
                        })
                    else:
                        # Sadece gerekli kolonları al
                        df_clean = df[definition['columns']].copy()
                        st.session_state[definition['state_key']] = df_clean
                        
                        detay = f"✅ {len(df_clean):,} satır"
                        if extra_cols:
                            detay += f" (fazla kolonlar kaldırıldı)"
                        
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Veri Tipi': f"{definition['icon']} {definition['name']}",
                            'Durum': '✅ Başarılı',
                            'Detay': detay
                        })
                
                except Exception as e:
                    upload_results.append({
                        'Dosya': uploaded_file.name,
                        'Veri Tipi': f"{definition['icon']} {definition['name']}",
                        'Durum': '❌ Hata',
                        'Detay': str(e)[:50]
                    })
            
            # Sonuçları göster
            st.markdown("---")
            st.subheader("📋 Yükleme Sonuçları")
            
            results_df = pd.DataFrame(upload_results)
            
            def highlight_upload_results(row):
                if '✅ Başarılı' in row['Durum']:
                    return ['background-color: #d4edda'] * len(row)
                elif '❌' in row['Durum']:
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return ['background-color: #fff3cd'] * len(row)
            
            st.dataframe(
                results_df.style.apply(highlight_upload_results, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            success_count = sum(1 for r in upload_results if '✅ Başarılı' in r['Durum'])
            st.success(f"✅ {success_count} / {len(upload_results)} dosya başarıyla yüklendi!")
            
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    # VERİ DURUMU TABLOSU
    st.subheader("📊 Veri Yükleme Durumu")
    
    # Durum tablosunu oluştur
    status_data = []
    for key, definition in data_definitions.items():
        data = st.session_state.get(definition['state_key'])
        
        if data is not None and len(data) > 0:
            status = '✅ Yüklü'
            row_count = len(data)
            
            # Eksik kolon kontrolü
            existing_cols = set(data.columns)
            required_cols = set(definition['columns'])
            missing_cols = required_cols - existing_cols
            
            if missing_cols:
                kolon_durumu = f"⚠️ Eksik kolon var"
            else:
                kolon_durumu = '✅ Tam'
        else:
            status = '❌ Yüklenmedi'
            row_count = 0
            kolon_durumu = '-'
        
        # Beklenen kolonları liste olarak
        expected_cols_str = ', '.join(definition['columns'][:5])
        if len(definition['columns']) > 5:
            expected_cols_str += f"... (+{len(definition['columns'])-5})"
        
        status_data.append({
            'Veri': f"{definition['icon']} {definition['name']}",
            'Zorunlu': '🔴' if definition['required'] else '🟢',
            'Durum': status,
            'Satır': f"{row_count:,}" if row_count > 0 else '-',
            'Kolon': kolon_durumu,
            'Beklenen Kolonlar': expected_cols_str
        })
    
    status_df = pd.DataFrame(status_data)
    
    # Renk kodlaması
    def highlight_status(row):
        if '✅ Yüklü' in row['Durum']:
            return ['background-color: #d4edda'] * len(row)
        elif '❌ Yüklenmedi' in row['Durum'] and '🔴' in row['Zorunlu']:
            return ['background-color: #f8d7da'] * len(row)
        else:
            return [''] * len(row)
    
    st.dataframe(
        status_df.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    # Bilgilendirme
    st.info("""
    **💡 Veri Yapısı:**
    - 🔴 Zorunlu veriler yüklenmeli | 🟢 Opsiyonel
    - **Master'lar** diğer tablolara join için kullanılır
    - Diğer CSV'lerde sadece **kod** kolonları, **ad** kolonları master'lardan gelir
    - **Yasak**: yasak_durum = 1 (yasak), 0 veya yok (yasak değil)
    """)
    
    # Özet bilgiler
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_loaded = sum(1 for _, def_data in data_definitions.items() 
                          if st.session_state.get(def_data['state_key']) is not None 
                          and len(st.session_state.get(def_data['state_key'])) > 0)
        st.metric("📂 Yüklü", f"{total_loaded}/{len(data_definitions)}")
    
    with col2:
        required_count = sum(1 for def_data in data_definitions.values() if def_data['required'])
        required_loaded = sum(1 for _, def_data in data_definitions.items() 
                             if def_data['required'] 
                             and st.session_state.get(def_data['state_key']) is not None
                             and len(st.session_state.get(def_data['state_key'])) > 0)
        st.metric("🔴 Zorunlu", f"{required_loaded}/{required_count}")
    
    with col3:
        total_rows = sum(len(st.session_state.get(def_data['state_key'])) 
                        for def_data in data_definitions.values() 
                        if st.session_state.get(def_data['state_key']) is not None)
        st.metric("📊 Toplam Satır", f"{total_rows:,}")
    
    with col4:
        if st.button("🗑️ Tümünü Sil", use_container_width=True):
            for def_data in data_definitions.values():
                st.session_state[def_data['state_key']] = None
            st.success("✅ Tüm veriler silindi!")
            time.sleep(0.5)
            st.rerun()
    
    st.markdown("---")
    
    # TEK DOSYA DETAYI
    st.subheader("🔍 Detaylı Veri İncelemesi")
    
    selected_data = st.selectbox(
        "İncelemek istediğiniz veriyi seçin:",
        options=[k for k in data_definitions.keys() if st.session_state.get(data_definitions[k]['state_key']) is not None],
        format_func=lambda x: f"{data_definitions[x]['icon']} {data_definitions[x]['name']}",
        key="detail_select"
    ) if any(st.session_state.get(data_definitions[k]['state_key']) is not None for k in data_definitions.keys()) else None
    
    if selected_data:
        current_def = data_definitions[selected_data]
        data = st.session_state[current_def['state_key']]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Satır", f"{len(data):,}")
        with col2:
            st.metric("Kolon", len(data.columns))
        with col3:
            st.metric("Bellek", f"{data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        st.write("**Beklenen Kolonlar:**")
        st.code(', '.join(current_def['columns']), language=None)
        
        st.dataframe(data.head(20), use_container_width=True, height=300)
    else:
        st.info("Henüz yüklenmiş veri yok")

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
    
    # Ürün bazında gruplama - SADECE MEVCUT KOLONLAR
    urun_aggregated = data.groupby('urun_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
    urun_aggregated['cover'] = urun_aggregated['stok_satis_orani']
    
    # Ürün adını master'dan ekle
    if st.session_state.urun_master is not None:
        urun_master = st.session_state.urun_master[['urun_kod', 'urun_ad', 'marka_ad']].copy()
        urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
        urun_aggregated['urun_kod'] = urun_aggregated['urun_kod'].astype(str)
        urun_aggregated = urun_aggregated.merge(urun_master, on='urun_kod', how='left')
    else:
        urun_aggregated['urun_ad'] = 'Bilinmiyor'
        urun_aggregated['marka_ad'] = 'Bilinmiyor'
    
    # Mağaza bazında gruplama - SADECE MEVCUT KOLONLAR
    magaza_aggregated = data.groupby('magaza_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
    magaza_aggregated['cover'] = magaza_aggregated['stok_satis_orani']
    
    # Mağaza adını master'dan ekle
    if st.session_state.magaza_master is not None:
        magaza_master = st.session_state.magaza_master[['magaza_kod', 'magaza_ad']].copy()
        magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
        magaza_aggregated['magaza_kod'] = magaza_aggregated['magaza_kod'].astype(str)
        magaza_aggregated = magaza_aggregated.merge(magaza_master, on='magaza_kod', how='left')
    else:
        magaza_aggregated['magaza_ad'] = 'Bilinmiyor'
    
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
        
        # Segmentasyon parametrelerini al
        product_ranges = st.session_state.segmentation_params['product_ranges']
        store_ranges = st.session_state.segmentation_params['store_ranges']
        
        # Ürün segmentasyonu
        product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
        urun_aggregated['urun_segment'] = pd.cut(
            urun_aggregated['stok_satis_orani'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=product_labels,
            include_lowest=True
        )
        
        # Mağaza segmentasyonu
        store_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
        magaza_aggregated['magaza_segment'] = pd.cut(
            magaza_aggregated['stok_satis_orani'],
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=store_labels,
            include_lowest=True
        )
        
        # Segment sıralama fonksiyonu
        def sort_segments(segments):
            """Segmentleri numerik değere göre sıralar: 0-4, 5-8, 9-12, 15-20, 20-inf"""
            def get_sort_key(seg):
                try:
                    # İlk sayıyı al (0-4 -> 0, 5-8 -> 5, 20-inf -> 20)
                    return int(seg.split('-')[0])
                except:
                    return 9999  # inf veya parse edilemeyen değerler en sona
            
            return sorted(segments, key=get_sort_key)
        
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
        
        # Segmentleri string olarak al ve SIRALA
        prod_segments_raw = [str(x) for x in urun_aggregated['urun_segment'].unique() if pd.notna(x)]
        store_segments_raw = [str(x) for x in magaza_aggregated['magaza_segment'].unique() if pd.notna(x)]
        
        prod_segments = sort_segments(prod_segments_raw)
        store_segments = sort_segments(store_segments_raw)
        
        st.info(f"**Ürün Segmentleri:** {', '.join(prod_segments)}")
        st.info(f"**Mağaza Segmentleri:** {', '.join(store_segments)}")
        
        # 1. ŞİŞME ORANI MATRİSİ
        st.markdown("### 1️⃣ Şişme Oranı Matrisi (Default: 0.5)")
        
        if st.session_state.sisme_orani is None or len(st.session_state.sisme_orani) == 0:
            sisme_data = pd.DataFrame(0.5, index=prod_segments, columns=store_segments)
        else:
            # Mevcut matrisi kontrol et ve eksikleri doldur
            sisme_data = st.session_state.sisme_orani.copy()
            
            # Eksik satırları ekle
            for seg in prod_segments:
                if seg not in sisme_data.index:
                    sisme_data.loc[seg] = 0.5
            
            # Eksik kolonları ekle
            for seg in store_segments:
                if seg not in sisme_data.columns:
                    sisme_data[seg] = 0.5
            
            # Sıralama - ÖNEMLİ!
            sisme_data = sisme_data.reindex(index=prod_segments, columns=store_segments, fill_value=0.5)
        
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
        
        if st.session_state.genlestirme_orani is None or len(st.session_state.genlestirme_orani) == 0:
            genlestirme_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            genlestirme_data = st.session_state.genlestirme_orani.copy()
            
            for seg in prod_segments:
                if seg not in genlestirme_data.index:
                    genlestirme_data.loc[seg] = 1.0
            
            for seg in store_segments:
                if seg not in genlestirme_data.columns:
                    genlestirme_data[seg] = 1.0
            
            # Sıralama - ÖNEMLİ!
            genlestirme_data = genlestirme_data.reindex(index=prod_segments, columns=store_segments, fill_value=1.0)
        
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
        
        if st.session_state.min_oran is None or len(st.session_state.min_oran) == 0:
            min_oran_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            min_oran_data = st.session_state.min_oran.copy()
            
            for seg in prod_segments:
                if seg not in min_oran_data.index:
                    min_oran_data.loc[seg] = 1.0
            
            for seg in store_segments:
                if seg not in min_oran_data.columns:
                    min_oran_data[seg] = 1.0
            
            # Sıralama - ÖNEMLİ!
            min_oran_data = min_oran_data.reindex(index=prod_segments, columns=store_segments, fill_value=1.0)
        
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
        
        if st.session_state.initial_matris is None or len(st.session_state.initial_matris) == 0:
            initial_data = pd.DataFrame(1.0, index=prod_segments, columns=store_segments)
        else:
            initial_data = st.session_state.initial_matris.copy()
            
            for seg in prod_segments:
                if seg not in initial_data.index:
                    initial_data.loc[seg] = 1.0
            
            for seg in store_segments:
                if seg not in initial_data.columns:
                    initial_data[seg] = 1.0
            
            # Sıralama - ÖNEMLİ!
            initial_data = initial_data.reindex(index=prod_segments, columns=store_segments, fill_value=1.0)
        
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
    
    # Session state kontrolü - önceki sonuçları koru
    if 'sevkiyat_sonuc' not in st.session_state:
        st.session_state.sevkiyat_sonuc = None
    
    # Daha önce hesaplanmış sonuç varsa göster
    if st.session_state.sevkiyat_sonuc is not None:
        st.success("✅ Daha önce hesaplanmış sevkiyat sonuçları mevcut!")
        
        # Önceki sonuçları hızlıca göster
        result_final = st.session_state.sevkiyat_sonuc.copy()
        
        # Özet metrikler
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Toplam İhtiyaç", f"{result_final['ihtiyac_miktari'].sum():,.0f}")
        with col2:
            st.metric("✅ Toplam Sevkiyat", f"{result_final['sevkiyat_miktari'].sum():,.0f}")
        with col3:
            st.metric("⚠️ Satış Kaybı", f"{result_final['stok_yoklugu_satis_kaybi'].sum():,.0f}")
        with col4:
            st.metric("🏪 Mağaza Sayısı", f"{result_final['magaza_kod'].nunique()}")
        
        st.info("Yeni hesaplama yapmak isterseniz aşağıdaki butonu kullanın.")
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
        if st.session_state.sevkiyat_sonuc is None:
            st.success("✅ Tüm zorunlu veriler hazır! Hesaplama yapabilirsiniz.")
        else:
            st.success("✅ Tüm zorunlu veriler hazır! Yeni hesaplama yapabilir veya mevcut sonuçları kullanabilirsiniz.")
        
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
                    'Oncelik', 'magaza_kod', 'urun_kod',
                    'magaza_segment', 'urun_segment', 'Durum',
                    'stok', 'yol', 'satis', 'ihtiyac', 'sevkiyat_gercek', 'depo_kod', 'stok_yoklugu_kaybi'
                ]].rename(columns={
                    'Oncelik': 'oncelik',
                    'Durum': 'durum',
                    'ihtiyac': 'ihtiyac_miktari',
                    'sevkiyat_gercek': 'sevkiyat_miktari',
                    'stok_yoklugu_kaybi': 'stok_yoklugu_satis_kaybi'
                })
                
                # Ürün ve mağaza adlarını master'lardan ekle
                if st.session_state.urun_master is not None:
                    urun_master = st.session_state.urun_master[['urun_kod', 'urun_ad']].copy()
                    urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    result_final['urun_kod'] = result_final['urun_kod'].astype(str)
                    result_final = result_final.merge(urun_master, on='urun_kod', how='left')
                else:
                    result_final['urun_ad'] = 'Bilinmiyor'
                
                if st.session_state.magaza_master is not None:
                    magaza_master = st.session_state.magaza_master[['magaza_kod', 'magaza_ad']].copy()
                    magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                    result_final['magaza_kod'] = result_final['magaza_kod'].astype(str)
                    result_final = result_final.merge(magaza_master, on='magaza_kod', how='left')
                else:
                    result_final['magaza_ad'] = 'Bilinmiyor'
                
                # Kolon sıralamasını düzenle
                result_final = result_final[[
                    'oncelik', 'magaza_kod', 'magaza_ad', 'urun_kod', 'urun_ad',
                    'magaza_segment', 'urun_segment', 'durum',
                    'stok', 'yol', 'satis', 'ihtiyac_miktari', 'sevkiyat_miktari', 'depo_kod', 'stok_yoklugu_satis_kaybi'
                ]]
                
                result_final.insert(0, 'sira_no', range(1, len(result_final) + 1))
                
                # Hesaplama süresini hesapla
                end_time = time.time()
                calculation_time = end_time - start_time
                
                progress_bar.progress(100, text="Tamamlandı!")
                
                # SONUÇLARI SESSION STATE'E KAYDET - BU ÇOK ÖNEMLİ!
                st.session_state.sevkiyat_sonuc = result_final.copy()
                
                # Hesaplama tamamlandı mesajını BURADA göster
                st.success("✅ Hesaplama tamamlandı! Sonuçlar kaydedildi.")
            
            # -------------------------------
            # CSV İNDİRME BUTONU (Hesaplama Sonrası)
            # -------------------------------
            if 'result_df' in locals() and not result_df.empty:
                try:
                    # CSV için gerekli sütunları filtrele
                    detayli_df = result_df[[
                        'urun_kod', 'magaza_kod', 'mağaza_grup', 'ürün_grup',
                        'satış', 'stok', 'yol', 'ihtiyaç', 'depo_stok'
                    ]].copy()

                    # CSV'yi bellek üzerinden indirilebilir hale getir
                    csv_bytes = detayli_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

                    st.download_button(
                        label="📥 Detaylı Sevkiyat CSV İndir",
                        data=csv_bytes,
                        file_name=f"detayli_sevkiyat_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv',
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"CSV oluşturulurken hata oluştu: {e}")
 
             

    # Sayfa yüklendiğinde sonuçları göster (yeniden hesaplama yapılmadıysa)
        # Sayfa yüklendiğinde sonuçları göster (yeniden hesaplama yapılmadıysa)
    if st.session_state.sevkiyat_sonuc is not None:
        st.markdown("---")
        st.subheader("📊 Mevcut Sevkiyat Sonuçları")
        
        result_final = st.session_state.sevkiyat_sonuc.copy()
        
        # Ana metrikler tablosu
        st.markdown("### 📈 Performans Özeti")
        
        # Ana metrikler
        toplam_ihtiyac = result_final['ihtiyac_miktari'].sum()
        toplam_sevkiyat = result_final['sevkiyat_miktari'].sum()
        toplam_kayip = result_final['stok_yoklugu_satis_kaybi'].sum()
        sku_count = result_final[result_final['sevkiyat_miktari'] > 0]['urun_kod'].nunique()
        magaza_count = result_final[result_final['sevkiyat_miktari'] > 0]['magaza_kod'].nunique()
        kayip_oran = (toplam_kayip / toplam_ihtiyac * 100) if toplam_ihtiyac > 0 else 0
        
        # Durum bazlı sevkiyatlar
        rpt_sevk = result_final[result_final['durum'] == 'RPT']['sevkiyat_miktari'].sum()
        initial_sevk = result_final[result_final['durum'] == 'Initial']['sevkiyat_miktari'].sum()
        min_sevk = result_final[result_final['durum'] == 'Min']['sevkiyat_miktari'].sum()
        
        # Tablo oluştur
        summary_data = {
            'Kategori': ['Genel', 'Genel', 'Genel', 'Genel', 'Genel', 'Genel', 'Durum', 'Durum', 'Durum'],
            'Metrik': [
                'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Stok Kaybı', 
                'SKU Sayısı', 'Mağaza Sayısı', 'Kayıp Oranı',
                'RPT Sevkiyat', 'Initial Sevkiyat', 'Min Sevkiyat'
            ],
            'Değer': [
                f"{toplam_ihtiyac:,.0f}",
                f"{toplam_sevkiyat:,.0f}",
                f"{toplam_kayip:,.0f}",
                f"{sku_count}",
                f"{magaza_count}",
                f"{kayip_oran:.1f}%",
                f"{rpt_sevk:,.0f}",
                f"{initial_sevk:,.0f}",
                f"{min_sevk:,.0f}"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        # Performans özetini göster
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # 📥 DETAYLI SEVKİYAT CSV İNDİRME BUTONU
        # ------------------------------------------
        try:
            detayli_df = result_final[[
                'urun_kod', 'magaza_kod',
                'magaza_segment', 'urun_segment',
                'satis', 'stok', 'yol',
                'ihtiyac_miktari', 'sevkiyat_miktari', 'durum'
            ]].copy()

            detayli_df = detayli_df.rename(columns={
                'magaza_segment': 'mağaza_grup',
                'urun_segment': 'ürün_grup',
                'satis': 'satış',
                'ihtiyac_miktari': 'ihtiyaç',
                'sevkiyat_miktari': 'sevk_miktari',
                'durum': 'svk_tipi'
            })

            csv_bytes = detayli_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

            st.download_button(
                label="📥 Detaylı Sevkiyat CSV İndir",
                data=csv_bytes,
                file_name=f"detayli_sevkiyat_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )
        except Exception as e:
            st.warning(f"CSV oluşturulurken hata oluştu: {e}")

        # ------------------------------------------
        # 🧾 SONUÇLARI TEMİZLE BUTONU
        # ------------------------------------------
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Sonuçları Temizle", type="secondary"):
                st.session_state.sevkiyat_sonuc = None
                st.success("✅ Sonuçlar temizlendi!")
                st.rerun()


# ============================================
# 💵 ALIM SİPARİŞ - YENİ MANTIK
# ============================================
elif menu == "💵 Alım Sipariş":
    st.title("💵 Alım Sipariş Hesaplama")
    st.markdown("---")
    
    # Veri kontrolleri
    required_data = {
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.warning(f"⚠️ Eksik veriler: {', '.join(missing_data)}")
        st.info("Lütfen önce 'Veri Yükleme' bölümünden gerekli verileri yükleyin.")
        st.stop()
    
    # Depo stok kontrolü
    if len(st.session_state.depo_stok) == 0:
        st.error("❌ Depo Stok verisi boş! Lütfen depo_stok.csv dosyasını yükleyin.")
        st.stop()
    
    st.success("✅ Tüm gerekli veriler hazır!")
    
    st.markdown("---")
    
    # Filtreler
    st.subheader("🎯 Hesaplama Filtreleri")
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        cover_threshold = st.number_input(
            "Cover < X için hesapla",
            min_value=0,
            max_value=100,
            value=12,
            step=1,
            help="Örnek: 12 girersek Cover < 12 olan ürünler hesaplanır"
        )
    
    with col2:
        margin_threshold = st.number_input(
            "Brüt Kar Marjı > % Y için hesapla",
            min_value=-100.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            help="Negatif değer girebilirsiniz. Örnek: 10 girersek Marj > %10 olanlar hesaplanır"
        )
    
    st.markdown("---")
    
    # 5. Matris - Cover Segment Katsayıları
    st.subheader("📊 5. Matris: Cover Segment Genişletme Katsayıları")
    
    
    # Segmentasyon parametrelerini al
    product_ranges = st.session_state.segmentation_params['product_ranges']
    
    # Cover segmentlerini oluştur
    cover_segments = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
    
    # Segment sıralama fonksiyonu
    def sort_segments(segments):
        def get_sort_key(seg):
            try:
                return int(seg.split('-')[0])
            except:
                return 9999
        return sorted(segments, key=get_sort_key)
    
    cover_segments_sorted = sort_segments(cover_segments)
    
    if 'cover_segment_matrix' not in st.session_state or st.session_state.cover_segment_matrix is None:
        # Default katsayı tablosu
        st.session_state.cover_segment_matrix = pd.DataFrame({
            'cover_segment': cover_segments_sorted,
            'katsayi': [1.0] * len(cover_segments_sorted)
        })
    else:
        # Mevcut matrisi güncelle - yeni segmentler eklenmişse
        existing_df = st.session_state.cover_segment_matrix.copy()
        existing_segments = set(existing_df['cover_segment'].tolist())
        
        # Yeni segmentleri ekle
        for seg in cover_segments_sorted:
            if seg not in existing_segments:
                new_row = pd.DataFrame({'cover_segment': [seg], 'katsayi': [1.0]})
                existing_df = pd.concat([existing_df, new_row], ignore_index=True)
        
        # Sadece mevcut segmentleri tut
        existing_df = existing_df[existing_df['cover_segment'].isin(cover_segments_sorted)]
        
        # Sırala
        existing_df['sort_key'] = existing_df['cover_segment'].apply(
            lambda x: int(x.split('-')[0]) if x.split('-')[0].isdigit() else 9999
        )
        existing_df = existing_df.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
        
        st.session_state.cover_segment_matrix = existing_df
    
    edited_cover_matrix = st.data_editor(
        st.session_state.cover_segment_matrix,
        use_container_width=True,
        hide_index=True,
        column_config={
            "cover_segment": st.column_config.TextColumn(
                "Cover Segment",
                disabled=True,
                width="medium"
            ),
            "katsayi": st.column_config.NumberColumn(
                "Genişletme Katsayısı",
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                format="%.2f",
                required=True,
                width="medium"
            )
        }
    )
    
    if st.button("💾 Cover Segment Matrisini Kaydet"):
        st.session_state.cover_segment_matrix = edited_cover_matrix
        st.success("✅ Kaydedildi!")
    
    st.markdown("---")
    
    if st.button("🚀 Alım Sipariş Hesapla", type="primary", use_container_width=True):
        try:
            with st.spinner("📊 Hesaplama yapılıyor..."):
                
                # 1. VERİLERİ HAZIRLA
                anlik_df = st.session_state.anlik_stok_satis.copy()
                depo_df = st.session_state.depo_stok.copy()
                kpi_df = st.session_state.kpi.copy()
                cover_matrix = st.session_state.cover_segment_matrix.copy()
                
                st.write("**📊 Debug: Veri boyutları**")
                st.write(f"- Anlık Stok/Satış: {len(anlik_df):,} satır")
                st.write(f"- Depo Stok: {len(depo_df):,} satır")
                st.write(f"- KPI: {len(kpi_df)} satır")
                st.write(f"- Cover Segment Matrix: {len(cover_matrix)} segment")
                
                # Veri tiplerini düzelt
                anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                depo_df['urun_kod'] = depo_df['urun_kod'].astype(str).apply(
                    lambda x: str(int(float(x))) if '.' in str(x) else str(x)
                )
                
                # 2. ÜRÜN BAZINDA TOPLAMA
                urun_toplam = anlik_df.groupby('urun_kod').agg({
                    'urun_kod': 'first',
                    'stok': 'sum',
                    'yol': 'sum',
                    'satis': 'sum',
                    'ciro': 'sum',
                    'smm': 'sum'
                }).reset_index(drop=True)
                
                st.write(f"**🏷️  Ürün bazında toplam:** {len(urun_toplam):,} ürün")
                
                # 3. DEPO STOK EKLE
                depo_toplam = depo_df.groupby('urun_kod')['stok'].sum().reset_index()
                depo_toplam.columns = ['urun_kod', 'depo_stok']
                
                st.write(f"**📦 Depo stok:** {len(depo_toplam):,} ürün, Toplam: {depo_toplam['depo_stok'].sum():,.0f}")
                
                urun_toplam = urun_toplam.merge(depo_toplam, on='urun_kod', how='left')
                urun_toplam['depo_stok'] = urun_toplam['depo_stok'].fillna(0)
                
                # 4. BRÜT KAR VE MARJ HESAPLA
                st.write("**💰  SMM ve Ciro kontrol (ilk 5 ürün):**")
                sample = urun_toplam[['urun_kod', 'satis', 'ciro', 'smm']].head(5)
                st.dataframe(sample)
                
                ortalama_smm = urun_toplam['smm'].mean()
                ortalama_ciro = urun_toplam['ciro'].mean()
                
                if ortalama_smm < ortalama_ciro * 0.1:
                    st.warning("⚠️ SMM birim maliyet olarak algılandı. Toplam maliyet = SMM × Satış")
                    urun_toplam['toplam_smm'] = urun_toplam['smm'] * urun_toplam['satis']
                else:
                    urun_toplam['toplam_smm'] = urun_toplam['smm']
                
                urun_toplam['brut_kar'] = urun_toplam['ciro'] - urun_toplam['toplam_smm']
                
                # Brüt kar marjı
                urun_toplam['brut_kar_marji'] = np.where(
                    urun_toplam['ciro'] > 0,
                    (urun_toplam['brut_kar'] / urun_toplam['ciro'] * 100),
                    0
                )
                
                
                # 5. COVER HESAPLA
                urun_toplam['toplam_stok'] = (
                    urun_toplam['stok'] + 
                    urun_toplam['yol'] + 
                    urun_toplam['depo_stok']
                )
                
                urun_toplam['cover'] = np.where(
                    urun_toplam['satis'] > 0,
                    urun_toplam['toplam_stok'] / urun_toplam['satis'],
                    999
                )
                
                
                # 6. COVER SEGMENT ATAMASI
                # Segmentasyon range'lerini al
                product_ranges = st.session_state.segmentation_params['product_ranges']
                product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
                
                urun_toplam['cover_segment'] = pd.cut(
                    urun_toplam['cover'],
                    bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
                    labels=product_labels,
                    include_lowest=True
                )
                
                urun_toplam['cover_segment'] = urun_toplam['cover_segment'].astype(str)
                
                st.write(f"**🎯 Debug: Cover segment dağılımı:**")
                st.write(urun_toplam['cover_segment'].value_counts().sort_index())
                
                # 7. GENİŞLETME KATSAYISINI EKLE
                urun_toplam = urun_toplam.merge(
                    cover_matrix.rename(columns={'katsayi': 'genlestirme_katsayisi'}),
                    on='cover_segment',
                    how='left'
                )
                urun_toplam['genlestirme_katsayisi'] = urun_toplam['genlestirme_katsayisi'].fillna(1.0)
                
                # 8. FORWARD COVER VE MIN SEVK EKLE
                default_fc = kpi_df['forward_cover'].mean()
                urun_toplam['forward_cover'] = default_fc
                
                # Min sevk adeti
                if st.session_state.sevkiyat_sonuc is not None:
                    sevk_df = st.session_state.sevkiyat_sonuc.copy()
                    sevk_df['urun_kod'] = sevk_df['urun_kod'].astype(str)
                    
                    min_sevk = sevk_df.groupby('urun_kod')['sevkiyat_miktari'].sum().reset_index()
                    min_sevk.columns = ['urun_kod', 'min_sevk_adeti']
                    
                    urun_toplam = urun_toplam.merge(min_sevk, on='urun_kod', how='left')
                else:
                    urun_toplam['min_sevk_adeti'] = 0
                
                urun_toplam['min_sevk_adeti'] = urun_toplam['min_sevk_adeti'].fillna(0)
                
                # 9. FİLTRELERİ UYGULA
                urun_toplam['filtre_uygun'] = (
                    (urun_toplam['cover'] < cover_threshold) &
                    (urun_toplam['brut_kar_marji'] > margin_threshold)
                )
                
                filtre_sayisi = urun_toplam['filtre_uygun'].sum()
                st.write(f"**✅ Filtreye uygun ürün:** {filtre_sayisi}")
                st.write(f"   - Cover < {cover_threshold}: {(urun_toplam['cover'] < cover_threshold).sum()}")
                st.write(f"   - Brüt Kar Marjı > {margin_threshold}%: {(urun_toplam['brut_kar_marji'] > margin_threshold).sum()}")
                
                # 10. ALIM SİPARİŞ HESAPLA
                # Formül: [(satış × genişletme × (forward_cover + 2)] - [stok + yol + depo_stok] + min_sevk
                
                urun_toplam['talep'] = (
                    urun_toplam['satis'] * 
                    urun_toplam['genlestirme_katsayisi'] * 
                    (urun_toplam['forward_cover'] + 2)
                )
                
                urun_toplam['mevcut_stok'] = (
                    urun_toplam['stok'] + 
                    urun_toplam['yol'] + 
                    urun_toplam['depo_stok']
                )
                
                urun_toplam['alim_siparis_hesap'] = (
                    urun_toplam['talep'] - urun_toplam['mevcut_stok']
                )
                
                # Filtreye uygunsa ve pozitifse min_sevk ekle
                urun_toplam['alim_siparis'] = urun_toplam.apply(
                    lambda row: (
                        max(0, row['alim_siparis_hesap'] + row['min_sevk_adeti'])
                        if row['filtre_uygun'] and row['alim_siparis_hesap'] > 0
                        else 0
                    ),
                    axis=1
                )
                
                st.write(f"**📦  Alım sipariş > 0 olan ürün:** {(urun_toplam['alim_siparis'] > 0).sum()}")
                st.write(f"**📦  Toplam alım sipariş:** {urun_toplam['alim_siparis'].sum():,.0f}")
                
                # 11. SONUÇLARI HAZIRLA
                sonuc_df = urun_toplam[[
                    'urun_kod', 'cover_segment',
                    'stok', 'yol', 'depo_stok', 'satis',
                    'ciro', 'toplam_smm', 'brut_kar', 'brut_kar_marji',
                    'cover', 'genlestirme_katsayisi', 'forward_cover',
                    'min_sevk_adeti', 'filtre_uygun', 'alim_siparis'
                ]].copy()
                
                sonuc_df = sonuc_df.sort_values('alim_siparis', ascending=False).reset_index(drop=True)
                
                st.session_state.alim_siparis_sonuc = sonuc_df
                
                st.success("✅ Alım sipariş hesaplaması tamamlandı!")
                st.balloons()
                
                # SONUÇLAR
                st.markdown("---")
                st.subheader("📊 Alım Sipariş Sonuçları")
                
                # Metrikler
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    toplam_alim = sonuc_df['alim_siparis'].sum()
                    st.metric("📦 Toplam Alım Sipariş", f"{toplam_alim:,.0f}")
                
                with col2:
                    alim_sku = (sonuc_df['alim_siparis'] > 0).sum()
                    st.metric("🏷️ Alım Gereken SKU", f"{alim_sku}")
                
                with col3:
                    filtre_uygun = sonuc_df['filtre_uygun'].sum()
                    st.metric("✅ Filtreye Uygun", f"{filtre_uygun}")
                
                with col4:
                    if alim_sku > 0:
                        ort_alim = toplam_alim / alim_sku
                        st.metric("📊 Ort. Alım/SKU", f"{ort_alim:,.0f}")
                    else:
                        st.metric("📊 Ort. Alım/SKU", "0")
                
                st.markdown("---")
                
                # Cover Segment bazında özet
                st.subheader("🎯 Cover Segment Bazında Analiz")
                
                if (sonuc_df['alim_siparis'] > 0).sum() > 0:
                    cover_dist = sonuc_df[sonuc_df['alim_siparis'] > 0].groupby('cover_segment').agg({
                        'urun_kod': 'count',
                        'alim_siparis': 'sum'
                    }).reset_index()
                    cover_dist.columns = ['Cover Segment', 'Ürün Sayısı', 'Toplam Alım']
                    
                    # Sırala
                    cover_dist['sort_key'] = cover_dist['Cover Segment'].apply(
                        lambda x: int(x.split('-')[0]) if x.split('-')[0].isdigit() else 9999
                    )
                    cover_dist = cover_dist.sort_values('sort_key').drop('sort_key', axis=1)
                    
                    st.dataframe(cover_dist, use_container_width=True)
                
                st.markdown("---")
                
                # Detaylı tablo
                st.subheader("📋 Detaylı Alım Sipariş Tablosu")
                
                show_all = st.checkbox("Tüm ürünleri göster (alım sipariş=0 dahil)", value=False)
                
                if show_all:
                    display_df = sonuc_df
                else:
                    display_df = sonuc_df[sonuc_df['alim_siparis'] > 0]
                
                st.write(f"**Gösterilen ürün sayısı:** {len(display_df)}")
                
                if len(display_df) > 0:
                    st.dataframe(
                        display_df.style.format({
                            'stok': '{:,.0f}',
                            'yol': '{:,.0f}',
                            'depo_stok': '{:,.0f}',
                            'satis': '{:,.0f}',
                            'ciro': '{:,.2f}',
                            'toplam_smm': '{:,.2f}',
                            'brut_kar': '{:,.2f}',
                            'brut_kar_marji': '{:.2f}%',
                            'cover': '{:.2f}',
                            'genlestirme_katsayisi': '{:.2f}',
                            'forward_cover': '{:.2f}',
                            'min_sevk_adeti': '{:,.0f}',
                            'alim_siparis': '{:,.0f}'
                        }),
                        use_container_width=True,
                        height=500
                    )
                    
                    st.markdown("---")
                    
                    # Top 10
                    st.subheader("🏆 En Yüksek Alım Siparişli 10 Ürün")
                    
                    top_10 = display_df.nlargest(10, 'alim_siparis')[[
                        'urun_kod', 'cover_segment', 'cover',
                        'brut_kar_marji', 'satis', 'alim_siparis'
                    ]]
                    
                    st.dataframe(
                        top_10.style.format({
                            'cover': '{:.2f}',
                            'brut_kar_marji': '{:.2f}%',
                            'satis': '{:,.0f}',
                            'alim_siparis': '{:,.0f}'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("ℹ️ Filtreye uygun ürün bulunamadı. Filtre değerlerini ayarlayın.")
                
                st.markdown("---")
                
                # Export
                st.subheader("📥 Sonuçları Dışa Aktar")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📥 CSV İndir (Tümü)",
                        data=sonuc_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="alim_siparis_tum.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    alim_var = sonuc_df[sonuc_df['alim_siparis'] > 0]
                    st.download_button(
                        label="📥 CSV İndir (Alım>0)",
                        data=alim_var.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="alim_siparis_pozitif.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"❌ Hata oluştu: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ============================================
# 📈 RAPORLAR - TAMAMI DÜZELTİLMİŞ
# ============================================
elif menu == "📈 Raporlar":
    st.title("📈 Raporlar ve Analizler")
    st.markdown("---")
    
    # Hata ayıklama için session state kontrolü
    st.write("**🔍 Debug: Session State Kontrolü**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"Sevkiyat Sonucu: {'✅ Var' if st.session_state.sevkiyat_sonuc is not None else '❌ Yok'}")
        if st.session_state.sevkiyat_sonuc is not None:
            st.write(f"Satır: {len(st.session_state.sevkiyat_sonuc)}")
    
    with col2:
        st.write(f"Ürün Master: {'✅ Var' if st.session_state.urun_master is not None else '❌ Yok'}")
    
    with col3:
        st.write(f"Mağaza Master: {'✅ Var' if st.session_state.magaza_master is not None else '❌ Yok'}")
    
    if st.session_state.sevkiyat_sonuc is None:
        st.error("⚠️ Henüz hesaplama yapılmadı!")
        st.info("Lütfen önce 'Hesaplama' menüsünden hesaplama yapın.")
        
        # Debug için hesaplama verisi oluşturma butonu (sadece geliştirme sırasında)
        if st.button("🛠️ Test Verisi Oluştur (Debug)"):
            # Basit test verisi oluştur
            test_data = pd.DataFrame({
                'sira_no': [1, 2, 3],
                'oncelik': [1, 2, 3],
                'magaza_kod': ['M001', 'M002', 'M003'],
                'magaza_ad': ['Mağaza A', 'Mağaza B', 'Mağaza C'],
                'urun_kod': ['U001', 'U002', 'U003'],
                'urun_ad': ['Ürün A', 'Ürün B', 'Ürün C'],
                'magaza_segment': ['0-4', '5-8', '9-12'],
                'urun_segment': ['0-4', '5-8', '9-12'],
                'durum': ['RPT', 'Initial', 'Min'],
                'stok': [100, 150, 200],
                'yol': [10, 15, 20],
                'satis': [50, 60, 70],
                'ihtiyac_miktari': [200, 250, 300],
                'sevkiyat_miktari': [180, 220, 280],
                'depo_kod': ['D001', 'D001', 'D002'],
                'stok_yoklugu_satis_kaybi': [20, 30, 20]
            })
            st.session_state.sevkiyat_sonuc = test_data
            st.success("✅ Test verisi oluşturuldu! Sayfayı yenileyin.")
            st.rerun()
    else:
        result_df = st.session_state.sevkiyat_sonuc.copy()
        
        # Debug: Veri yapısını göster
        with st.expander("🔍 Veri Yapısı (Debug)", expanded=False):
            st.write("**Kolonlar:**", list(result_df.columns))
            st.write("**İlk 5 satır:**")
            st.dataframe(result_df.head(), use_container_width=True)
            st.write("**Temel İstatistikler:**")
            st.write(f"- Toplam satır: {len(result_df)}")
            
            # KOLON ADI DÜZELTMESİ
            sevkiyat_kolon_adi = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon_adi = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon_adi = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            if sevkiyat_kolon_adi in result_df.columns:
                st.write(f"- Sevkiyat miktarı > 0: {(result_df[sevkiyat_kolon_adi] > 0).sum()}")
            if ihtiyac_kolon_adi in result_df.columns:
                st.write(f"- İhtiyaç miktarı > 0: {(result_df[ihtiyac_kolon_adi] > 0).sum()}")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📦 Ürün Analizi",
            "🏪 Mağaza Analizi", 
            "⚠️ Satış Kaybı Analizi",
            "🗺️ İl Bazında Harita"
        ])
        
        # ============================================
        # ÜRÜN ANALİZİ - DÜZELTİLMİŞ
        # ============================================
        with tab1:
            st.subheader("📦 Ürün Bazında Analiz")
            
            # KOLON ADI DÜZELTMESİ
            sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            # Ürün bazında toplamlar
            urun_sevkiyat = result_df.groupby('urun_kod').agg({
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum',
                kayip_kolon: 'sum',
                'magaza_kod': 'nunique'
            }).reset_index()

            urun_sevkiyat.columns = ['urun_kod', 'İhtiyaç', 'Sevkiyat', 'Satış Kaybı', 'Mağaza Sayısı']
            
            # Hesaplamalar
            urun_sevkiyat['Sevkiyat/İhtiyaç %'] = np.where(
                urun_sevkiyat['İhtiyaç'] > 0,
                (urun_sevkiyat['Sevkiyat'] / urun_sevkiyat['İhtiyaç'] * 100),
                0
            ).round(2)
            
            urun_sevkiyat['Kayıp Oranı %'] = np.where(
                urun_sevkiyat['İhtiyaç'] > 0,
                (urun_sevkiyat['Satış Kaybı'] / urun_sevkiyat['İhtiyaç'] * 100),
                0
            ).round(2)
            
            # Ürün master'dan detayları ekle
            if st.session_state.urun_master is not None:
                urun_detay = st.session_state.urun_master[['urun_kod', 'urun_ad', 'marka_ad', 'mg_ad']].copy()
                urun_detay['urun_kod'] = urun_detay['urun_kod'].astype(str)
                urun_sevkiyat['urun_kod'] = urun_sevkiyat['urun_kod'].astype(str)
                
                urun_sevkiyat = urun_sevkiyat.merge(urun_detay, on='urun_kod', how='left')
                
                # Kolon sıralaması
                urun_sevkiyat = urun_sevkiyat[[
                    'urun_kod', 'urun_ad', 'marka_ad', 'mg_ad', 
                    'İhtiyaç', 'Sevkiyat', 'Sevkiyat/İhtiyaç %', 
                    'Satış Kaybı', 'Kayıp Oranı %', 'Mağaza Sayısı'
                ]]
                
                urun_sevkiyat.columns = [
                    'Ürün Kodu', 'Ürün Adı', 'Marka', 'Mal Grubu', 
                    'İhtiyaç', 'Sevkiyat', 'Sevkiyat/İhtiyaç %',
                    'Satış Kaybı', 'Kayıp Oranı %', 'Mağaza Sayısı'
                ]
            else:
                # Ürün master yoksa sadece kodlarla çalış
                urun_sevkiyat.columns = [
                    'Ürün Kodu', 'İhtiyaç', 'Sevkiyat', 'Satış Kaybı', 'Mağaza Sayısı',
                    'Sevkiyat/İhtiyaç %', 'Kayıp Oranı %'
                ]
            
            # En yüksek sevkiyatlı 10 ürün
            top_10_urun = urun_sevkiyat.nlargest(10, 'Sevkiyat')
            
            # Metrikler
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Toplam Ürün", len(urun_sevkiyat))
            with col2:
                st.metric("Toplam İhtiyaç", f"{urun_sevkiyat['İhtiyaç'].sum():,.0f}")
            with col3:
                st.metric("Toplam Sevkiyat", f"{urun_sevkiyat['Sevkiyat'].sum():,.0f}")
            with col4:
                toplam_kayip = urun_sevkiyat['Satış Kaybı'].sum()
                st.metric("Toplam Kayıp", f"{toplam_kayip:,.0f}")
            
            st.markdown("---")
            
            # Filtreleme seçenekleri
            col1, col2 = st.columns(2)
            with col1:
                min_sevkiyat = st.number_input("Min Sevkiyat Filtresi", 
                                             min_value=0, 
                                             value=0,
                                             help="Sadece bu değerden yüksek sevkiyatı olan ürünleri göster")
            
            with col2:
                min_mağaza = st.number_input("Min Mağaza Sayısı", 
                                           min_value=0, 
                                           value=0,
                                           help="Sadece bu sayıdan fazla mağazada bulunan ürünleri göster")
            
            # Filtrele
            filtered_urun = urun_sevkiyat[
                (urun_sevkiyat['Sevkiyat'] >= min_sevkiyat) & 
                (urun_sevkiyat['Mağaza Sayısı'] >= min_mağaza)
            ]
            
            st.write(f"**Filtrelenmiş Ürün Sayısı:** {len(filtered_urun)}")
            
            # Tablolar
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 Ürün Performans Tablosu")
                st.dataframe(
                    filtered_urun.style.format({
                        'İhtiyaç': '{:,.0f}',
                        'Sevkiyat': '{:,.0f}',
                        'Sevkiyat/İhtiyaç %': '{:.1f}%',
                        'Satış Kaybı': '{:,.0f}',
                        'Kayıp Oranı %': '{:.1f}%',
                        'Mağaza Sayısı': '{:.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
            
            with col2:
                st.subheader("🏆 En İyi Performans")
                if len(filtered_urun) > 0:
                    best_coverage = filtered_urun.nlargest(5, 'Sevkiyat/İhtiyaç %')[['Ürün Kodu', 'Sevkiyat/İhtiyaç %']]
                    st.dataframe(best_coverage, use_container_width=True)
                
                st.subheader("⚠️ En Fazla Kayıp")
                if len(filtered_urun) > 0:
                    worst_loss = filtered_urun.nlargest(5, 'Satış Kaybı')[['Ürün Kodu', 'Satış Kaybı']]
                    st.dataframe(worst_loss, use_container_width=True)
            
            st.markdown("---")
            
            # Grafikler
            col1, col2 = st.columns(2)
            
            with col1:
                if len(top_10_urun) > 0:
                    st.write("**Top 10 Ürün - Sevkiyat Miktarı**")
                    grafik_df = top_10_urun.set_index('Ürün Kodu' if 'Ürün Adı' not in top_10_urun.columns else 'Ürün Adı')[['Sevkiyat']]
                    st.bar_chart(grafik_df)
            
            with col2:
                if len(filtered_urun) > 0:
                    st.write("**Sevkiyat/İhtiyaç Oranı Dağılımı**")
                    oran_dagilim = filtered_urun['Sevkiyat/İhtiyaç %'].value_counts(bins=10).sort_index()
                    # Grafik etiketlerini düzelt
                    oran_dagilim.index = [f"%{int(interval.left)}-%{int(interval.right)}" for interval in oran_dagilim.index]
                    st.bar_chart(oran_dagilim)
            
            st.markdown("---")
            
            # İndirme butonları
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Tüm Ürün Analizi İndir (CSV)",
                    data=urun_sevkiyat.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="urun_analizi_tum.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📥 Filtrelenmiş Ürünler İndir (CSV)",
                    data=filtered_urun.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="urun_analizi_filtreli.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # ============================================
        # MAĞAZA ANALİZİ - DÜZELTİLMİŞ
        # ============================================
        with tab2:
            st.subheader("🏪 Mağaza Bazında Analiz")
            
            # KOLON ADI DÜZELTMESİ
            sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            # Mağaza bazında toplamlar
            magaza_ozet = result_df.groupby('magaza_kod').agg({
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum',
                kayip_kolon: 'sum',
                'urun_kod': 'nunique'
            }).reset_index()
            
            magaza_ozet.columns = ['magaza_kod', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']
            
            # Mağaza adlarını ekle - VERİ TİPİ DÜZELTMESİ
            if st.session_state.magaza_master is not None:
                magaza_detay = st.session_state.magaza_master[['magaza_kod', 'magaza_ad', 'il', 'bolge']].copy()
                magaza_detay['magaza_kod'] = magaza_detay['magaza_kod'].astype(str)
                magaza_ozet['magaza_kod'] = magaza_ozet['magaza_kod'].astype(str)
                
                magaza_ozet = magaza_ozet.merge(magaza_detay, left_on='magaza_kod', right_on='magaza_kod', how='left')
                
                # Kolon sıralaması
                magaza_ozet = magaza_ozet[['magaza_kod', 'magaza_ad', 'il', 'bolge', 
                                         'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']]
                magaza_ozet.columns = ['Mağaza Kod', 'Mağaza Adı', 'İl', 'Bölge', 
                                     'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']
            else:
                magaza_ozet.columns = ['Mağaza Kod', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Satış Kaybı', 'Ürün Sayısı']
            
            # Hesaplamalar
            magaza_ozet['Gerçekleşme %'] = np.where(
                magaza_ozet['Toplam İhtiyaç'] > 0,
                (magaza_ozet['Toplam Sevkiyat'] / magaza_ozet['Toplam İhtiyaç'] * 100),
                0
            ).round(2)
            
            magaza_ozet['Kayıp Oranı %'] = np.where(
                magaza_ozet['Toplam İhtiyaç'] > 0,
                (magaza_ozet['Satış Kaybı'] / magaza_ozet['Toplam İhtiyaç'] * 100),
                0
            ).round(2)
            
            magaza_ozet = magaza_ozet.sort_values('Toplam İhtiyaç', ascending=False)
            
            # Metrikler
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
            
            # Filtreleme
            col1, col2 = st.columns(2)
            with col1:
                min_ihtiyac = st.number_input("Min İhtiyaç Filtresi", 
                                            min_value=0, 
                                            value=0,
                                            help="Sadece bu değerden yüksek ihtiyacı olan mağazaları göster")
            
            with col2:
                bolge_filtre = st.multiselect(
                    "Bölge Filtresi",
                    options=magaza_ozet['Bölge'].unique() if 'Bölge' in magaza_ozet.columns else [],
                    default=[]
                )
            
            # Filtrele
            filtered_magaza = magaza_ozet[magaza_ozet['Toplam İhtiyaç'] >= min_ihtiyac]
            
            if bolge_filtre and 'Bölge' in filtered_magaza.columns:
                filtered_magaza = filtered_magaza[filtered_magaza['Bölge'].isin(bolge_filtre)]
            
            st.write(f"**Filtrelenmiş Mağaza Sayısı:** {len(filtered_magaza)}")
            
            # Ana tablo
            st.dataframe(
                filtered_magaza.style.format({
                    'Toplam İhtiyaç': '{:,.0f}',
                    'Toplam Sevkiyat': '{:,.0f}',
                    'Satış Kaybı': '{:,.0f}',
                    'Ürün Sayısı': '{:.0f}',
                    'Gerçekleşme %': '{:.1f}%',
                    'Kayıp Oranı %': '{:.1f}%'
                }),
                use_container_width=True,
                height=400
            )
            
            st.markdown("---")
            
            # Grafikler
            col1, col2 = st.columns(2)
            
            with col1:
                if len(filtered_magaza) > 0:
                    st.write("**Top 10 Mağaza - İhtiyaç Miktarı**")
                    top_10_magaza = filtered_magaza.head(10).set_index('Mağaza Adı' if 'Mağaza Adı' in filtered_magaza.columns else 'Mağaza Kod')[['Toplam İhtiyaç']]
                    st.bar_chart(top_10_magaza)
            
            with col2:
                if len(filtered_magaza) > 0:
                    st.write("**Gerçekleşme Oranı Dağılımı**")
                    basari_dagilim = filtered_magaza['Gerçekleşme %'].value_counts(bins=10).sort_index()
                    # Grafik etiketlerini düzelt
                    basari_dagilim.index = [f"%{int(interval.left)}-%{int(interval.right)}" for interval in basari_dagilim.index]
                    st.bar_chart(basari_dagilim)
            
            st.markdown("---")
            
            # Bölge bazında özet (eğer bölge bilgisi varsa)
            if 'Bölge' in filtered_magaza.columns and len(filtered_magaza) > 0:
                st.subheader("🗺️ Bölge Bazında Performans")
                
                bolge_ozet = filtered_magaza.groupby('Bölge').agg({
                    'Mağaza Kod': 'count',
                    'Toplam İhtiyaç': 'sum',
                    'Toplam Sevkiyat': 'sum',
                    'Satış Kaybı': 'sum'
                }).reset_index()
                
                # YENİ HESAPLAMA: Toplam Sevkiyat / Mağaza Sayısı
                bolge_ozet['Ortalama Sevkiyat/Mağaza'] = (bolge_ozet['Toplam Sevkiyat'] / bolge_ozet['Mağaza Kod']).round(0)
                bolge_ozet['Gerçekleşme %'] = (bolge_ozet['Toplam Sevkiyat'] / bolge_ozet['Toplam İhtiyaç'] * 100).round(2)
                
                bolge_ozet.columns = ['Bölge', 'Mağaza Sayısı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Toplam Kayıp', 'Ortalama Sevkiyat/Mağaza', 'Gerçekleşme %']
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.dataframe(
                        bolge_ozet.style.format({
                            'Mağaza Sayısı': '{:.0f}',
                            'Toplam İhtiyaç': '{:,.0f}',
                            'Toplam Sevkiyat': '{:,.0f}',
                            'Toplam Kayıp': '{:,.0f}',
                            'Ortalama Sevkiyat/Mağaza': '{:,.0f}',
                            'Gerçekleşme %': '{:.1f}%'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    st.write("**Bölge Bazında Ortalama Sevkiyat/Mağaza**")
                    bolge_chart = bolge_ozet.set_index('Bölge')[['Ortalama Sevkiyat/Mağaza']]
                    st.bar_chart(bolge_chart)
            
            st.download_button(
                label="📥 Mağaza Analizi İndir (CSV)",
                data=filtered_magaza.to_csv(index=False, encoding='utf-8-sig'),
                file_name="magaza_analizi.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ============================================
        # SATIŞ KAYBI ANALİZİ - DÜZELTİLMİŞ
        # ============================================
        with tab3:
            st.subheader("⚠️ Stok Yokluğu Kaynaklı Satış Kaybı Analizi")
            
            # KOLON ADI DÜZELTMESİ
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            
            kayip_df = result_df[result_df[kayip_kolon] > 0].copy()
            
            if len(kayip_df) > 0:
                # Metrikler
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Kayıp Olan Satır", len(kayip_df))
                with col2:
                    toplam_kayip = kayip_df[kayip_kolon].sum()
                    st.metric("Toplam Satış Kaybı", f"{toplam_kayip:,.0f}")
                with col3:
                    toplam_ihtiyac = result_df[ihtiyac_kolon].sum()
                    kayip_oran = (toplam_kayip / toplam_ihtiyac * 100) if toplam_ihtiyac > 0 else 0
                    st.metric("Kayıp Oranı", f"{kayip_oran:.2f}%")
                with col4:
                    ortalama_kayip = kayip_df[kayip_kolon].mean()
                    st.metric("Ortalama Kayıp/Satır", f"{ortalama_kayip:.1f}")
                
                st.markdown("---")
                
                # Detaylı analiz
                st.subheader("📋 Detaylı Kayıp Analizi")
                
                # En fazla kayıp olan 20 satır
                st.write("**En Fazla Kayıp Olan 20 Satır:**")
                top_kayip = kayip_df.nlargest(20, kayip_kolon)[[
                    'magaza_kod', 'magaza_ad', 'urun_kod', 'urun_ad', 
                    ihtiyac_kolon, sevkiyat_kolon, kayip_kolon
                ]]
                
                # Kolon isimlerini düzelt
                top_kayip.columns = ['magaza_kod', 'magaza_ad', 'urun_kod', 'urun_ad', 
                                   'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi']
                
                st.dataframe(
                    top_kayip.style.format({
                        'ihtiyac_miktari': '{:,.0f}',
                        'sevkiyat_miktari': '{:,.0f}',
                        'stok_yoklugu_satis_kaybi': '{:,.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                st.markdown("---")
                
                # Grup bazında analizler
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Ürün Bazında Toplam Kayıp (Top 15):**")
                    urun_kayip = kayip_df.groupby('urun_kod').agg({
                        kayip_kolon: 'sum',
                        'magaza_kod': 'nunique'
                    }).reset_index()
                    
                    # Ürün adlarını ekle
                    if st.session_state.urun_master is not None:
                        urun_detay = st.session_state.urun_master[['urun_kod', 'urun_ad']].copy()
                        urun_detay['urun_kod'] = urun_detay['urun_kod'].astype(str)
                        urun_kayip['urun_kod'] = urun_kayip['urun_kod'].astype(str)
                        urun_kayip = urun_kayip.merge(urun_detay, on='urun_kod', how='left')
                        urun_kayip = urun_kayip[['urun_kod', 'urun_ad', kayip_kolon, 'magaza_kod']]
                        urun_kayip.columns = ['Ürün Kodu', 'Ürün Adı', 'Toplam Kayıp', 'Etkilenen Mağaza']
                    else:
                        urun_kayip.columns = ['Ürün Kodu', 'Toplam Kayıp', 'Etkilenen Mağaza']
                    
                    top_15_urun = urun_kayip.nlargest(15, 'Toplam Kayıp')
                    st.dataframe(
                        top_15_urun.style.format({
                            'Toplam Kayıp': '{:,.0f}',
                            'Etkilenen Mağaza': '{:.0f}'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    st.write("**Mağaza Bazında Toplam Kayıp (Top 15):**")
                    magaza_kayip = kayip_df.groupby('magaza_kod').agg({
                        kayip_kolon: 'sum',
                        'urun_kod': 'nunique'
                    }).reset_index()
                    
                    # Mağaza adlarını ekle - VERİ TİPİ DÜZELTMESİ
                    if st.session_state.magaza_master is not None:
                        magaza_detay = st.session_state.magaza_master[['magaza_kod', 'magaza_ad']].copy()
                        magaza_detay['magaza_kod'] = magaza_detay['magaza_kod'].astype(str)
                        magaza_kayip['magaza_kod'] = magaza_kayip['magaza_kod'].astype(str)
                        magaza_kayip = magaza_kayip.merge(magaza_detay, on='magaza_kod', how='left')
                        magaza_kayip = magaza_kayip[['magaza_kod', 'magaza_ad', kayip_kolon, 'urun_kod']]
                        magaza_kayip.columns = ['Mağaza Kodu', 'Mağaza Adı', 'Toplam Kayıp', 'Etkilenen Ürün']
                    else:
                        magaza_kayip.columns = ['Mağaza Kodu', 'Toplam Kayıp', 'Etkilenen Ürün']
                    
                    top_15_magaza = magaza_kayip.nlargest(15, 'Toplam Kayıp')
                    st.dataframe(
                        top_15_magaza.style.format({
                            'Toplam Kayıp': '{:,.0f}',
                            'Etkilenen Ürün': '{:.0f}'
                        }),
                        use_container_width=True
                    )
                
                st.markdown("---")
                
                # Segment bazında analiz
                st.subheader("🎯 Segment Bazında Kayıp Analizi")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Ürün Segmenti Bazında Kayıp:**")
                    urun_segment_kayip = kayip_df.groupby('urun_segment').agg({
                        kayip_kolon: 'sum',
                        'magaza_kod': 'nunique'
                    }).reset_index()
                    urun_segment_kayip.columns = ['Ürün Segmenti', 'Toplam Kayıp', 'Etkilenen Mağaza']
                    urun_segment_kayip = urun_segment_kayip.sort_values('Toplam Kayıp', ascending=False)
                    
                    st.dataframe(
                        urun_segment_kayip.style.format({
                            'Toplam Kayıp': '{:,.0f}',
                            'Etkilenen Mağaza': '{:.0f}'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    st.write("**Mağaza Segmenti Bazında Kayıp:**")
                    magaza_segment_kayip = kayip_df.groupby('magaza_segment').agg({
                        kayip_kolon: 'sum',
                        'urun_kod': 'nunique'
                    }).reset_index()
                    magaza_segment_kayip.columns = ['Mağaza Segmenti', 'Toplam Kayıp', 'Etkilenen Ürün']
                    magaza_segment_kayip = magaza_segment_kayip.sort_values('Toplam Kayıp', ascending=False)
                    
                    st.dataframe(
                        magaza_segment_kayip.style.format({
                            'Toplam Kayıp': '{:,.0f}',
                            'Etkilenen Ürün': '{:.0f}'
                        }),
                        use_container_width=True
                    )
                
                st.markdown("---")
                
                # İndirme butonları
                st.subheader("📥 Raporları İndir")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        label="📥 Detaylı Kayıp Raporu",
                        data=kayip_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="detayli_kayip_raporu.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Ürün Bazında Özet",
                        data=urun_kayip.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="urun_bazinda_kayip.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col3:
                    st.download_button(
                        label="📥 Mağaza Bazında Özet",
                        data=magaza_kayip.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="magaza_bazinda_kayip.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
            else:
                st.success("🎉 Tebrikler! Hiç stok yokluğu kaynaklı satış kaybı yok!")
                st.info("""
                **Bu ne anlama geliyor?**
                - Tüm mağazaların ihtiyaçları depo stoğundan karşılanabildi
                - Sevkiyat planlaması optimal şekilde çalıştı
                - Stok dağıtımı dengeli ve verimli
                """)
        
        # ============================================
        # İL BAZINDA HARİTA - DÜZELTİLMİŞ
        # ============================================
        with tab4:
            st.subheader("🗺️ İl Bazında Sevkiyat Haritası")
            
            # Plotly kontrolü
            try:
                import plotly.express as px
                import plotly.graph_objects as go
                st.success("✅ Plotly kütüphanesi yüklü!")
            except ImportError:
                st.error("Plotly kütüphanesi yüklü değil! requirements.txt dosyasına 'plotly' ekleyin.")
                st.stop()
            
            if st.session_state.magaza_master is None:
                st.warning("⚠️ Mağaza Master verisi yüklenmemiş! Harita için il bilgisi gerekiyor.")
            else:
                # KOLON ADI DÜZELTMESİ
                sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
                ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
                
                # İl bazında verileri hazırla
                il_verileri = result_df.groupby('magaza_kod').agg({
                    sevkiyat_kolon: 'sum',
                    ihtiyac_kolon: 'sum'
                }).reset_index()
                
                # Mağaza master'dan il bilgilerini ekle - VERİ TİPİ DÜZELTMESİ
                magaza_master = st.session_state.magaza_master[['magaza_kod', 'il']].copy()
                magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                il_verileri['magaza_kod'] = il_verileri['magaza_kod'].astype(str)
                
                il_verileri = il_verileri.merge(magaza_master, on='magaza_kod', how='left')
                
                # İl bazında toplamlar
                il_bazinda = il_verileri.groupby('il').agg({
                    sevkiyat_kolon: 'sum',
                    ihtiyac_kolon: 'sum',
                    'magaza_kod': 'nunique'
                }).reset_index()
                
                il_bazinda.columns = ['İl', 'Toplam Sevkiyat', 'Toplam İhtiyaç', 'Mağaza Sayısı']
                
                # Ortalama sevkiyat/mağaza hesapla
                il_bazinda['Ortalama Sevkiyat/Mağaza'] = (il_bazinda['Toplam Sevkiyat'] / il_bazinda['Mağaza Sayısı']).round(0)
                
                # Segmentlere ayır (4 segment)
                segmentler = pd.cut(
                    il_bazinda['Ortalama Sevkiyat/Mağaza'], 
                    bins=4,
                    labels=['Çok Düşük', 'Düşük', 'Orta', 'Yüksek']
                )
                il_bazinda['Performans Segmenti'] = segmentler
                
                # Türkiye il koordinatları
                turkiye_iller = {
                    'İstanbul': (41.0082, 28.9784), 'Ankara': (39.9334, 32.8597), 'İzmir': (38.4237, 27.1428),
                    'Bursa': (40.1885, 29.0610), 'Antalya': (36.8969, 30.7133), 'Adana': (37.0000, 35.3213),
                    'Konya': (37.8667, 32.4833), 'Gaziantep': (37.0662, 37.3833), 'Şanlıurfa': (37.1591, 38.7969),
                    'Mersin': (36.8000, 34.6333), 'Kocaeli': (40.8533, 29.8815), 'Diyarbakır': (37.9144, 40.2306),
                    'Hatay': (36.4018, 36.3498), 'Manisa': (38.6191, 27.4289), 'Kayseri': (38.7312, 35.4787),
                    'Samsun': (41.2928, 36.3313), 'Balıkesir': (39.6484, 27.8826), 'Kahramanmaraş': (37.5858, 36.9371),
                    'Van': (38.4891, 43.4080), 'Aydın': (37.8560, 27.8416), 'Tekirdağ': (40.9781, 27.5117),
                    'Denizli': (37.7765, 29.0864), 'Muğla': (37.2153, 28.3636), 'Eskişehir': (39.7767, 30.5206),
                    'Trabzon': (41.0015, 39.7178), 'Ordu': (40.9833, 37.8833), 'Afyonkarahisar': (38.7638, 30.5403),
                    'Sivas': (39.7477, 37.0179), 'Malatya': (38.3552, 38.3095), 'Erzurum': (39.9000, 41.2700),
                    'Elazığ': (38.6810, 39.2264), 'Batman': (37.8812, 41.1351), 'Kütahya': (39.4167, 29.9833),
                    'Çorum': (40.5506, 34.9556), 'Isparta': (37.7648, 30.5566), 'Osmaniye': (37.2130, 36.1763),
                    'Çanakkale': (40.1553, 26.4142), 'Giresun': (40.9128, 38.3895), 'Aksaray': (38.3687, 34.0370),
                    'Yozgat': (39.8200, 34.8044), 'Edirne': (41.6667, 26.5667), 'Düzce': (40.8433, 31.1565),
                    'Tokat': (40.3167, 36.5500), 'Kastamonu': (41.3767, 33.7765), 'Uşak': (38.6823, 29.4082),
                    'Kırklareli': (41.7333, 27.2167), 'Niğde': (37.9667, 34.6833), 'Rize': (41.0201, 40.5234),
                    'Amasya': (40.6500, 35.8333), 'Bolu': (40.7333, 31.6000), 'Nevşehir': (38.6939, 34.6857),
                    'Bilecik': (40.1500, 29.9833), 'Burdur': (37.7167, 30.2833), 'Kırıkkale': (39.8468, 33.5153),
                    'Karabük': (41.2000, 32.6333), 'Karaman': (37.1759, 33.2287), 'Kırşehir': (39.1500, 34.1667),
                    'Sinop': (42.0231, 35.1531), 'Hakkari': (37.5833, 43.7333), 'Iğdır': (39.9167, 44.0333),
                    'Yalova': (40.6500, 29.2667), 'Bartın': (41.6344, 32.3375), 'Ardahan': (41.1105, 42.7022),
                    'Bayburt': (40.2552, 40.2249), 'Kilis': (36.7164, 37.1156), 'Muş': (38.9462, 41.7539),
                    'Siirt': (37.9333, 41.9500), 'Tunceli': (39.1071, 39.5400), 'Şırnak': (37.5164, 42.4611),
                    'Bitlis': (38.4000, 42.1000), 'Artvin': (41.1667, 41.8333), 'Gümüşhane': (40.4603, 39.4814),
                    'Ağrı': (39.7191, 43.0513), 'Erzincan': (39.7500, 39.5000), 'Adıyaman': (37.7648, 38.2786),
                    'Zonguldak': (41.4564, 31.7987), 'Mardin': (37.3212, 40.7245), 'Sakarya': (40.6937, 30.4358)
                }
                
                # Koordinatları dataframe'e ekle
                il_bazinda['lat'] = il_bazinda['İl'].map(lambda x: turkiye_iller.get(x, (0, 0))[0])
                il_bazinda['lon'] = il_bazinda['İl'].map(lambda x: turkiye_iller.get(x, (0, 0))[1])
                
                # Koordinatı olmayan illeri filtrele
                il_bazinda = il_bazinda[il_bazinda['lat'] != 0]
                
                if len(il_bazinda) > 0:
                    # Renk skalası
                    renk_skalasi = {
                        'Çok Düşük': 'red',
                        'Düşük': 'orange', 
                        'Orta': 'yellow',
                        'Yüksek': 'green'
                    }
                    
                    # Interaktif harita oluştur
                    st.subheader("📍 İl Bazında Ortalama Sevkiyat Performansı")
                    
                    fig = px.scatter_mapbox(
                        il_bazinda,
                        lat="lat",
                        lon="lon", 
                        hover_name="İl",
                        hover_data={
                            'Ortalama Sevkiyat/Mağaza': True,
                            'Toplam Sevkiyat': True,
                            'Mağaza Sayısı': True,
                            'Performans Segmenti': True,
                            'lat': False,
                            'lon': False
                        },
                        color="Performans Segmenti",
                        color_discrete_map=renk_skalasi,
                        size="Ortalama Sevkiyat/Mağaza",
                        size_max=25,
                        zoom=4.5,
                        center={"lat": 39.0, "lon": 35.0},
                        height=600,
                        title="Türkiye İl Bazında Ortalama Sevkiyat/Mağaza Dağılımı"
                    )
                    
                    fig.update_layout(
                        mapbox_style="open-street-map",
                        margin={"r": 0, "t": 30, "l": 0, "b": 0}
                    )
                    
                    st.info("🔍 Haritayı mouse tekerleği ile zoom in/out yapabilir, sürükleyerek hareket ettirebilirsiniz.")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # İl seçimi için dropdown
                    st.markdown("---")
                    st.subheader("🔍 İl Detayları")
                    
                    secilen_il = st.selectbox(
                        "Detayını görmek istediğiniz ili seçin:",
                        options=il_bazinda['İl'].sort_values().tolist()
                    )
                    
                    if secilen_il:
                        # Seçilen ilin detaylarını göster
                        il_detay = il_bazinda[il_bazinda['İl'] == secilen_il].iloc[0]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Ortalama Sevkiyat/Mağaza", f"{il_detay['Ortalama Sevkiyat/Mağaza']:,.0f}")
                        with col2:
                            st.metric("Toplam Sevkiyat", f"{il_detay['Toplam Sevkiyat']:,.0f}")
                        with col3:
                            st.metric("Mağaza Sayısı", f"{il_detay['Mağaza Sayısı']:,.0f}")
                        with col4:
                            st.metric("Performans", il_detay['Performans Segmenti'])
                        
                        # Seçilen ildeki mağaza detayları - DÜZELTİLMİŞ
                        st.subheader(f"🏪 {secilen_il} İlindeki Mağaza Performansları")
                        
                        try:
                            # Mağaza bazında verileri hazırla - VERİ TİPLERİNİ DÜZELT
                            magaza_detay = result_df[result_df['magaza_kod'].isin(
                                magaza_master[magaza_master['il'] == secilen_il]['magaza_kod'].astype(str)
                            )]
                            
                            if len(magaza_detay) > 0:
                                magaza_ozet = magaza_detay.groupby('magaza_kod').agg({
                                    sevkiyat_kolon: 'sum',
                                    ihtiyac_kolon: 'sum',
                                    'urun_kod': 'nunique'
                                }).reset_index()
                                
                                # VERİ TİPLERİNİ AYNI YAP
                                magaza_ozet['magaza_kod'] = magaza_ozet['magaza_kod'].astype(str)
                                
                                # Mağaza adlarını ekle - VERİ TİPİ UYUMLU HALE GETİR
                                magaza_master_temp = st.session_state.magaza_master[['magaza_kod', 'magaza_ad']].copy()
                                magaza_master_temp['magaza_kod'] = magaza_master_temp['magaza_kod'].astype(str)
                                
                                magaza_ozet = magaza_ozet.merge(
                                    magaza_master_temp, 
                                    on='magaza_kod', 
                                    how='left'
                                )
                                
                                magaza_ozet.columns = ['Mağaza Kodu', 'Toplam Sevkiyat', 'Toplam İhtiyaç', 'Ürün Sayısı', 'Mağaza Adı']
                                magaza_ozet['Gerçekleşme %'] = np.where(
                                    magaza_ozet['Toplam İhtiyaç'] > 0,
                                    (magaza_ozet['Toplam Sevkiyat'] / magaza_ozet['Toplam İhtiyaç'] * 100),
                                    0
                                ).round(1)
                                
                                st.dataframe(
                                    magaza_ozet.style.format({
                                        'Toplam Sevkiyat': '{:,.0f}',
                                        'Toplam İhtiyaç': '{:,.0f}',
                                        'Ürün Sayısı': '{:.0f}',
                                        'Gerçekleşme %': '{:.1f}%'
                                    }),
                                    use_container_width=True,
                                    height=300
                                )
                            else:
                                st.info("Bu ilde mağaza verisi bulunamadı.")
                                
                        except Exception as e:
                            st.error(f"Mağaza detayları yüklenirken hata oluştu: {str(e)}")
                    
                    # Segment bazında özet
                    st.markdown("---")
                    st.subheader("📊 Performans Segmentleri Özeti")
                    
                    segment_ozet = il_bazinda.groupby('Performans Segmenti').agg({
                        'İl': 'count',
                        'Ortalama Sevkiyat/Mağaza': 'mean',
                        'Toplam Sevkiyat': 'sum'
                    }).reset_index()
                    
                    segment_ozet.columns = ['Performans Segmenti', 'İl Sayısı', 'Ort. Sevkiyat/Mağaza', 'Toplam Sevkiyat']
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.dataframe(
                            segment_ozet.style.format({
                                'İl Sayısı': '{:.0f}',
                                'Ort. Sevkiyat/Mağaza': '{:,.0f}',
                                'Toplam Sevkiyat': '{:,.0f}'
                            }),
                            use_container_width=True
                        )
                    
                    with col2:
                        st.write("**Segment Dağılımı**")
                        segment_dagilim = segment_ozet.set_index('Performans Segmenti')[['İl Sayısı']]
                        st.bar_chart(segment_dagilim)
                    
                    # İndirme butonu
                    st.download_button(
                        label="📥 İl Bazında Analiz İndir (CSV)",
                        data=il_bazinda.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="il_bazinda_analiz.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                else:
                    st.warning("Harita için yeterli il verisi bulunamadı.")
                    
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

