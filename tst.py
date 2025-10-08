import streamlit as st
import pandas as pd
import numpy as np
import time
import io
import logging
from typing import Dict, List, Tuple, Optional

# -------------------------------
# LOGGING YAPILANDIRMASI
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------------------
# SABİTLER VE YAPILANDIRMA
# -------------------------------
class Config:
    """Uygulama sabitleri"""
    MAX_COVER_THRESHOLD = 50
    MIN_WEEKLY_SALES = 0.1
    DEFAULT_COVER = 999
    DEFAULT_CARPAN = 1.0
    
    # Zorunlu kolonlar
    REQUIRED_SEVK_COLS = ['depo_id', 'urun_id', 'magaza_id', 'haftalik_satis', 'mevcut_stok', 'klasmankod']
    REQUIRED_DEPO_COLS = ['depo_id', 'urun_id', 'depo_stok']
    
    # Numeric kolonlar
    NUMERIC_COLUMNS = [
        'haftalik_satis', 'mevcut_stok', 'yolda', 
        'cover', 'hedef_hafta', 'min_adet', 'maks_adet', 'depo_stok'
    ]
    
    # Varsayılan cover grupları
    DEFAULT_COVER_GROUPS = [
        {"min": 0, "max": 4, "etiket": "0-4"},
        {"min": 5, "max": 8, "etiket": "5-8"},
        {"min": 9, "max": 12, "etiket": "9-12"},
        {"min": 13, "max": 20, "etiket": "13-20"},
        {"min": 21, "max": 999, "etiket": "20+"}
    ]
    
    # Varsayılan sevkiyat matrisi
    DEFAULT_SEVK_MATRIX = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 1.0, "20+": 0.9},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 1.0, "13-20": 0.9, "20+": 0.8},
        "9-12": {"0-4": 1.0, "5-8": 1.0, "9-12": 0.9, "13-20": 0.8, "20+": 0.7},
        "13-20": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0},
        "20+": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0}
    }
    
    # Varsayılan alım matrisi
    DEFAULT_ALIM_MATRIX = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 1.0, "20+": 0},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 1.0, "13-20": 1.0, "20+": 0},
        "9-12": {"0-4": 1.0, "5-8": 1.0, "9-12": 1.0, "13-20": 0, "20+": 0},
        "13-20": {"0-4": 1.0, "5-8": 1.0, "9-12": 1.0, "13-20": 0, "20+": 0},
        "20+": {"0-4": 1.0, "5-8": 0, "9-12": 0, "13-20": 0, "20+": 0}
    }
    
    # Varsayılan MIN TAMAMLAMA matrisi (YENİ)
    DEFAULT_MIN_TAMAMLAMA_MATRIX = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 0.8, "20+": 0},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 0.9, "13-20": 0.5, "20+": 0},
        "9-12": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0},
        "13-20": {"0-4": 0.8, "5-8": 0.5, "9-12": 0, "13-20": 0, "20+": 0},
        "20+": {"0-4": 0, "5-8": 0, "9-12": 0, "13-20": 0, "20+": 0}
    }

# -------------------------------
# YARDIMCI FONKSIYONLAR - VERİ İŞLEME
# -------------------------------

