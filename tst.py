import streamlit as st
import pandas as pd
import numpy as np
import time
import io
import logging
from datetime import datetime

# -------------------------------
# LOGGING SETUP
# -------------------------------
logging.basicConfig(
    filename='sevkiyat_optimizasyon.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------------------------------
# MEMORY YÖNETİMİ
# -------------------------------
def clear_session_state():
    """Session state'i temizle"""
    keys_to_clear = [
        'sevk_df', 'total_sevk', 'original_sevkiyat_df', 
        'depo_stok_df', 'sevk_df_result', 'file_data',
        'urunler_df', 'magazalar_df'
    ]
    
    cleared_count = 0
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            cleared_count += 1
    
    # Cache temizle
    st.cache_data.clear()
    
    logging.info(f"Memory temizlendi: {cleared_count} öğe silindi")
    return cleared_count

def get_memory_usage():
    """Session state memory kullanımını hesapla"""
    total_size = 0
    details = {}
    
    for key, value in st.session_state.items():
        if isinstance(value, pd.DataFrame):
            size = value.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
            total_size += size
            details[key] = f"{size:.2f} MB"
    
    return total_size, details

# -------------------------------
# VERİ VALIDASYON
# -------------------------------
def validate_file_structure(file_data):
    """Dosya yapılarını doğrula"""
    
    required_files = {
        'sevkiyat': {
            'required_columns': ['depo_id', 'urun_id', 'magaza_id', 'haftalik_satis', 'mevcut_stok'],
            'optional_columns': ['yolda', 'klasmankod'],
            'data_types': {
                'haftalik_satis': 'numeric',
                'mevcut_stok': 'numeric'
            }
        },
        'depo': {
            'required_columns': ['depo_id', 'urun_id', 'depo_stok'],
            'optional_columns': [],
            'data_types': {
                'depo_stok': 'numeric'
            }
        }
    }
    
    errors = []
    warnings = []
    file_status = {}
    
    for file_type, requirements in required_files.items():
        # Dosyayı bul
        matching_file = None
        for name, df in file_data.items():
            if file_type in name.lower():
                matching_file = (name, df)
                break
        
        if matching_file is None:
            errors.append(f"❌ **{file_type.upper()}** dosyası bulunamadı")
            file_status[file_type] = "❌ Eksik"
            continue
        
        file_name, df = matching_file
        df_normalized = normalize_columns(df)
        
        # Zorunlu kolonları kontrol et
        missing_required = set(requirements['required_columns']) - set(df_normalized.columns)
        if missing_required:
            errors.append(f"❌ **{file_name}** dosyasında eksik kolonlar: {', '.join(missing_required)}")
            file_status[file_type] = "❌ Hatalı"
            continue
        
        # Opsiyonel kolonları kontrol et
        missing_optional = set(requirements['optional_columns']) - set(df_normalized.columns)
        if missing_optional:
            warnings.append(f"⚠️ **{file_name}** dosyasında opsiyonel kolonlar eksik: {', '.join(missing_optional)}")
        
        # Veri tiplerini kontrol et
        for col, expected_type in requirements['data_types'].items():
            if col in df_normalized.columns:
                if expected_type == 'numeric':
                    try:
                        pd.to_numeric(df_normalized[col], errors='coerce')
                    except:
                        errors.append(f"❌ **{file_name}**: '{col}' kolonu sayısal olmalı")
        
        # Boş değer kontrolü
        null_counts = df_normalized[requirements['required_columns']].isnull().sum()
        if null_counts.sum() > 0:
            warnings.append(f"⚠️ **{file_name}**: Boş değerler var - {null_counts[null_counts > 0].to_dict()}")
        
        # Negatif değer kontrolü
        for col in requirements['data_types'].keys():
            if col in df_normalized.columns:
                numeric_col = pd.to_numeric(df_normalized[col], errors='coerce')
                negative_count = (numeric_col < 0).sum()
                if negative_count > 0:
                    warnings.append(f"⚠️ **{file_name}**: '{col}' kolonunda {negative_count} negatif değer")
        
        # Satır sayısı kontrolü
        if len(df) == 0:
            errors.append(f"❌ **{file_name}**: Dosya boş")
            file_status[file_type] = "❌ Boş"
        elif len(df) < 10:
            warnings.append(f"⚠️ **{file_name}**: Çok az veri ({len(df)} satır)")
            file_status[file_type] = "✅ OK (Az veri)"
        else:
            file_status[file_type] = f"✅ OK ({len(df):,} satır)"
    
    # Opsiyonel dosyaları kontrol et
    optional_files = ['urun', 'magaza', 'cover', 'kpi', 'yasak']
    for opt_file in optional_files:
        found = any(opt_file in name.lower() for name in file_data.keys())
        if found:
            file_status[opt_file] = "✅ Yüklendi"
        else:
            file_status[opt_file] = "⚪ Yüklenmedi (opsiyonel)"
    
    return errors, warnings, file_status

def validate_data_quality(sevk_df, depo_stok_df):
    """Veri kalitesini kontrol et"""
    
    issues = []
    
    # 1. Sevkiyat verisi kontrolü
    if sevk_df is not None and not sevk_df.empty:
        # Stok < 0 kontrolü
        negative_stock = (sevk_df['mevcut_stok'] < 0).sum()
        if negative_stock > 0:
            issues.append(f"⚠️ {negative_stock} kayıtta negatif mevcut stok")
        
        # Satış = 0 kontrolü
        zero_sales = (sevk_df['haftalik_satis'] == 0).sum()
        if zero_sales > 0:
            issues.append(f"ℹ️ {zero_sales} kayıtta haftalık satış 0")
        
        # Duplicate kontrolü
        duplicates = sevk_df.duplicated(subset=['depo_id', 'magaza_id', 'urun_id']).sum()
        if duplicates > 0:
            issues.append(f"⚠️ {duplicates} duplicate kayıt (depo-mağaza-ürün)")
    
    # 2. Depo stok kontrolü
    if depo_stok_df is not None and not depo_stok_df.empty:
        # Negatif stok
        negative_depo = (depo_stok_df['depo_stok'] < 0).sum()
        if negative_depo > 0:
            issues.append(f"⚠️ {negative_depo} kayıtta negatif depo stok")
        
        # Sıfır stok oranı
        zero_stock = (depo_stok_df['depo_stok'] == 0).sum()
        zero_percent = (zero_stock / len(depo_stok_df) * 100) if len(depo_stok_df) > 0 else 0
        if zero_percent > 50:
            issues.append(f"⚠️ Depo stoklarının %{zero_percent:.1f}'i sıfır")
    
    return issues

# -------------------------------
# YARDIMCI FONKSİYONLAR (OPTİMİZE EDİLMİŞ)
# -------------------------------

@st.cache_data(ttl=3600)
def read_csv_advanced(file_content, file_name):
    """Gelişmiş CSV okuma - CACHE'LENMİŞ"""
    try:
        return pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
    except:
        try:
            return pd.read_csv(io.BytesIO(file_content), encoding='iso-8859-9')
        except:
            content = file_content.decode('utf-8', errors='ignore')
            delimiters = [',', ';', '\t', '|']
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                    if len(df.columns) > 1:
                        return df
                except:
                    continue
            return pd.read_csv(io.StringIO(content), delimiter=',')

def normalize_columns(df):
    """Kolon isimlerini standardize et - OPTİMİZE"""
    if df.empty:
        return df
    
    df = df.copy()
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(r'[^a-z0-9_]', '_', regex=True))
    return df

