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
if 'klasman_data' not in st.session_state:
    st.session_state.klasman_data = None
if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }
if 'weekly_data' not in st.session_state:
    st.session_state.weekly_data = None
if 'target_matrix' not in st.session_state:
    st.session_state.target_matrix = None

# Sidebar menü
st.sidebar.title("📦 Sevkiyat Planlama")
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "📋 Klasman Parametreleri", "🎯 Segmentasyon Ayarları", 
     "📊 Stok/Satış Verisi", "🎲 Hedef Matris", "🚚 Sevkiyat Hesaplama"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================
if menu == "🏠 Ana Sayfa":
    st.title("🏠 Retail Sevkiyat Planlama Sistemi")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Klasman Sayısı", 
            len(st.session_state.klasman_data) if st.session_state.klasman_data is not None else 0
        )
    
    with col2:
        st.metric(
            "Veri Yüklendi", 
            "✅" if st.session_state.weekly_data is not None else "❌"
        )
    
    with col3:
        st.metric(
            "Matris Durumu",
            "✅" if st.session_state.target_matrix is not None else "❌"
        )
    
    st.markdown("### 📋 İşlem Adımları")
    st.info("""
    1. **Klasman Parametreleri**: Klasman bilgilerini CSV ile yükleyin
    2. **Segmentasyon Ayarları**: Ürün ve mağaza gruplama aralıklarını belirleyin
    3. **Stok/Satış Verisi**: Haftalık verileri yükleyin (son 4 hafta)
    4. **Hedef Matris**: Her segment için şişme oranlarını girin
    5. **Sevkiyat Hesaplama**: Sonuçları görüntüleyin ve export edin
    """)