def read_csv_advanced(uploaded_file):
    """Gelişmiş CSV okuma fonksiyonu"""
    try:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding='iso-8859-9')
        except Exception as e:
            logger.warning(f"Standart encoding başarısız, alternatif deneniyor: {e}")
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            delimiters = [',', ';', '\t', '|']
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
            return pd.read_csv(io.StringIO(content), delimiter=',')
    except Exception as e:
        logger.error(f"CSV okuma hatası: {e}", exc_info=True)
        raise

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Kolon isimlerini standardize et"""
    if df.empty:
        return df
    df.columns = df.columns.str.strip().str.lower()
    df.columns = df.columns.str.replace('[^a-z0-9_]', '_', regex=True)
    return df

def safe_numeric_conversion(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Güvenli numeric dönüşüm"""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
            
            # Özel kurallar
            if col == 'haftalik_satis':
                df[col] = df[col].clip(lower=Config.MIN_WEEKLY_SALES)
            else:
                df[col] = df[col].clip(lower=0)
    
    return df

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame memory kullanımını optimize et"""
    try:
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].astype('float32')
        
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].max() < 2147483647:  # int32 max
                df[col] = df[col].astype('int32')
        
        for col in df.select_dtypes(include=['object']).columns:
            num_unique = df[col].nunique()
            if num_unique / len(df) < 0.5:
                df[col] = df[col].astype('category')
        
        logger.info(f"DataFrame memory optimizasyonu tamamlandı")
    except Exception as e:
        logger.warning(f"Memory optimizasyonu hatası (devam ediliyor): {e}")
    
    return df

def validate_required_columns(df: pd.DataFrame, required_cols: List[str], file_name: str) -> bool:
    """Zorunlu kolonları kontrol et"""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        error_msg = f"{file_name} dosyasında eksik kolonlar: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return True

# -------------------------------
# YARDIMCI FONKSIYONLAR - HESAPLAMA
# -------------------------------

def calculate_urun_cover(haftalik_satis: float, mevcut_stok: float, yolda: float = 0) -> float:
    """
    Ürün cover'ını hesapla
    
    İŞ MANTIĞI:
    - Cover = mevcut_stok / haftalik_satis
    - YOLDA stoğu dahil ETMİYORUZ (mağazada henüz yok)
    - İhtiyaç hesabında ise yolda stoğu ekleyeceğiz
    """
    try:
        haftalik_satis = float(haftalik_satis) if haftalik_satis else 0
        mevcut_stok = float(mevcut_stok) if mevcut_stok else 0
        
        if haftalik_satis <= 0:
            return Config.DEFAULT_COVER
        
        if mevcut_stok <= 0:
            return 0
        
        cover = mevcut_stok / haftalik_satis
        return round(float(cover), 2)
        
    except (TypeError, ValueError) as e:
        logger.error(f"Cover hesaplama hatası: {e}")
        return Config.DEFAULT_COVER

def get_cover_grubu_adi(cover_value: float, cover_gruplari: List[Dict]) -> str:
    """Cover değerine göre grup adını bul"""
    try:
        cover_value = float(cover_value)
        for grup in cover_gruplari:
            if grup['min'] <= cover_value <= grup['max']:
                return grup['etiket']
        return "20+"
    except Exception as e:
        logger.debug(f"Cover grup belirleme hatası: {e}")
        return "20+"

def safe_get_carpan(magaza_cover_grubu: str, urun_cover_grubu: str) -> float:
    """Güvenli çarpan alma (Sevkiyat - TUR 1)"""
    try:
        carpan_matrisi = st.session_state.get('carpan_matrisi', {})
        
        if not carpan_matrisi:
            logger.warning("Çarpan matrisi boş, default 1.0 kullanılıyor")
            return Config.DEFAULT_CARPAN
        
        if magaza_cover_grubu not in carpan_matrisi:
            logger.debug(f"Mağaza grubu bulunamadı: {magaza_cover_grubu}")
            return Config.DEFAULT_CARPAN
        
        return carpan_matrisi[magaza_cover_grubu].get(urun_cover_grubu, Config.DEFAULT_CARPAN)
        
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Çarpan alma hatası: {e}", exc_info=True)
        return Config.DEFAULT_CARPAN

def safe_get_min_carpan(magaza_cover_grubu: str, urun_cover_grubu: str) -> float:
    """Min tamamlama çarpanını güvenli al (TUR 2)"""
    try:
        min_matrisi = st.session_state.get('min_tamamlama_matrisi', {})
        
        if not min_matrisi:
            logger.warning("Min tamamlama matrisi boş, default 0.0 kullanılıyor")
            return 0.0
        
        if magaza_cover_grubu not in min_matrisi:
            logger.debug(f"Min matrisinde mağaza grubu bulunamadı: {magaza_cover_grubu}")
            return 0.0
        
        return min_matrisi[magaza_cover_grubu].get(urun_cover_grubu, 0.0)
        
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f"Min çarpanı alma hatası: {e}", exc_info=True)
        return 0.0

# -------------------------------
# ALIM SİPARİŞ İHTİYACI HESAPLAMA
# -------------------------------

def calculate_purchase_need(sevk_df: pd.DataFrame, total_sevk: pd.DataFrame, 
                           original_sevkiyat_df: pd.DataFrame, depo_stok_df: pd.DataFrame) -> pd.DataFrame:
    """
    Karşılanamayan ihtiyaçları hesapla ve alım matrisi ile genişlet
    """
    try:
        if original_sevkiyat_df.empty:
            logger.warning("Orijinal sevkiyat verisi boş, alım hesaplanamıyor")
            return pd.DataFrame()
        
        # Orijinal sevkiyat verisini kopyala
        sevkiyat_df = original_sevkiyat_df.copy()
        
        # Sevkiyat miktarını birleştir
        if not sevk_df.empty and 'sevk_miktar' in sevk_df.columns:
            sevk_toplam = sevk_df.groupby(['depo_id', 'magaza_id', 'urun_id'])['sevk_miktar'].sum().reset_index()
            sevkiyat_df = pd.merge(
                sevkiyat_df,
                sevk_toplam,
                on=['depo_id', 'magaza_id', 'urun_id'],
                how='left'
            )
            sevkiyat_df['sevk_miktar'] = sevkiyat_df['sevk_miktar'].fillna(0)
        else:
            sevkiyat_df['sevk_miktar'] = 0
        
        # İhtiyaç hesapla (eğer yoksa)
        if 'ihtiyac' not in sevkiyat_df.columns:
            sevkiyat_df['ihtiyac'] = (
                (sevkiyat_df['haftalik_satis'] * sevkiyat_df.get('hedef_hafta', 4)) - 
                (sevkiyat_df['mevcut_stok'] + sevkiyat_df.get('yolda', 0))
            ).clip(lower=0)
        
        # Kalan ihtiyaç = ihtiyaç - sevk_miktar
        sevkiyat_df["kalan_ihtiyac"] = (sevkiyat_df["ihtiyac"] - sevkiyat_df["sevk_miktar"]).clip(lower=0)
        
        # Depo stok bilgilerini ekle
        if not depo_stok_df.empty:
            depo_stok_toplam = depo_stok_df.groupby(['depo_id', 'urun_id'])['depo_stok'].sum().reset_index()
            sevkiyat_df = pd.merge(
                sevkiyat_df,
                depo_stok_toplam,
                on=['depo_id', 'urun_id'],
                how='left'
            )
            sevkiyat_df['depo_stok'] = sevkiyat_df['depo_stok'].fillna(0)
        else:
            sevkiyat_df['depo_stok'] = 0

        # Karşılanamayan ve depoda stok olmayanları filtrele
        alim_siparis_df = sevkiyat_df[
            (sevkiyat_df["kalan_ihtiyac"] > 0) & (sevkiyat_df["depo_stok"] <= 0)
        ].copy()

        if alim_siparis_df.empty:
            logger.info("Alım ihtiyacı bulunmamaktadır")
            st.info("ℹ️ Alım ihtiyacı bulunmamaktadır.")
            return pd.DataFrame()

        # ALIM MATRİSİ İLE ÇARPAN UYGULA
        def get_alim_carpan(magaza_cover_grubu: str, urun_cover_grubu: str) -> float:
            """Alım matrısinden çarpan al"""
            try:
                alim_matrisi = st.session_state.get('alim_carpan_matrisi', {})
                
                if not alim_matrisi:
                    logger.warning("Alım matrisi boş, default 1.0 kullanılıyor")
                    return 1.0
                
                if magaza_cover_grubu not in alim_matrisi:
                    logger.debug(f"Alım matrisinde mağaza grubu bulunamadı: {magaza_cover_grubu}")
                    return 1.0
                
                return alim_matrisi[magaza_cover_grubu].get(urun_cover_grubu, 1.0)
                
            except Exception as e:
                logger.error(f"Alım çarpanı alma hatası: {e}")
                return 1.0
        
        # Cover grupları yoksa ekle
        if 'magaza_cover_grubu' not in alim_siparis_df.columns:
            alim_siparis_df['magaza_cover_grubu'] = '0-4'
        if 'urun_cover_grubu' not in alim_siparis_df.columns:
            alim_siparis_df['urun_cover_grubu'] = '0-4'
        
        # Alım çarpanını uygula
        alim_siparis_df['alim_carpan'] = alim_siparis_df.apply(
            lambda row: get_alim_carpan(
                row.get('magaza_cover_grubu', '0-4'),
                row.get('urun_cover_grubu', '0-4')
            ), axis=1
        )
        
        # Alım miktarı = kalan ihtiyaç × alım çarpanı
        alim_siparis_df['alim_siparis_miktari'] = (
            alim_siparis_df['kalan_ihtiyac'] * alim_siparis_df['alim_carpan']
        ).clip(lower=0)

        # Ürün bazında toplam alım siparişi
        alim_siparis_toplam = alim_siparis_df.groupby(
            ["depo_id", "urun_id", "klasmankod"], as_index=False
        ).agg({
            'alim_siparis_miktari': 'sum',
            'kalan_ihtiyac': 'sum',
            'ihtiyac': 'sum',
            'depo_stok': 'first',
            'haftalik_satis': 'mean',
            'alim_carpan': 'mean',
            'magaza_cover_grubu': lambda x: x.mode()[0] if len(x) > 0 else '0-4',
            'urun_cover_grubu': lambda x: x.mode()[0] if len(x) > 0 else '0-4'
        })

        # Ürün adını ekle
        if 'urunler_df' in st.session_state and not st.session_state.urunler_df.empty:
            urunler_df = st.session_state.urunler_df.copy()
            urunler_df['urun_id'] = urunler_df['urun_id'].astype(str).str.strip()
            alim_siparis_toplam['urun_id'] = alim_siparis_toplam['urun_id'].astype(str).str.strip()
            if 'urun_adi' in urunler_df.columns:
                alim_siparis_toplam = pd.merge(
                    alim_siparis_toplam,
                    urunler_df[['urun_id', 'urun_adi']],
                    on='urun_id',
                    how='left'
                )
        
        if 'urun_adi' not in alim_siparis_toplam.columns:
            alim_siparis_toplam['urun_adi'] = "Ürün " + alim_siparis_toplam['urun_id'].astype(str)
        
        # Cover bilgilerini ekle
        alim_siparis_toplam['toplam_ihtiyac_cover'] = (
            alim_siparis_toplam['alim_siparis_miktari'] / alim_siparis_toplam['haftalik_satis']
        ).round(1)
        
        # Sıralama
        alim_siparis_toplam = alim_siparis_toplam.sort_values('alim_siparis_miktari', ascending=False)
        
        logger.info(f"Alım ihtiyacı hesaplandı: {len(alim_siparis_toplam)} ürün, toplam {alim_siparis_toplam['alim_siparis_miktari'].sum():,.0f} adet")
        
        return alim_siparis_toplam
    
    except Exception as e:
        st.error(f"Alım ihtiyacı hesaplanırken hata: {str(e)}")
        logger.error(f"Alım ihtiyacı hesaplama hatası: {e}", exc_info=True)
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

# -------------------------------
# COVER GRUPLARI VE MATRİS YÖNETİMİ
# -------------------------------

def initialize_session_state():
    """Session state'i başlat - 3 MATRİS + WIZARD"""
    # Wizard state
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    
    if "cover_gruplari" not in st.session_state:
        st.session_state.cover_gruplari = Config.DEFAULT_COVER_GROUPS.copy()
    
    if "carpan_matrisi" not in st.session_state:
        st.session_state.carpan_matrisi = Config.DEFAULT_SEVK_MATRIX.copy()
    
    if "alim_carpan_matrisi" not in st.session_state:
        st.session_state.alim_carpan_matrisi = Config.DEFAULT_ALIM_MATRIX.copy()
    
    # YENİ: Min tamamlama matrisi
    if "min_tamamlama_matrisi" not in st.session_state:
        st.session_state.min_tamamlama_matrisi = Config.DEFAULT_MIN_TAMAMLAMA_MATRIX.copy()
    
    if "cover_gruplari_edited" not in st.session_state:
        st.session_state.cover_gruplari_edited = st.session_state.cover_gruplari.copy()
    
    if "carpan_matrisi_edited" not in st.session_state:
        st.session_state.carpan_matrisi_edited = st.session_state.carpan_matrisi.copy()
    
    if "alim_carpan_matrisi_edited" not in st.session_state:
        st.session_state.alim_carpan_matrisi_edited = st.session_state.alim_carpan_matrisi.copy()
    
    # YENİ: Min tamamlama edited
    if "min_tamamlama_matrisi_edited" not in st.session_state:
        st.session_state.min_tamamlama_matrisi_edited = st.session_state.min_tamamlama_matrisi.copy()