def standardize_ids(df, id_columns):
    """ID kolonlarını standardize et - VEKTÖRİZE"""
    df = df.copy()
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

def calculate_urun_cover_vectorized(df):
    """Ürün cover'ını vektörize hesapla - HIZLI"""
    haftalik_satis = pd.to_numeric(df['haftalik_satis'], errors='coerce').fillna(0.1)
    mevcut_stok = pd.to_numeric(df['mevcut_stok'], errors='coerce').fillna(0)
    
    # Satış > 0 olanlar için cover hesapla
    cover = np.where(
        haftalik_satis > 0,
        mevcut_stok / haftalik_satis,
        999  # Satış yoksa yüksek cover
    )
    
    # Stok <= 0 olanlar için 0
    cover = np.where(mevcut_stok <= 0, 0, cover)
    
    return np.round(cover, 2)

def get_cover_grubu_vectorized(cover_values, cover_gruplari):
    """Cover gruplarını vektörize belirle - HIZLI"""
    cover_values = pd.to_numeric(cover_values, errors='coerce').fillna(999)
    
    # Grup etiketlerini belirle
    result = pd.Series(['20+'] * len(cover_values), index=cover_values.index)
    
    for grup in sorted(cover_gruplari, key=lambda x: x['min']):
        mask = (cover_values >= grup['min']) & (cover_values <= grup['max'])
        result[mask] = grup['etiket']
    
    return result

def apply_yasaklar_vectorized(sevk_df, yasaklar_df):
    """Yasakları vektörize uygula - ÇOK HIZLI"""
    
    if yasaklar_df is None or yasaklar_df.empty:
        return sevk_df, 0
    
    try:
        # Yasakları normalize et
        yasaklar_df = normalize_columns(yasaklar_df)
        yasaklar_df = standardize_ids(yasaklar_df, ['magaza_id', 'urun_id'])
        sevk_df = standardize_ids(sevk_df, ['magaza_id', 'urun_id'])
        
        # Yasaklı kombinasyonları işaretle
        yasakli_df = yasaklar_df[yasaklar_df['yasak'].astype(int) == 1][['magaza_id', 'urun_id']].copy()
        yasakli_df['yasak_flag'] = True
        
        # Merge ile yasakları işaretle
        sevk_df = sevk_df.merge(
            yasakli_df,
            on=['magaza_id', 'urun_id'],
            how='left'
        )
        
        # Yasaklı kayıtların ihtiyacını 0 yap
        yasakli_mask = sevk_df['yasak_flag'] == True
        yasakli_count = yasakli_mask.sum()
        
        sevk_df.loc[yasakli_mask, 'ihtiyac'] = 0
        sevk_df.drop('yasak_flag', axis=1, inplace=True, errors='ignore')
        
        if yasakli_count > 0:
            st.success(f"🚫 {yasakli_count:,} yasaklı kaydın ihtiyacı 0'a çekildi")
            logging.info(f"Yasaklar uygulandı: {yasakli_count} kayıt")
        
        return sevk_df, yasakli_count
        
    except Exception as e:
        st.error(f"❌ Yasak uygulama hatası: {str(e)}")
        logging.error(f"Yasak uygulama hatası: {str(e)}")
        return sevk_df, 0