# ============================================
# 📋 KLASMAN PARAMETRELERİ
# ============================================
elif menu == "📋 Klasman Parametreleri":
    st.title("📋 Klasman Parametreleri")
    st.markdown("---")
    
    # CSV yükleme
    st.subheader("📤 CSV Yükleme")
    st.info("**Beklenen format**: klasman_id, klasman_adi, min_deger, max_deger, forward_cover")
    
    uploaded_file = st.file_uploader("Klasman parametrelerini yükleyin", type=['csv'])
    
    # Örnek CSV indirme
    example_df = pd.DataFrame({
        'klasman_id': [1, 2, 3],
        'klasman_adi': ['Klasman A', 'Klasman B', 'Klasman C'],
        'min_deger': [0, 100, 500],
        'max_deger': [99, 499, 999],
        'forward_cover': [1.5, 2.0, 2.5]
    })
    
    st.download_button(
        label="📥 Örnek CSV İndir",
        data=example_df.to_csv(index=False, encoding='utf-8-sig'),
        file_name="ornek_klasman.csv",
        mime="text/csv"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validasyon
            required_cols = ['klasman_id', 'klasman_adi', 'min_deger', 'max_deger', 'forward_cover']
            if all(col in df.columns for col in required_cols):
                st.session_state.klasman_data = df
                st.success(f"✅ {len(df)} klasman başarıyla yüklendi!")
            else:
                st.error(f"❌ CSV'de eksik sütunlar var. Beklenen: {', '.join(required_cols)}")
        except Exception as e:
            st.error(f"❌ CSV okuma hatası: {str(e)}")
    
    # Tablo düzenleme
    if st.session_state.klasman_data is not None:
        st.markdown("---")
        st.subheader("✏️ Parametre Düzenleme")
        
        edited_df = st.data_editor(
            st.session_state.klasman_data,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "klasman_id": st.column_config.NumberColumn("ID", required=True),
                "klasman_adi": st.column_config.TextColumn("Klasman Adı", required=True),
                "min_deger": st.column_config.NumberColumn("Min Değer", min_value=0, required=True),
                "max_deger": st.column_config.NumberColumn("Max Değer", min_value=0, required=True),
                "forward_cover": st.column_config.NumberColumn("Forward Cover", min_value=0.0, format="%.2f", required=True)
            }
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Değişiklikleri Kaydet", type="primary"):
                # Validasyon
                errors = []
                for idx, row in edited_df.iterrows():
                    if row['min_deger'] >= row['max_deger']:
                        errors.append(f"Satır {idx+1}: Min değer, max değerden küçük olmalı")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    st.session_state.klasman_data = edited_df
                    # CSV'ye kaydet
                    edited_df.to_csv('data/klasman_params.csv', index=False, encoding='utf-8-sig')
                    st.success("✅ Değişiklikler kaydedildi!")
                    st.rerun()

# ============================================
# 🎯 SEGMENTASYON AYARLARI
# ============================================
elif menu == "🎯 Segmentasyon Ayarları":
    st.title("🎯 Segmentasyon Ayarları")
    st.markdown("---")
    
    st.info("**Stok Tutar/Satış (SMM) oranına göre** ürün ve mağazaları gruplandırma")
    
    # Ürün segmentasyonu
    st.subheader("🏷️ Ürün Segmentasyonu")
    
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
    
    st.markdown("---")
    
    # Mağaza segmentasyonu
    st.subheader("🏪 Mağaza Segmentasyonu")
    
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
    
    if st.button("💾 Segmentasyon Ayarlarını Kaydet", type="primary"):
        st.session_state.segmentation_params = {
            'product_ranges': product_ranges,
            'store_ranges': store_ranges
        }
        st.success("✅ Ayarlar kaydedildi!")

# ============================================
# 📊 STOK/SATIŞ VERİSİ
# ============================================
elif menu == "📊 Stok/Satış Verisi":
    st.title("📊 Stok/Satış Verisi Yükleme")
    st.markdown("---")
    
    st.info("**Beklenen format**: hafta, magaza_id, urun_id, stok_tutar, satis (Son 4 hafta)")
    
    uploaded_file = st.file_uploader("Haftalık verileri yükleyin", type=['csv'], key="weekly_upload")
    
    # Örnek CSV
    example_weekly = pd.DataFrame({
        'hafta': [1, 1, 2, 2, 3, 3, 4, 4],
        'magaza_id': ['M001', 'M002', 'M001', 'M002', 'M001', 'M002', 'M001', 'M002'],
        'urun_id': ['U001', 'U001', 'U001', 'U001', 'U001', 'U001', 'U001', 'U001'],
        'stok_tutar': [1000, 1500, 1100, 1600, 950, 1450, 1050, 1550],
        'satis': [200, 250, 180, 240, 210, 260, 190, 255]
    })
    
    st.download_button(
        label="📥 Örnek Haftalık Veri CSV İndir",
        data=example_weekly.to_csv(index=False, encoding='utf-8-sig'),
        file_name="ornek_haftalik_veri.csv",
        mime="text/csv"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            required_cols = ['hafta', 'magaza_id', 'urun_id', 'stok_tutar', 'satis']
            if all(col in df.columns for col in required_cols):
                # Son 4 hafta ortalamasını hesapla
                df['smm'] = df['stok_tutar'] / df['satis'].replace(0, 1)  # Sıfıra bölme hatası önleme
                
                avg_smm = df.groupby(['magaza_id', 'urun_id'])['smm'].mean().reset_index()
                avg_smm.columns = ['magaza_id', 'urun_id', 'avg_smm_4week']
                
                st.session_state.weekly_data = avg_smm
                
                st.success(f"✅ {len(avg_smm)} ürün-mağaza kombinasyonu için ortalama SMM hesaplandı!")
                
                st.subheader("📊 Veri Özeti")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Mağaza", avg_smm['magaza_id'].nunique())
                with col2:
                    st.metric("Toplam Ürün", avg_smm['urun_id'].nunique())
                with col3:
                    st.metric("Ortalama SMM", f"{avg_smm['avg_smm_4week'].mean():.2f}")
                
                st.dataframe(avg_smm.head(20), use_container_width=True)
            else:
                st.error(f"❌ CSV'de eksik sütunlar var. Beklenen: {', '.join(required_cols)}")
        except Exception as e:
            st.error(f"❌ CSV okuma hatası: {str(e)}")

# ============================================
# 🎲 HEDEF MATRİS
# ============================================
elif menu == "🎲 Hedef Matris":
    st.title("🎲 Hedef Matris - Şişme Oranları")
    st.markdown("---")
    
    if st.session_state.weekly_data is None:
        st.warning("⚠️ Önce 'Stok/Satış Verisi' bölümünden veri yükleyin!")
    else:
        # Segmentasyon yap
        from sklearn.preprocessing import KBinsDiscretizer
        
        data = st.session_state.weekly_data.copy()
        
        # Ürün segmentasyonu
        product_ranges = st.session_state.segmentation_params['product_ranges']
        data['urun_segment'] = pd.cut(
            data['avg_smm_4week'], 
            bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in product_ranges],
            include_lowest=True
        )
        
        # Mağaza için grup bazlı SMM hesapla
        store_smm = data.groupby('magaza_id')['avg_smm_4week'].mean().reset_index()
        store_ranges = st.session_state.segmentation_params['store_ranges']
        store_smm['magaza_segment'] = pd.cut(
            store_smm['avg_smm_4week'],
            bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
            labels=[f"{r[0]}-{r[1]}" for r in store_ranges],
            include_lowest=True
        )
        
        # Segmentasyon sonuçları
        st.subheader("📊 Segmentasyon Sonuçları")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Ürün Dağılımı**")
            prod_dist = data['urun_segment'].value_counts().sort_index()
            st.dataframe(prod_dist, use_container_width=True)
        
        with col2:
            st.write("**Mağaza Dağılımı**")
            store_dist = store_smm['magaza_segment'].value_counts().sort_index()
            st.dataframe(store_dist, use_container_width=True)
        
        st.markdown("---")
        
        # Matris oluştur
        st.subheader("🎯 Şişme Oranı Matrisi")
        st.info("Her ürün-mağaza segment kombinasyonu için şişme oranını girin")
        
        prod_segments = sorted([str(x) for x in data['urun_segment'].unique() if pd.notna(x)])
        store_segments = sorted([str(x) for x in store_smm['magaza_segment'].unique() if pd.notna(x)])
        
        # Matris için data editor
        if st.session_state.target_matrix is None:
            matrix_data = pd.DataFrame(
                1.0,  # Varsayılan değer
                index=prod_segments,
                columns=store_segments
            )
        else:
            matrix_data = st.session_state.target_matrix
        
        edited_matrix = st.data_editor(
            matrix_data,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                col,
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                format="%.2f"
            ) for col in store_segments}
        )
        
        if st.button("💾 Matris Kaydet", type="primary"):
            st.session_state.target_matrix = edited_matrix
            st.success("✅ Hedef matris kaydedildi!")

# ============================================
# 🚚 SEVKİYAT HESAPLAMA
# ============================================
elif menu == "🚚 Sevkiyat Hesaplama":
    st.title("🚚 Sevkiyat Hesaplama")
    st.markdown("---")
    
    if st.session_state.klasman_data is None or st.session_state.weekly_data is None or st.session_state.target_matrix is None:
        st.warning("⚠️ Tüm adımları tamamlayın!")
        st.info("""
        - ✅ Klasman Parametreleri
        - ✅ Segmentasyon Ayarları
        - ✅ Stok/Satış Verisi
        - ✅ Hedef Matris
        """)
    else:
        st.success("✅ Tüm veriler hazır! Hesaplama yapılabilir.")
        
        if st.button("🚀 Sevkiyat Hesapla", type="primary"):
            st.info("🔄 Hesaplama yapılıyor...")
            # Burada sevkiyat algoritması çalışacak
            st.success("✅ Hesaplama tamamlandı!")
            st.balloons()