def show_carpan_matrix_table(matrix_data: Dict, matrix_type: str, color_scheme: str = "sevk"):
    """Çarpan matrisini renkli tablo olarak göster - 3 MATRİS DESTEĞİ"""
    
    cover_gruplari = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
    
    # DataFrame oluştur
    default_value = 1.0 if color_scheme != "min_tamamlama" else 0.0
    df = pd.DataFrame(matrix_data).T
    df = df.reindex(columns=cover_gruplari, index=cover_gruplari, fill_value=default_value)
    
    st.write(f"**{matrix_type} Çarpan Matrisi**")
    
    # Renklendirme fonksiyonu
    def color_cell(val):
        try:
            val = float(val)
            if color_scheme == "sevk":
                if val >= 1.1:
                    return 'background-color: #4ade80; color: black; font-weight: bold'
                elif val >= 0.9:
                    return 'background-color: #fbbf24; color: black'
                elif val > 0:
                    return 'background-color: #60a5fa; color: white'
                else:
                    return 'background-color: #1f2937; color: white'
            elif color_scheme == "min_tamamlama":
                if val >= 1.0:
                    return 'background-color: #4ade80; color: black; font-weight: bold'
                elif val > 0:
                    return 'background-color: #fbbf24; color: black'
                else:
                    return 'background-color: #1f2937; color: white'
            else:  # alim
                if val >= 1.2:
                    return 'background-color: #4ade80; color: black; font-weight: bold'
                elif val >= 1.0:
                    return 'background-color: #fbbf24; color: black'
                elif val > 0:
                    return 'background-color: #60a5fa; color: white'
                else:
                    return 'background-color: #1f2937; color: white'
        except:
            return ''
    
    # Legend
    if color_scheme == "sevk":
        st.caption("🟢 Yüksek öncelik (≥1.1) | 🟡 Normal (0.9-1.1) | 🔵 Düşük öncelik (>0) | ⚫ Sevk yok (0)")
    elif color_scheme == "min_tamamlama":
        st.caption("🟢 Tamamla (≥1.0) | 🟡 Düşük öncelik (>0) | ⚫ Tamamlama yapma (0)")
    else:
        st.caption("🟢 Yüksek alım (≥1.2) | 🟡 Normal alım (1.0-1.2) | 🔵 Düşük alım (>0) | ⚫ Alım yok (0)")
    
    # Formatla ve göster
    styled_df = df.style\
        .format("{:.2f}")\
        .applymap(color_cell)\
        .set_properties(**{
            'text-align': 'center',
            'font-size': '14px',
            'padding': '8px'
        })
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Açıklama
    with st.expander("ℹ️ Matris Nasıl Okunur?"):
        example_mag = cover_gruplari[0]
        example_urun = cover_gruplari[1] if len(cover_gruplari) > 1 else cover_gruplari[0]
        example_carpan = df.loc[example_mag, example_urun] if example_mag in df.index and example_urun in df.columns else 'N/A'
        
        st.markdown(f"""
        **Satırlar**: Mağaza cover grupları  
        **Sütunlar**: Ürün cover grupları  
        
        **Örnek**: Mağaza **{example_mag}** × Ürün **{example_urun}** → Çarpan: **{example_carpan}**
        """)
        
        if color_scheme == "sevk":
            st.markdown("""
            **Sevkiyat Matrisi (TUR 1):**
            - İhtiyaç × Sevkiyat Çarpanı = Sevk Miktarı
            - Yüksek çarpan = Daha fazla gönder
            """)
        elif color_scheme == "min_tamamlama":
            st.markdown("""
            **Min Tamamlama Matrisi (TUR 2):**
            - Eksik Min × Min Çarpan = Sevk Miktarı
            - Çarpan 0 = Tamamlama yapma
            """)
        else:
            st.markdown("""
            **Alım Matrisi:**
            - Kalan İhtiyaç × Alım Çarpanı = Alım Miktarı
            """)