# -------------------------------
# OPTİMİZE EDİLMİŞ HESAPLAMA
# -------------------------------

def calculate_shipment_optimized_v2(file_data, params, cover_gruplari):
    """Vektörize edilmiş sevkiyat hesaplama - 2-5X DAHA HIZLI"""
    
    start_time = time.time()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(progress, message):
        progress_bar.progress(progress)
        status_text.text(f"⏳ {message}...")
        logging.info(message)
    
    try:
        update_progress(0.05, "Dosyalar yükleniyor")
        
        # Dosyaları yükle
        sevk_df = next((df for name, df in file_data.items() if "sevkiyat" in name.lower()), None)
        depo_stok_df = next((df for name, df in file_data.items() if "depo" in name.lower() and "stok" in name.lower()), None)
        urunler_df = next((df for name, df in file_data.items() if "urun" in name.lower()), None)
        magazalar_df = next((df for name, df in file_data.items() if "magaza" in name.lower()), None)
        cover_df = next((df for name, df in file_data.items() if "cover" in name.lower()), None)
        kpi_df = next((df for name, df in file_data.items() if "kpi" in name.lower()), None)
        yasaklar_df = next((df for name, df in file_data.items() if "yasak" in name.lower()), None)
        
        if sevk_df is None or depo_stok_df is None:
            raise Exception("Zorunlu dosyalar eksik!")
        
        update_progress(0.10, "Veri kalitesi kontrol ediliyor")
        quality_issues = validate_data_quality(sevk_df, depo_stok_df)
        if quality_issues:
            with st.expander("⚠️ Veri Kalitesi Uyarıları", expanded=False):
                for issue in quality_issues:
                    st.warning(issue)
        
        update_progress(0.15, "Veri normalize ediliyor")
        
        # Normalize et
        sevk_df = normalize_columns(sevk_df)
        depo_stok_df = normalize_columns(depo_stok_df)
        original_sevkiyat_df = sevk_df.copy()
        
        # ID'leri standardize et - VEKTÖRİZE
        id_columns = ['depo_id', 'magaza_id', 'urun_id']
        sevk_df = standardize_ids(sevk_df, id_columns)
        depo_stok_df = standardize_ids(depo_stok_df, ['depo_id', 'urun_id'])
        original_sevkiyat_df = standardize_ids(original_sevkiyat_df, id_columns)
        
        if urunler_df is not None:
            urunler_df = normalize_columns(urunler_df)
            urunler_df = standardize_ids(urunler_df, ['urun_id'])
            st.session_state.urunler_df = urunler_df
        
        if magazalar_df is not None:
            magazalar_df = normalize_columns(magazalar_df)
            magazalar_df = standardize_ids(magazalar_df, ['magaza_id'])
            st.session_state.magazalar_df = magazalar_df
        
        update_progress(0.25, "KPI parametreleri ekleniyor")
        
        # KPI parametrelerini ekle - VEKTÖRİZE
        if kpi_df is not None and not kpi_df.empty:
            kpi_df = normalize_columns(kpi_df)
            kpi_mapping = kpi_df.set_index('klasmankod')[['hedef_hafta', 'min_adet', 'maks_adet']].to_dict('index')
            
            sevk_df['hedef_hafta'] = sevk_df['klasmankod'].map(lambda x: kpi_mapping.get(x, {}).get('hedef_hafta', params['hedef_hafta']))
            sevk_df['min_adet'] = sevk_df['klasmankod'].map(lambda x: kpi_mapping.get(x, {}).get('min_adet', params['min_adet']))
            sevk_df['maks_adet'] = sevk_df['klasmankod'].map(lambda x: kpi_mapping.get(x, {}).get('maks_adet', params['maks_adet']))
        else:
            sevk_df['hedef_hafta'] = params['hedef_hafta']
            sevk_df['min_adet'] = params['min_adet']
            sevk_df['maks_adet'] = params['maks_adet']
        
        original_sevkiyat_df['hedef_hafta'] = sevk_df['hedef_hafta']
        
        update_progress(0.35, "Mağaza cover ekleniyor")
        
        # Cover ekle - VEKTÖRİZE
        if cover_df is not None and not cover_df.empty:
            cover_df = normalize_columns(cover_df)
            cover_df = standardize_ids(cover_df, ['magaza_id'])
            cover_mapping = cover_df.set_index('magaza_id')['cover'].to_dict()
            sevk_df['cover'] = sevk_df['magaza_id'].map(cover_mapping).fillna(999)
            original_sevkiyat_df['cover'] = original_sevkiyat_df['magaza_id'].map(cover_mapping).fillna(999)
        else:
            sevk_df['cover'] = 999
            original_sevkiyat_df['cover'] = 999
        
        update_progress(0.45, "Ürün cover hesaplanıyor (vektörize)")
        
        # Ürün cover - VEKTÖRİZE
        sevk_df['urun_cover'] = calculate_urun_cover_vectorized(sevk_df)
        original_sevkiyat_df['urun_cover'] = calculate_urun_cover_vectorized(original_sevkiyat_df)
        
        update_progress(0.55, "Cover grupları belirleniyor (vektörize)")
        
        # Cover grupları - VEKTÖRİZE
        sevk_df['magaza_cover_grubu'] = get_cover_grubu_vectorized(sevk_df['cover'], cover_gruplari)
        sevk_df['urun_cover_grubu'] = get_cover_grubu_vectorized(sevk_df['urun_cover'], cover_gruplari)
        
        # Cover <= 50 filtresi
        df_filtered = sevk_df[sevk_df['cover'] <= 50].copy()
        
        update_progress(0.60, "İhtiyaç hesaplanıyor (vektörize)")
        
        # İhtiyaç hesabı - VEKTÖRİZE
        yolda = pd.to_numeric(df_filtered.get('yolda', 0), errors='coerce').fillna(0)
        df_filtered['ihtiyac'] = np.maximum(
            0,
            (df_filtered['haftalik_satis'] * df_filtered['hedef_hafta']) - 
            (df_filtered['mevcut_stok'] + yolda)
        )
        
        yolda_orig = pd.to_numeric(original_sevkiyat_df.get('yolda', 0), errors='coerce').fillna(0)
        original_sevkiyat_df['ihtiyac'] = np.maximum(
            0,
            (original_sevkiyat_df['haftalik_satis'] * original_sevkiyat_df['hedef_hafta']) - 
            (original_sevkiyat_df['mevcut_stok'] + yolda_orig)
        )
        
        update_progress(0.65, "Yasaklar uygulanıyor (vektörize)")
        
        # Yasakları uygula - VEKTÖRİZE
        df_filtered, yasakli_count = apply_yasaklar_vectorized(df_filtered, yasaklar_df)
        original_sevkiyat_df, _ = apply_yasaklar_vectorized(original_sevkiyat_df, yasaklar_df)
        st.session_state.yasakli_kayit_sayisi = yasakli_count
        
        update_progress(0.70, "Çarpan matrisi ekleniyor (vektörize)")
        
        # Çarpan matrisini DataFrame'e çevir - TEK SEFERDE MERGE
        carpan_matrisi = st.session_state.get('carpan_matrisi', {})
        carpan_df = pd.DataFrame([
            {'magaza_cover_grubu': m, 'urun_cover_grubu': u, 'carpan': v}
            for m, urun_dict in carpan_matrisi.items()
            for u, v in urun_dict.items()
        ])
        
        df_sorted = df_filtered.merge(
            carpan_df,
            on=['magaza_cover_grubu', 'urun_cover_grubu'],
            how='left'
        )
        df_sorted['carpan'] = df_sorted['carpan'].fillna(1.0)
        
        # Sıralama
        df_sorted = df_sorted.sort_values(
            by=['urun_id', 'urun_cover', 'haftalik_satis'],
            ascending=[True, True, False]
        ).reset_index(drop=True)
        
        update_progress(0.75, f"Sevkiyat hesaplanıyor ({len(df_sorted):,} kayıt)")
        
        # Sevkiyat hesaplama - TOPLU İŞLEM
        sevk_listesi = []
        depo_stok_dict = depo_stok_df.groupby(['depo_id', 'urun_id'])['depo_stok'].sum().to_dict()
        
        # Grup bazında işlem
        for (depo, urun), grup in df_sorted.groupby(['depo_id', 'urun_id']):
            stok = depo_stok_dict.get((depo, urun), 0)
            
            if stok <= 0:
                continue
            
            # TUR 1: İhtiyaç bazlı - VEKTÖRİZE
            ihtiyac_carpanli = grup['ihtiyac'] * grup['carpan']
            sevk_tur1 = np.minimum(
                np.minimum(ihtiyac_carpanli, grup['maks_adet']),
                stok
            ).astype(int)
            
            # İhtiyaç > 0 olanları al
            tur1_mask = (sevk_tur1 > 0) & (grup['ihtiyac'] > 0)
            
            for idx, row in grup[tur1_mask].iterrows():
                sevk = sevk_tur1[idx]
                if sevk > 0:
                    stok -= sevk
                    sevk_listesi.append({
                        'depo_id': depo, 'magaza_id': row['magaza_id'], 'urun_id': urun,
                        'klasmankod': row['klasmankod'], 'tur': 1,
                        'magaza_cover_grubu': row['magaza_cover_grubu'],
                        'urun_cover_grubu': row['urun_cover_grubu'],
                        'ihtiyac': row['ihtiyac'], 'carpan': row['carpan'],
                        'sevk_miktar': sevk, 'haftalik_satis': row['haftalik_satis'],
                        'mevcut_stok': row['mevcut_stok'], 'cover': row['cover'],
                        'urun_cover': row['urun_cover'], 'hedef_hafta': row['hedef_hafta'],
                        'min_adet': row['min_adet'], 'maks_adet': row['maks_adet']
                    })
            
            # TUR 2: Min stok tamamlama
            if stok > 0:
                low_cover_mask = (grup['cover'] < 12) | (grup['urun_cover'] < 12)
                grup_tur2 = grup[low_cover_mask].copy()
                
                yolda_tur2 = pd.to_numeric(grup_tur2.get('yolda', 0), errors='coerce').fillna(0)
                eksik_min = np.maximum(0, grup_tur2['min_adet'] - (grup_tur2['mevcut_stok'] + yolda_tur2))
                eksik_min_carpanli = eksik_min * grup_tur2['carpan']
                sevk_tur2 = np.minimum(
                    np.minimum(eksik_min_carpanli, grup_tur2['maks_adet']),
                    stok
                ).astype(int)
                
                for idx, row in grup_tur2[sevk_tur2 > 0].iterrows():
                    sevk = sevk_tur2[idx]
                    if sevk > 0:
                        stok -= sevk
                        sevk_listesi.append({
                            'depo_id': depo, 'magaza_id': row['magaza_id'], 'urun_id': urun,
                            'klasmankod': row['klasmankod'], 'tur': 2,
                            'magaza_cover_grubu': row['magaza_cover_grubu'],
                            'urun_cover_grubu': row['urun_cover_grubu'],
                            'ihtiyac': row['ihtiyac'], 'carpan': row['carpan'],
                            'sevk_miktar': sevk, 'haftalik_satis': row['haftalik_satis'],
                            'mevcut_stok': row['mevcut_stok'], 'cover': row['cover'],
                            'urun_cover': row['urun_cover'], 'hedef_hafta': row['hedef_hafta'],
                            'min_adet': row['min_adet'], 'maks_adet': row['maks_adet']
                        })
            
            # Stok güncelle
            depo_stok_dict[(depo, urun)] = stok
        
        update_progress(0.90, "Sonuçlar birleştiriliyor")
        
        # Sonuçları birleştir
        if sevk_listesi:
            sevk_df_result = pd.DataFrame(sevk_listesi)
            
            total_sevk = sevk_df_result.groupby(
                ['depo_id', 'magaza_id', 'urun_id', 'klasmankod', 
                 'magaza_cover_grubu', 'urun_cover_grubu'],
                as_index=False
            ).agg({
                'sevk_miktar': 'sum', 'haftalik_satis': 'first',
                'ihtiyac': 'first', 'mevcut_stok': 'first',
                'cover': 'first', 'urun_cover': 'first',
                'carpan': 'first', 'hedef_hafta': 'first',
                'min_adet': 'first', 'maks_adet': 'first', 'tur': 'first'
            })
            
            min_tamamlama = sevk_df_result[sevk_df_result['tur'] == 2]['sevk_miktar'].sum()
            toplam_sevk = sevk_df_result['sevk_miktar'].sum()
            min_yuzde = (min_tamamlama / toplam_sevk * 100) if toplam_sevk > 0 else 0
            
            st.session_state.min_tamamlama = min_tamamlama
            st.session_state.min_yuzde = min_yuzde
            st.session_state.toplam_sevk = toplam_sevk
            st.session_state.sevk_df_result = sevk_df_result
            
        else:
            sevk_df_result = pd.DataFrame()
            total_sevk = pd.DataFrame()
            st.session_state.min_tamamlama = 0
            st.session_state.min_yuzde = 0
            st.session_state.toplam_sevk = 0
            st.session_state.sevk_df_result = pd.DataFrame()
        
        # Depo stok güncelle
        depo_stok_df_updated = pd.DataFrame([
            {'depo_id': k[0], 'urun_id': k[1], 'depo_stok': v}
            for k, v in depo_stok_dict.items()
        ])
        
        update_progress(1.0, f"Tamamlandı ({time.time() - start_time:.1f}s)")
        
        logging.info(f"Hesaplama tamamlandı: {toplam_sevk:,} adet, {len(total_sevk):,} kayıt")
        
        return sevk_df_result, total_sevk, depo_stok_df_updated, original_sevkiyat_df
        
    except Exception as e:
        progress_bar.progress(1.0)
        status_text.text("❌ Hata oluştu!")
        logging.error(f"Hesaplama hatası: {str(e)}")
        raise e

# -------------------------------
# COVER GRUPLARI VE MATRİS YÖNETİMİ
# -------------------------------

def manage_cover_groups_and_matrix():
    st.header("📊 Parametre Ayarları")
    
    # Varsayılan değerler
    default_cover_data = [
        {"min": 0, "max": 4, "etiket": "0-4"},
        {"min": 5, "max": 8, "etiket": "5-8"},
        {"min": 9, "max": 12, "etiket": "9-12"},
        {"min": 13, "max": 20, "etiket": "13-20"},
        {"min": 21, "max": 999, "etiket": "20+"}
    ]
    
    default_matrix = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 1.0, "20+": 0.9},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 1.0, "13-20": 0.9, "20+": 0.8},
        "9-12": {"0-4": 1.0, "5-8": 1.0, "9-12": 0.9, "13-20": 0.8, "20+": 0.7},
        "13-20": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0},
        "20+": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0}
    }
    
    # Session state başlatma
    if "cover_gruplari" not in st.session_state:
        st.session_state.cover_gruplari = default_cover_data.copy()
    if "carpan_matrisi" not in st.session_state:
        st.session_state.carpan_matrisi = default_matrix.copy()
    if "cover_gruplari_edited" not in st.session_state:
        st.session_state.cover_gruplari_edited = st.session_state.cover_gruplari.copy()
    if "carpan_matrisi_edited" not in st.session_state:
        st.session_state.carpan_matrisi_edited = st.session_state.carpan_matrisi.copy()
    
    # KPI ayarları
    st.subheader("🎯 KPI & Varsayılan Değerler")
    st.info("⚠️ Bu değerler SADECE KPI.csv dosyası yüklenmediğinde kullanılır")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        default_hedef_hafta = st.slider("Varsayılan Hedef Hafta", 1, 12, 4)
    with col2:
        default_min_adet = st.slider("Varsayılan Min Adet", 0, 100, 3)
    with col3:
        default_maks_adet = st.slider("Varsayılan Maks Adet", 0, 200, 20)
    
    st.markdown("---")
    
    # Cover grupları
    st.subheader("📈 Cover Grupları")
    current_df = pd.DataFrame(st.session_state.cover_gruplari_edited)
    
    edited_df = st.data_editor(
        current_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "min": st.column_config.NumberColumn("Min Cover", min_value=0, max_value=1000),
            "max": st.column_config.NumberColumn("Max Cover", min_value=0, max_value=1000),
            "etiket": st.column_config.TextColumn("Etiket")
        },
        key="cover_gruplari_editor"
    )
    
    if not edited_df.equals(current_df):
        st.session_state.cover_gruplari_edited = edited_df.to_dict('records')
        st.success("✅ Cover grupları güncellendi!")
        st.rerun()
    
    st.markdown("---")
    
    # Çarpan matrisi
    st.subheader("🎯 Sevkiyat Çarpan Matrisi")
    
    cover_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
    matrix_data = {}
    
    for magaza_grubu in cover_etiketler:
        matrix_data[magaza_grubu] = {}
        for urun_grubu in cover_etiketler:
            matrix_data[magaza_grubu][urun_grubu] = st.session_state.carpan_matrisi_edited.get(
                magaza_grubu, {}).get(urun_grubu, 1.0)
    
    matrix_df = pd.DataFrame(matrix_data).reindex(index=cover_etiketler, columns=cover_etiketler).fillna(1.0)
    
    matrix_edited = st.data_editor(
        matrix_df,
        use_container_width=True,
        column_config={col: st.column_config.NumberColumn(
            format="%.2f", min_value=0.01, max_value=2.0, step=0.1
        ) for col in matrix_df.columns},
        key="carpan_matrisi_editor"
    )
    
    if not matrix_edited.equals(matrix_df):
        st.session_state.carpan_matrisi_edited = matrix_edited.to_dict()
        st.success("✅ Çarpan matrisi güncellendi!")
        st.rerun()
    
    st.markdown("---")
    
    # Kaydetme butonları
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Değişiklikleri Kaydet", type="primary", use_container_width=True):
            st.session_state.cover_gruplari = st.session_state.cover_gruplari_edited.copy()
            st.session_state.carpan_matrisi = st.session_state.carpan_matrisi_edited.copy()
            st.success("✅ Ayarlar kaydedildi!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Varsayılanlara Dön", use_container_width=True):
            st.session_state.cover_gruplari = default_cover_data.copy()
            st.session_state.carpan_matrisi = default_matrix.copy()
            st.session_state.cover_gruplari_edited = default_cover_data.copy()
            st.session_state.carpan_matrisi_edited = default_matrix.copy()
            st.success("✅ Varsayılan değerlere dönüldü!")
            st.rerun()
    
    with col3:
        if st.button("🗑️ Memory Temizle", use_container_width=True):
            cleared = clear_session_state()
            st.success(f"✅ {cleared} öğe temizlendi!")
            st.rerun()
    
    return default_hedef_hafta, default_min_adet, default_maks_adet, edited_df