def manage_cover_groups_and_matrix():
    """Cover grupları ve matris yönetimi - 3 MATRİS"""
    st.header("⚙️ Parametre Ayarları")
    
    initialize_session_state()

    # KPI Değerleri
    st.subheader("🎯 KPI & Varsayılan Değerler")
    st.info("⚠️ Bu değerler SADECE KPI.csv yüklenmediğinde kullanılır")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        default_hedef_hafta = st.slider("Varsayılan Hedef Hafta", 1, 12, 4, key="hedef_hafta_slider")
    with col2:
        default_min_adet = st.slider("Varsayılan Min Adet", 0, 100, 3, key="min_adet_slider")
    with col3:
        default_maks_adet = st.slider("Varsayılan Maks Adet", 0, 200, 20, key="maks_adet_slider")
    
    st.markdown("---")
    
    # Cover Grupları
    st.subheader("📈 Cover Grupları")
    st.info("Mağaza ve ürün cover değerlerinin gruplandırılması")
    
    current_df = pd.DataFrame(st.session_state.cover_gruplari_edited)
    
    edited_df = st.data_editor(
        current_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "min": st.column_config.NumberColumn("Min Cover", min_value=0, max_value=1000, step=1),
            "max": st.column_config.NumberColumn("Max Cover", min_value=0, max_value=1000, step=1),
            "etiket": st.column_config.TextColumn("Etiket", width="medium")
        },
        key="cover_gruplari_editor"
    )
    
    # Cover grupları değişince matrisleri güncelle
    if not edited_df.equals(current_df):
        st.session_state.cover_gruplari_edited = edited_df.to_dict('records')
        
        new_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
        
        # 3 matris için yeni değerler
        new_matrix = {}
        new_alim_matrix = {}
        new_min_matrix = {}
        
        for mag in new_etiketler:
            new_matrix[mag] = {}
            new_alim_matrix[mag] = {}
            new_min_matrix[mag] = {}
            
            for urun in new_etiketler:
                # Sevkiyat
                if mag in st.session_state.carpan_matrisi_edited and urun in st.session_state.carpan_matrisi_edited[mag]:
                    new_matrix[mag][urun] = st.session_state.carpan_matrisi_edited[mag][urun]
                else:
                    try:
                        mag_idx = new_etiketler.index(mag)
                        urun_idx = new_etiketler.index(urun)
                        distance = abs(mag_idx - urun_idx)
                        new_matrix[mag][urun] = max(0.05, 1.2 - distance * 0.2)
                    except:
                        new_matrix[mag][urun] = 1.0
                
                # Alım
                if mag in st.session_state.alim_carpan_matrisi_edited and urun in st.session_state.alim_carpan_matrisi_edited[mag]:
                    new_alim_matrix[mag][urun] = st.session_state.alim_carpan_matrisi_edited[mag][urun]
                else:
                    try:
                        mag_idx = new_etiketler.index(mag)
                        urun_idx = new_etiketler.index(urun)
                        distance = abs(mag_idx - urun_idx)
                        new_alim_matrix[mag][urun] = max(0.1, 1.5 - distance * 0.2)
                    except:
                        new_alim_matrix[mag][urun] = 1.0
                
                # Min tamamlama
                if mag in st.session_state.min_tamamlama_matrisi_edited and urun in st.session_state.min_tamamlama_matrisi_edited[mag]:
                    new_min_matrix[mag][urun] = st.session_state.min_tamamlama_matrisi_edited[mag][urun]
                else:
                    try:
                        mag_idx = new_etiketler.index(mag)
                        urun_idx = new_etiketler.index(urun)
                        if mag_idx <= 2 and urun_idx <= 2:
                            distance = abs(mag_idx - urun_idx)
                            new_min_matrix[mag][urun] = max(0.8, 1.2 - distance * 0.1)
                        else:
                            new_min_matrix[mag][urun] = 0.0
                    except:
                        new_min_matrix[mag][urun] = 0.0
        
        st.session_state.carpan_matrisi_edited = new_matrix
        st.session_state.alim_carpan_matrisi_edited = new_alim_matrix
        st.session_state.min_tamamlama_matrisi_edited = new_min_matrix
        st.success("✅ Cover grupları güncellendi! 3 matris yenilendi.")
        st.rerun()
    
    st.markdown("---")
    
    # 3 Matris Düzenleme
    tab1, tab2, tab3 = st.tabs(["🚚 Sevkiyat (TUR 1)", "🔧 Min Tamamlama (TUR 2)", "🛒 Alım Matrisi"])
    
    cover_gruplari_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
    
    # TAB 1: Sevkiyat
    with tab1:
        st.subheader("🎯 Sevkiyat Çarpan Matrisi (TUR 1)")
        st.info("⚠️ İhtiyaç × Çarpan = Sevk Miktarı")
        
        matrix_data = {}
        for mag in cover_gruplari_etiketler:
            matrix_data[mag] = {}
            for urun in cover_gruplari_etiketler:
                try:
                    matrix_data[mag][urun] = st.session_state.carpan_matrisi_edited.get(mag, {}).get(urun, 1.0)
                except:
                    matrix_data[mag][urun] = 1.0
        
        matrix_df = pd.DataFrame(matrix_data)
        
        for mag in cover_gruplari_etiketler:
            if mag not in matrix_df.index:
                matrix_df.loc[mag] = {urun: 1.0 for urun in cover_gruplari_etiketler}
            for urun in cover_gruplari_etiketler:
                if pd.isna(matrix_df.loc[mag, urun]):
                    matrix_df.loc[mag, urun] = 1.0
        
        matrix_df = matrix_df.reindex(columns=cover_gruplari_etiketler, index=cover_gruplari_etiketler)
        
        matrix_edited = st.data_editor(
            matrix_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                format="%.2f", min_value=0.0, max_value=2.0, step=0.1
            ) for col in matrix_df.columns},
            key="carpan_matrisi_editor"
        )
        
        if not matrix_edited.equals(matrix_df):
            st.session_state.carpan_matrisi_edited = matrix_edited.to_dict()
            st.success("✅ Sevkiyat matrisi güncellendi!")
            st.rerun()
    
    # TAB 2: Min Tamamlama
    with tab2:
        st.subheader("🔧 Min Tamamlama Çarpan Matrisi (TUR 2)")
        st.info("🎯 Eksik Min × Çarpan = Sevk Miktarı")
        
        st.warning("""
        ⚠️ **Önemli:**
        - Çarpan 0 = Tamamlama yapma
        - **Eski:** `if cover >= 12: skip`
        - **Yeni:** `if min_carpan == 0: skip`
        """)
        
        min_matrix_data = {}
        for mag in cover_gruplari_etiketler:
            min_matrix_data[mag] = {}
            for urun in cover_gruplari_etiketler:
                try:
                    min_matrix_data[mag][urun] = st.session_state.min_tamamlama_matrisi_edited.get(mag, {}).get(urun, 0.0)
                except:
                    min_matrix_data[mag][urun] = 0.0
        
        min_matrix_df = pd.DataFrame(min_matrix_data)
        
        for mag in cover_gruplari_etiketler:
            if mag not in min_matrix_df.index:
                min_matrix_df.loc[mag] = {urun: 0.0 for urun in cover_gruplari_etiketler}
            for urun in cover_gruplari_etiketler:
                if pd.isna(min_matrix_df.loc[mag, urun]):
                    min_matrix_df.loc[mag, urun] = 0.0
        
        min_matrix_df = min_matrix_df.reindex(columns=cover_gruplari_etiketler, index=cover_gruplari_etiketler)
        
        min_matrix_edited = st.data_editor(
            min_matrix_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                format="%.2f", min_value=0.0, max_value=2.0, step=0.1
            ) for col in min_matrix_df.columns},
            key="min_tamamlama_matrisi_editor"
        )
        
        if not min_matrix_edited.equals(min_matrix_df):
            st.session_state.min_tamamlama_matrisi_edited = min_matrix_edited.to_dict()
            st.success("✅ Min tamamlama matrisi güncellendi!")
            st.rerun()
    
    # TAB 3: Alım
    with tab3:
        st.subheader("🛒 Alım Çarpan Matrisi")
        st.info("💰 Kalan İhtiyaç × Çarpan = Alım Miktarı")
        
        alim_matrix_data = {}
        for mag in cover_gruplari_etiketler:
            alim_matrix_data[mag] = {}
            for urun in cover_gruplari_etiketler:
                try:
                    alim_matrix_data[mag][urun] = st.session_state.alim_carpan_matrisi_edited.get(mag, {}).get(urun, 1.0)
                except:
                    alim_matrix_data[mag][urun] = 1.0
        
        alim_matrix_df = pd.DataFrame(alim_matrix_data)
        
        for mag in cover_gruplari_etiketler:
            if mag not in alim_matrix_df.index:
                alim_matrix_df.loc[mag] = {urun: 1.0 for urun in cover_gruplari_etiketler}
            for urun in cover_gruplari_etiketler:
                if pd.isna(alim_matrix_df.loc[mag, urun]):
                    alim_matrix_df.loc[mag, urun] = 1.0
        
        alim_matrix_df = alim_matrix_df.reindex(columns=cover_gruplari_etiketler, index=cover_gruplari_etiketler)
        
        alim_matrix_edited = st.data_editor(
            alim_matrix_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                format="%.2f", min_value=0.0, max_value=3.0, step=0.1
            ) for col in alim_matrix_df.columns},
            key="alim_carpan_matrisi_editor"
        )
        
        if not alim_matrix_edited.equals(alim_matrix_df):
            st.session_state.alim_carpan_matrisi_edited = alim_matrix_edited.to_dict()
            st.success("✅ Alım matrisi güncellendi!")
            st.rerun()
    
    # Görselleştirme
    st.markdown("---")
    st.subheader("📊 Matris Görünümleri")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["🚚 Sevkiyat", "🔧 Min Tamamlama", "🛒 Alım"])
    
    with viz_tab1:
        show_carpan_matrix_table(st.session_state.carpan_matrisi_edited, "Sevkiyat (TUR 1)", "sevk")
    
    with viz_tab2:
        show_carpan_matrix_table(st.session_state.min_tamamlama_matrisi_edited, "Min Tamamlama (TUR 2)", "min_tamamlama")
    
    with viz_tab3:
        show_carpan_matrix_table(st.session_state.alim_carpan_matrisi_edited, "Alım", "alim")
    
    # Kaydetme
    st.markdown("---")
    st.subheader("💾 Ayarları Kaydet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True, key="save_all"):
            st.session_state.cover_gruplari = st.session_state.cover_gruplari_edited.copy()
            st.session_state.carpan_matrisi = st.session_state.carpan_matrisi_edited.copy()
            st.session_state.alim_carpan_matrisi = st.session_state.alim_carpan_matrisi_edited.copy()
            st.session_state.min_tamamlama_matrisi = st.session_state.min_tamamlama_matrisi_edited.copy()
            
            logger.info("3 matris kaydedildi")
            st.success("✅ Tüm ayarlar kaydedildi! (3 matris)")
    
    with col2:
        if st.button("🔄 Varsayılanlara Dön", use_container_width=True, key="reset_defaults"):
            st.session_state.cover_gruplari = Config.DEFAULT_COVER_GROUPS.copy()
            st.session_state.carpan_matrisi = Config.DEFAULT_SEVK_MATRIX.copy()
            st.session_state.alim_carpan_matrisi = Config.DEFAULT_ALIM_MATRIX.copy()
            st.session_state.min_tamamlama_matrisi = Config.DEFAULT_MIN_TAMAMLAMA_MATRIX.copy()
            st.session_state.cover_gruplari_edited = Config.DEFAULT_COVER_GROUPS.copy()
            st.session_state.carpan_matrisi_edited = Config.DEFAULT_SEVK_MATRIX.copy()
            st.session_state.alim_carpan_matrisi_edited = Config.DEFAULT_ALIM_MATRIX.copy()
            st.session_state.min_tamamlama_matrisi_edited = Config.DEFAULT_MIN_TAMAMLAMA_MATRIX.copy()
            
            logger.info("Varsayılanlara dönüldü")
            st.success("✅ Varsayılan değerlere dönüldü!")
            st.rerun()
    
    return default_hedef_hafta, default_min_adet, default_maks_adet, edited_df