# -------------------------------
# DOSYA YÜKLEME
# -------------------------------

def create_file_upload_section():
    st.header("📁 Veri Yükleme")
    
    with st.expander("📋 Dosya Formatları", expanded=True):
        st.markdown("""
        **Zorunlu Dosyalar:**
        - **Sevkiyat.csv**: depo_id, urun_id, magaza_id, haftalik_satis, mevcut_stok
        - **Depo_Stok.csv**: depo_id, urun_id, depo_stok
        
        **Opsiyonel Dosyalar:**
        - **Urunler.csv**: urun_id, urun_adi
        - **Magazalar.csv**: magaza_id, magaza_adi
        - **Cover.csv**: magaza_id, cover
        - **KPI.csv**: klasmankod, hedef_hafta, min_adet, maks_adet
        - **Yasaklar.csv**: magaza_id, urun_id, yasak (1=yasaklı)
        """)
    
    uploaded_files = st.file_uploader("CSV dosyalarını seçin", type=["csv"], accept_multiple_files=True)
    
    file_data = {}
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                file_content = uploaded_file.getvalue()
                df = read_csv_advanced(file_content, uploaded_file.name)
                file_data[uploaded_file.name] = df
                st.success(f"✅ {uploaded_file.name} - {len(df):,} satır, {len(df.columns)} kolon")
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} okunamadı: {e}")
        
        # Validasyon yap
        st.markdown("---")
        st.subheader("🔍 Veri Validasyonu")
        
        errors, warnings, file_status = validate_file_structure(file_data)
        
        # Durum özeti
        status_df = pd.DataFrame([
            {"Dosya Tipi": k, "Durum": v}
            for k, v in file_status.items()
        ])
        st.dataframe(status_df, use_container_width=True)
        
        # Hatalar
        if errors:
            st.error("❌ **Kritik Hatalar:**")
            for error in errors:
                st.error(error)
        
        # Uyarılar
        if warnings:
            with st.expander("⚠️ Uyarılar", expanded=False):
                for warning in warnings:
                    st.warning(warning)
        
        if not errors:
            st.success("✅ Tüm zorunlu dosyalar geçerli!")
    
    return file_data

# -------------------------------
# ALIM İHTİYACI HESAPLAMA
# -------------------------------

def calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df):
    """Alım ihtiyacını hesapla - OPTİMİZE"""
    try:
        if original_sevkiyat_df.empty:
            return pd.DataFrame()
        
        sevkiyat_df = original_sevkiyat_df.copy()
        
        # Sevk miktarını ekle
        if not sevk_df.empty and 'sevk_miktar' in sevk_df.columns:
            sevk_toplam = sevk_df.groupby(['depo_id', 'magaza_id', 'urun_id'])['sevk_miktar'].sum().reset_index()
            sevkiyat_df = sevkiyat_df.merge(sevk_toplam, on=['depo_id', 'magaza_id', 'urun_id'], how='left')
            sevkiyat_df['sevk_miktar'] = sevkiyat_df['sevk_miktar'].fillna(0)
        else:
            sevkiyat_df['sevk_miktar'] = 0
        
        # Kalan ihtiyaç
        sevkiyat_df['kalan_ihtiyac'] = (sevkiyat_df['ihtiyac'] - sevkiyat_df['sevk_miktar']).clip(lower=0)
        
        # Depo stok ekle
        if not depo_stok_df.empty:
            depo_stok_toplam = depo_stok_df.groupby(['depo_id', 'urun_id'])['depo_stok'].sum().reset_index()
            sevkiyat_df = sevkiyat_df.merge(depo_stok_toplam, on=['depo_id', 'urun_id'], how='left')
            sevkiyat_df['depo_stok'] = sevkiyat_df['depo_stok'].fillna(0)
        else:
            sevkiyat_df['depo_stok'] = 0
        
        # Karşılanamayan ihtiyaçlar
        alim_siparis_df = sevkiyat_df[
            (sevkiyat_df['kalan_ihtiyac'] > 0) & (sevkiyat_df['depo_stok'] <= 0)
        ].copy()
        
        if alim_siparis_df.empty:
            return pd.DataFrame()
        
        alim_siparis_df['alim_siparis_miktari'] = alim_siparis_df['kalan_ihtiyac']
        
        # Ürün bazında toplam
        alim_siparis_toplam = alim_siparis_df.groupby(
            ['depo_id', 'urun_id', 'klasmankod'], as_index=False
        ).agg({
            'alim_siparis_miktari': 'sum',
            'kalan_ihtiyac': 'sum',
            'haftalik_satis': 'first'
        })
        
        # Ürün adı ekle
        if 'urunler_df' in st.session_state and not st.session_state.urunler_df.empty:
            urunler_df = st.session_state.urunler_df.copy()
            if 'urun_adi' in urunler_df.columns:
                alim_siparis_toplam = alim_siparis_toplam.merge(
                    urunler_df[['urun_id', 'urun_adi']], on='urun_id', how='left'
                )
        
        if 'urun_adi' not in alim_siparis_toplam.columns:
            alim_siparis_toplam['urun_adi'] = "Ürün " + alim_siparis_toplam['urun_id'].astype(str)
        
        alim_siparis_toplam['toplam_ihtiyac_cover'] = (
            alim_siparis_toplam['alim_siparis_miktari'] / alim_siparis_toplam['haftalik_satis']
        ).round(1)
        
        return alim_siparis_toplam.sort_values('alim_siparis_miktari', ascending=False)
        
    except Exception as e:
        st.error(f"Alım ihtiyacı hesaplama hatası: {str(e)}")
        logging.error(f"Alım ihtiyacı hatası: {str(e)}")
        return pd.DataFrame()

# -------------------------------
# RAPORLAR
# -------------------------------

def show_reports():
    st.title("📊 Raporlar ve Analizler")
    
    if 'total_sevk' not in st.session_state or st.session_state.total_sevk.empty:
        st.warning("ℹ️ Henüz hesaplama yapılmadı. Önce ana sayfadan hesaplama çalıştırın.")
        return
    
    total_sevk = st.session_state.total_sevk.copy()
    sevk_df_result = st.session_state.get('sevk_df_result', pd.DataFrame())
    
    tab1, tab2, tab3 = st.tabs(["📈 Özet Rapor", "🏪 Mağaza Analizi", "📦 Ürün Analizi"])
    
    with tab1:
        st.subheader("📈 Özet Metrikler")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Toplam Sevkiyat", f"{st.session_state.toplam_sevk:,}")
        col2.metric("Mağaza Sayısı", total_sevk['magaza_id'].nunique())
        col3.metric("Ürün Çeşidi", total_sevk['urun_id'].nunique())
        col4.metric("Min %", f"{st.session_state.min_yuzde:.1f}%")
        col5.metric("🚫 Yasaklı", f"{st.session_state.get('yasakli_kayit_sayisi', 0):,}")
        
        # Matris dağılımı
        if not sevk_df_result.empty:
            st.subheader("🎯 Matris Dağılımı")
            matris_dagilim = sevk_df_result.groupby(['magaza_cover_grubu', 'urun_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'magaza_id': 'nunique'
            }).reset_index()
            st.dataframe(matris_dagilim, use_container_width=True)
    
    with tab2:
        st.subheader("🏪 Mağaza Analizi")
        magaza_analiz = total_sevk.groupby('magaza_id').agg({
            'sevk_miktar': 'sum',
            'ihtiyac': 'sum',
            'cover': 'first'
        }).reset_index()
        
        magaza_analiz['ihtiyac_karsilama'] = (magaza_analiz['sevk_miktar'] / magaza_analiz['ihtiyac'] * 100).round(1)
        st.dataframe(magaza_analiz.head(100), use_container_width=True)
    
    with tab3:
        st.subheader("📦 Ürün Analizi")
        urun_analiz = total_sevk.groupby('urun_id').agg({
            'sevk_miktar': 'sum',
            'magaza_id': 'nunique',
            'ihtiyac': 'sum'
        }).reset_index()
        
        urun_analiz = urun_analiz.sort_values('sevk_miktar', ascending=False)
        st.dataframe(urun_analiz.head(100), use_container_width=True)

# -------------------------------
# ANA SAYFA
# -------------------------------

def show_main_page():
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%); 
                color: white; border-radius: 15px; margin-bottom: 25px;">
        <h1>📦 EVE Sevkiyat Planlama - OPTİMİZE VERSİYON</h1>
        <p>Vektörize İşlemler | Memory Yönetimi | Veri Validasyonu</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Memory durumu göster
    if st.session_state:
        total_size, details = get_memory_usage()
        if total_size > 0:
            with st.expander(f"💾 Memory Kullanımı: {total_size:.2f} MB", expanded=False):
                for key, size in details.items():
                    st.text(f"{key}: {size}")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Parametreler", "📁 Veri Yükleme", "🚀 Hesaplama"])
    
    with tab1:
        hedef_hafta, min_adet, maks_adet, cover_df = manage_cover_groups_and_matrix()
        st.session_state.params = {
            'hedef_hafta': hedef_hafta,
            'min_adet': min_adet,
            'maks_adet': maks_adet
        }
        st.session_state.cover_gruplari = cover_df.to_dict('records') if not cover_df.empty else []
    
    with tab2:
        file_data = create_file_upload_section()
        st.session_state.file_data = file_data
        
        if file_data:
            selected_file = st.selectbox("Dosya önizleme:", list(file_data.keys()))
            if selected_file:
                st.dataframe(file_data[selected_file].head(10), use_container_width=True)
    
    with tab3:
        st.header("🚀 Sevkiyat Hesaplama")
        
        if not st.session_state.get('file_data'):
            st.error("❌ Lütfen önce dosyaları yükleyin!")
            return
        
        # Validasyon kontrol
        errors, _, _ = validate_file_structure(st.session_state.file_data)
        if errors:
            st.error("❌ Veri validasyonu başarısız! Veri yükleme sekmesindeki hataları düzeltin.")
            return
        
        if st.button("🎯 HESAPLAMAYI BAŞLAT", type="primary", use_container_width=True):
            try:
                with st.spinner("Optimize edilmiş hesaplama çalışıyor..."):
                    sevk_df, total_sevk, depo_stok_df, original_sevkiyat_df = calculate_shipment_optimized_v2(
                        st.session_state.file_data,
                        st.session_state.params,
                        st.session_state.cover_gruplari
                    )
                    
                    st.session_state.sevk_df = sevk_df
                    st.session_state.total_sevk = total_sevk
                    st.session_state.depo_stok_df = depo_stok_df
                    st.session_state.original_sevkiyat_df = original_sevkiyat_df
                    st.session_state.calculation_done = True
                    
                    st.success("🎉 Hesaplama tamamlandı!")
                    
                    # Özet metrikler
                    if not total_sevk.empty:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Toplam Sevkiyat", f"{st.session_state.toplam_sevk:,}")
                        col2.metric("Mağaza", total_sevk['magaza_id'].nunique())
                        col3.metric("Ürün", total_sevk['urun_id'].nunique())
                        col4.metric("Yasaklı", f"{st.session_state.get('yasakli_kayit_sayisi', 0):,}")
                        
                        # İndirme butonları
                        col1, col2 = st.columns(2)
                        with col1:
                            csv_sevk = total_sevk.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "📥 Sevkiyat Planını İndir",
                                csv_sevk,
                                "sevkiyat_plani.csv",
                                "text/csv",
                                use_container_width=True
                            )
                        with col2:
                            alim_ihtiyaci = calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df)
                            if not alim_ihtiyaci.empty:
                                csv_alim = alim_ihtiyaci.to_csv(index=False, encoding='utf-8-sig')
                                st.download_button(
                                    "📥 Alım İhtiyacını İndir",
                                    csv_alim,
                                    "alim_ihtiyaci.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                        
                        st.dataframe(total_sevk.head(50), use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
                logging.error(f"Hesaplama hatası: {str(e)}")
                import traceback
                with st.expander("Hata Detayları"):
                    st.code(traceback.format_exc())

# -------------------------------
# ANA UYGULAMA
# -------------------------------

def main():
    st.set_page_config(page_title="EVE Sevkiyat - Optimize", layout="wide")
    
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; background-color: #f0f2f6;
            border-radius: 8px 8px 0px 0px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E40AF; color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    main_tab1, main_tab2 = st.tabs(["🏠 Ana Sayfa", "📈 Raporlar"])
    
    with main_tab1:
        show_main_page()
    
    with main_tab2:
        show_reports()

if __name__ == "__main__":
    main()
