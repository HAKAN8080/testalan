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
    """Session state'i başlat - 3 MATRİS"""
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
            - **Eski:** `if cover >= 12: skip`
            - **Yeni:** `if min_carpan == 0: skip`
            """)
        else:
            st.markdown("""
            **Alım Matrisi:**
            - Kalan İhtiyaç × Alım Çarpanı = Alım Miktarı
            """)

def show_current_settings_user_friendly():
    """Geçerli ayarları kullanıcı dostu göster - 3 MATRİS"""
    
    st.markdown("---")
    st.subheader("📋 Geçerli Parametre Ayarları")
    
    # 1. Cover Grupları
    with st.expander("📊 Cover Grupları", expanded=True):
        cover_df = pd.DataFrame(st.session_state.cover_gruplari)
        cover_df.columns = ['Min Cover', 'Max Cover', 'Grup Adı']
        
        st.dataframe(
            cover_df.style.set_properties(**{
                'background-color': '#f0f9ff',
                'color': '#1e40af',
                'border': '1px solid #3b82f6'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"✅ Toplam **{len(cover_df)}** grup tanımlı")
    
    # 2. Sevkiyat Matrisi
    with st.expander("🚚 Sevkiyat Matrisi Özeti (TUR 1)", expanded=True):
        carpan_matrisi = st.session_state.carpan_matrisi
        
        all_values = [
            val 
            for grup_vals in carpan_matrisi.values() 
            for val in grup_vals.values()
        ]
        
        if all_values:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("En Yüksek Çarpan", f"{max(all_values):.2f}")
            col2.metric("En Düşük Çarpan", f"{min(all_values):.2f}")
            col3.metric("Ortalama Çarpan", f"{sum(all_values)/len(all_values):.2f}")
            col4.metric("Sıfır Sevk Sayısı", sum(1 for v in all_values if v == 0))
    
    # 3. Min Tamamlama Matrisi
    with st.expander("🔧 Min Tamamlama Matrisi Özeti (TUR 2)", expanded=True):
        min_matrisi = st.session_state.min_tamamlama_matrisi
        
        all_values = [
            val 
            for grup_vals in min_matrisi.values() 
            for val in grup_vals.values()
        ]
        
        if all_values:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("En Yüksek Çarpan", f"{max(all_values):.2f}")
            col2.metric("En Düşük Çarpan", f"{min(all_values):.2f}")
            col3.metric("Ortalama Çarpan", f"{sum(all_values)/len(all_values):.2f}")
            col4.metric("Tamamlama Yok Sayısı", sum(1 for v in all_values if v == 0))
            
            st.info("💡 Bu matris TUR 2'de kullanılır. Çarpan 0 ise tamamlama yapılmaz.")
    
    # 4. Alım Matrisi
    with st.expander("🛒 Alım Matrisi Özeti", expanded=True):
        alim_matrisi = st.session_state.alim_carpan_matrisi
        
        all_values = [
            val 
            for grup_vals in alim_matrisi.values() 
            for val in grup_vals.values()
        ]
        
        if all_values:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("En Yüksek Çarpan", f"{max(all_values):.2f}")
            col2.metric("En Düşük Çarpan", f"{min(all_values):.2f}")
            col3.metric("Ortalama Çarpan", f"{sum(all_values)/len(all_values):.2f}")
            col4.metric("Sıfır Alım Sayısı", sum(1 for v in all_values if v == 0))
    
    # 5. KPI Değerleri
    with st.expander("🎯 Varsayılan KPI Değerleri", expanded=False):
        st.info("⚠️ Bu değerler sadece KPI.csv yüklenmediğinde kullanılır")
        
        kpi_df = pd.DataFrame([
            {'Parametre': 'Hedef Hafta', 'Değer': st.session_state.get('hedef_hafta_slider', 4), 'Birim': 'hafta'},
            {'Parametre': 'Min Adet', 'Değer': st.session_state.get('min_adet_slider', 3), 'Birim': 'adet'},
            {'Parametre': 'Maks Adet', 'Değer': st.session_state.get('maks_adet_slider', 20), 'Birim': 'adet'}
        ])
        
        st.dataframe(kpi_df, use_container_width=True, hide_index=True)
    
    # Özet
    st.success(f"""
    ✅ **Sistem Hazır - 3 Matris Aktif**  
    - {len(st.session_state.cover_gruplari)} cover grubu
    - Sevkiyat matrisi (TUR 1)
    - Min tamamlama matrisi (TUR 2)
    - Alım matrisi
    """)

def manage_cover_groups_and_matrix():
    """Cover grupları ve matris yönetimi - 3 MATRİS"""
    st.header("🔧 Parametre Ayarları")
    
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True, key="save_all"):
            st.session_state.cover_gruplari = st.session_state.cover_gruplari_edited.copy()
            st.session_state.carpan_matrisi = st.session_state.carpan_matrisi_edited.copy()
            st.session_state.alim_carpan_matrisi = st.session_state.alim_carpan_matrisi_edited.copy()
            st.session_state.min_tamamlama_matrisi = st.session_state.min_tamamlama_matrisi_edited.copy()
            
            logger.info("3 matris kaydedildi")
            st.success("✅ Tüm ayarlar kaydedildi! (3 matris)")
            st.rerun()
    
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
    
    with col3:
        if st.button("📊 Geçerli Ayarları Göster", use_container_width=True, key="show_current"):
            show_current_settings_user_friendly()
    
    return default_hedef_hafta, default_min_adet, default_maks_adet, edited_df

# -------------------------------
# DOSYA YÜKLEME
# -------------------------------

def create_file_upload_section():
    """Dosya yükleme bölümü"""
    st.header("📁 Veri Yükleme")
    
    with st.expander("📋 **Dosya Formatları**", expanded=True):
        st.markdown("""
        **Zorunlu Dosyalar:**
        - **Sevkiyat.csv**: depo_id, urun_id, magaza_id, haftalik_satis, mevcut_stok, yolda, klasmankod
        - **Depo_Stok.csv**: depo_id, urun_id, depo_stok
        
        **Opsiyonel Dosyalar:**
        - **Urunler.csv**: urun_id, urun_adi
        - **Magazalar.csv**: magaza_id, magaza_adi  
        - **Cover.csv**: magaza_id, cover 
        - **KPI.csv**: klasmankod, hedef_hafta, min_adet, maks_adet
        """)
    
    uploaded_files = st.file_uploader("**CSV dosyalarınızı seçin**", type=["csv"], accept_multiple_files=True)
    
    file_data = {}
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                df = read_csv_advanced(uploaded_file)
                file_data[uploaded_file.name] = df
                st.success(f"✅ {uploaded_file.name} - {len(df.columns)} kolon, {len(df)} satır")
                logger.info(f"Dosya yüklendi: {uploaded_file.name}")
                
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} okunamadı: {e}")
                logger.error(f"Dosya okuma hatası: {uploaded_file.name}, {e}")
    
    return file_data

# -------------------------------
# VERİ ÖN İŞLEME
# -------------------------------

def load_and_process_files(file_data: Dict) -> Tuple:
    """Dosyaları yükle"""
    sevk_df, depo_stok_df, urunler_df, magazalar_df, cover_df, kpi_df = None, None, None, None, None, None
    
    for name, df in file_data.items():
        name_lower = name.lower()
        if "sevkiyat" in name_lower:
            sevk_df = df.copy()
            st.info(f"📊 Sevkiyat: {len(sevk_df)} satır")
        elif "depo" in name_lower and "stok" in name_lower:
            depo_stok_df = df.copy()
            st.info(f"📦 Depo stok: {len(depo_stok_df)} satır")
        elif "urun" in name_lower:
            urunler_df = df.copy()
            st.info(f"🏷️ Ürünler: {len(urunler_df)} satır")
            st.session_state.urunler_df = urunler_df
        elif "magaza" in name_lower:
            magazalar_df = df.copy()
            st.info(f"🏪 Mağazalar: {len(magazalar_df)} satır")
            st.session_state.magazalar_df = magazalar_df
        elif "cover" in name_lower:
            cover_df = df.copy()
            st.info(f"📈 Cover: {len(cover_df)} satır")
        elif "kpi" in name_lower:
            kpi_df = df.copy()
            st.info(f"🎯 KPI: {len(kpi_df)} satır")
    
    if sevk_df is None or depo_stok_df is None:
        raise Exception("Zorunlu dosyalar eksik!")
    
    return sevk_df, depo_stok_df, urunler_df, magazalar_df, cover_df, kpi_df

def preprocess_sevkiyat_data(sevk_df: pd.DataFrame, cover_df: Optional[pd.DataFrame], 
                             kpi_df: Optional[pd.DataFrame], params: Dict) -> pd.DataFrame:
    """Sevkiyat verisini ön işle"""
    
    sevk_df = normalize_columns(sevk_df)
    validate_required_columns(sevk_df, Config.REQUIRED_SEVK_COLS, "Sevkiyat.csv")
    
    if 'yolda' not in sevk_df.columns:
        sevk_df['yolda'] = 0
    
    sevk_df = safe_numeric_conversion(sevk_df, Config.NUMERIC_COLUMNS)
    
    # Cover
    if cover_df is not None and not cover_df.empty:
        cover_df = normalize_columns(cover_df)
        if 'magaza_id' in cover_df.columns and 'cover' in cover_df.columns:
            cover_df = cover_df[['magaza_id', 'cover']].drop_duplicates()
            cover_df['magaza_id'] = cover_df['magaza_id'].astype(str).str.strip()
            sevk_df['magaza_id'] = sevk_df['magaza_id'].astype(str).str.strip()
            sevk_df = sevk_df.merge(cover_df, on='magaza_id', how='left')
            st.success("✅ Cover verileri eklendi")
        else:
            sevk_df['cover'] = Config.DEFAULT_COVER
    else:
        sevk_df['cover'] = Config.DEFAULT_COVER
    
    sevk_df['cover'] = pd.to_numeric(sevk_df['cover'], errors='coerce').fillna(Config.DEFAULT_COVER)
    
    # KPI
    kpi_loaded = False
    if kpi_df is not None and not kpi_df.empty:
        kpi_df = normalize_columns(kpi_df)
        if 'klasmankod' in kpi_df.columns:
            kpi_df['klasmankod'] = kpi_df['klasmankod'].astype(str).str.strip()
            sevk_df['klasmankod'] = sevk_df['klasmankod'].astype(str).str.strip()
            
            kpi_cols = ['klasmankod']
            for col in ['hedef_hafta', 'min_adet', 'maks_adet']:
                if col in kpi_df.columns:
                    kpi_cols.append(col)
            
            sevk_df = sevk_df.merge(kpi_df[kpi_cols], on='klasmankod', how='left')
            st.success("✅ KPI eklendi")
            kpi_loaded = True
    
    if not kpi_loaded:
        sevk_df['hedef_hafta'] = params['hedef_hafta']
        sevk_df['min_adet'] = params['min_adet']
        sevk_df['maks_adet'] = params['maks_adet']
    else:
        sevk_df['hedef_hafta'] = sevk_df['hedef_hafta'].fillna(params['hedef_hafta'])
        sevk_df['min_adet'] = sevk_df['min_adet'].fillna(params['min_adet'])
        sevk_df['maks_adet'] = sevk_df['maks_adet'].fillna(params['maks_adet'])
    
    return sevk_df

def calculate_covers_and_groups(sevk_df: pd.DataFrame, cover_gruplari: List[Dict]) -> pd.DataFrame:
    """Cover ve grupları hesapla"""
    
    sevk_df['urun_cover'] = sevk_df.apply(
        lambda row: calculate_urun_cover(
            row.get('haftalik_satis', 0), 
            row.get('mevcut_stok', 0), 
            row.get('yolda', 0)
        ), axis=1
    )
    
    sevk_df['magaza_cover_grubu'] = sevk_df['cover'].apply(
        lambda x: get_cover_grubu_adi(x, cover_gruplari)
    )
    sevk_df['urun_cover_grubu'] = sevk_df['urun_cover'].apply(
        lambda x: get_cover_grubu_adi(x, cover_gruplari)
    )
    
    return sevk_df

# -------------------------------
# ANA HESAPLAMA - 3 MATRİS DESTEKLİ
# -------------------------------

def calculate_shipment_optimized(file_data: Dict, params: Dict, cover_gruplari: List[Dict]) -> Tuple:
    """Ana sevkiyat hesaplama - 3 MATRİS"""
    
    # 1. Yükle
    sevk_df, depo_stok_df, urunler_df, magazalar_df, cover_df, kpi_df = load_and_process_files(file_data)
    
    original_sevkiyat_df = sevk_df.copy()
    
    # 2. Depo stok
    depo_stok_df = normalize_columns(depo_stok_df)
    validate_required_columns(depo_stok_df, Config.REQUIRED_DEPO_COLS, "Depo_Stok.csv")
    depo_stok_df = safe_numeric_conversion(depo_stok_df, ['depo_stok'])
    
    # 3. Sevkiyat ön işle
    sevk_df = preprocess_sevkiyat_data(sevk_df, cover_df, kpi_df, params)
    original_sevkiyat_df = preprocess_sevkiyat_data(original_sevkiyat_df, cover_df, kpi_df, params)
    
    # 4. Cover hesapla
    sevk_df = calculate_covers_and_groups(sevk_df, cover_gruplari)
    original_sevkiyat_df = calculate_covers_and_groups(original_sevkiyat_df, cover_gruplari)
    
    # 5. Filtrele
    df_filtered = sevk_df[sevk_df['cover'] <= Config.MAX_COVER_THRESHOLD].copy()
    st.info(f"ℹ️ Cover ≤ {Config.MAX_COVER_THRESHOLD}: {len(df_filtered)} satır işlenecek")
    
    # 6. İhtiyaç hesabı
    df_filtered["ihtiyac"] = (
        (df_filtered["haftalik_satis"] * df_filtered["hedef_hafta"]) - 
        (df_filtered["mevcut_stok"] + df_filtered["yolda"])
    ).clip(lower=0)
    
    original_sevkiyat_df["ihtiyac"] = (
        (original_sevkiyat_df["haftalik_satis"] * original_sevkiyat_df['hedef_hafta']) - 
        (original_sevkiyat_df["mevcut_stok"] + original_sevkiyat_df['yolda'])
    ).clip(lower=0)
    
    # 7. Sıralama
    df_sorted = df_filtered.sort_values(
        by=["urun_id", "urun_cover", "haftalik_satis"], 
        ascending=[True, True, False]
    ).copy()
    
    # 8. Memory optimize
    df_sorted = optimize_dataframe_memory(df_sorted)
    depo_stok_df = optimize_dataframe_memory(depo_stok_df)
    
    # 9. Sevkiyat hesaplama
    sevk_listesi = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    cover_gruplari_sirali = sorted(cover_gruplari, key=lambda x: x['min'])
    cover_gruplari_etiketler = [g['etiket'] for g in cover_gruplari_sirali]
    
    st.info(f"ℹ️ Cover grupları: {cover_gruplari_etiketler}")
    
    depo_urun_gruplari = list(df_sorted.groupby(["depo_id", "urun_id"]))
    total_groups = len(depo_urun_gruplari) * len(cover_gruplari_etiketler) * len(cover_gruplari_etiketler)
    processed_groups = 0
    
    # Ana döngü - 3 MATRİS
    for magaza_cover_grubu in cover_gruplari_etiketler:
        status_text.text(f"⏳ Mağaza {magaza_cover_grubu}...")
        magaza_grup_df = df_sorted[df_sorted["magaza_cover_grubu"] == magaza_cover_grubu]
        
        if magaza_grup_df.empty:
            processed_groups += len(depo_urun_gruplari) * len(cover_gruplari_etiketler)
            progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
            continue
        
        for urun_cover_grubu in cover_gruplari_etiketler:
            status_text.text(f"⏳ {magaza_cover_grubu} × {urun_cover_grubu}...")
            grup_df = magaza_grup_df[magaza_grup_df["urun_cover_grubu"] == urun_cover_grubu]
            
            if grup_df.empty:
                processed_groups += len(depo_urun_gruplari)
                progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                continue
            
            # Çarpanları al
            carpan = safe_get_carpan(magaza_cover_grubu, urun_cover_grubu)
            min_carpan = safe_get_min_carpan(magaza_cover_grubu, urun_cover_grubu)
            
            for (depo, urun), tum_grup in depo_urun_gruplari:
                grup = tum_grup[
                    (tum_grup["magaza_cover_grubu"] == magaza_cover_grubu) & 
                    (tum_grup["urun_cover_grubu"] == urun_cover_grubu)
                ]
                
                if grup.empty:
                    processed_groups += 1
                    progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                    continue
                
                # Depo stok
                stok_idx = (depo_stok_df["depo_id"] == depo) & (depo_stok_df["urun_id"] == urun)
                stok = int(depo_stok_df.loc[stok_idx, "depo_stok"].sum()) if stok_idx.any() else 0
                
                if stok <= 0:
                    processed_groups += 1
                    progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                    continue
                
                # TUR 1: İhtiyaç bazlı
                for _, row in grup.iterrows():
                    min_adet = row["min_adet"]
                    MAKS_SEVK = row["maks_adet"]
                    ihtiyac = row["ihtiyac"]
                    
                    ihtiyac_carpanli = ihtiyac * carpan
                    
                    sevk = int(min(ihtiyac_carpanli, stok, MAKS_SEVK)) if stok > 0 and ihtiyac_carpanli > 0 else 0
                    
                    if sevk > 0:
                        stok -= sevk
                        sevk_listesi.append({
                            "depo_id": depo, "magaza_id": row["magaza_id"], "urun_id": urun,
                            "klasmankod": row["klasmankod"], "tur": 1, 
                            "magaza_cover_grubu": magaza_cover_grubu,
                            "urun_cover_grubu": urun_cover_grubu,
                            "ihtiyac": ihtiyac, "ihtiyac_carpanli": ihtiyac_carpanli, 
                            "carpan": carpan, "min_carpan": min_carpan, "yolda": row["yolda"], 
                            "sevk_miktar": sevk,
                            "haftalik_satis": row["haftalik_satis"], "mevcut_stok": row["mevcut_stok"],
                            "cover": row["cover"], "urun_cover": row["urun_cover"],
                            "min_adet": min_adet, "maks_adet": MAKS_SEVK, "hedef_hafta": row["hedef_hafta"]
                        })
                
                # TUR 2: Min tamamlama - MATRİS TABANLI (YENİ)
                if stok > 0 and min_carpan > 0:  # ← MIN ÇARPAN KONTROLÜ
                    for _, row in grup.iterrows():
                        min_adet = row["min_adet"]
                        MAKS_SEVK = row["maks_adet"]
                        mevcut = row["mevcut_stok"] + row["yolda"]
                        eksik_min = max(0, min_adet - mevcut)
                        
                        # Min çarpanı uygula
                        eksik_min_carpanli = eksik_min * min_carpan
                        
                        sevk2 = int(min(eksik_min_carpanli, stok, MAKS_SEVK)) if eksik_min_carpanli > 0 else 0
                        
                        if sevk2 > 0:
                            stok -= sevk2
                            sevk_listesi.append({
                                "depo_id": depo, "magaza_id": row["magaza_id"], "urun_id": urun,
                                "klasmankod": row["klasmankod"], "tur": 2,
                                "magaza_cover_grubu": magaza_cover_grubu,
                                "urun_cover_grubu": urun_cover_grubu,
                                "ihtiyac": row["ihtiyac"], "ihtiyac_carpanli": row["ihtiyac"] * carpan,
                                "carpan": carpan, "min_carpan": min_carpan, "yolda": row["yolda"], 
                                "sevk_miktar": sevk2,
                                "haftalik_satis": row["haftalik_satis"], "mevcut_stok": row["mevcut_stok"],
                                "cover": row["cover"], "urun_cover": row["urun_cover"],
                                "min_adet": min_adet, "maks_adet": MAKS_SEVK, "hedef_hafta": row["hedef_hafta"]
                            })
                
                # Depo güncelle
                if stok_idx.any():
                    if stok_idx.sum() == 1:
                        depo_stok_df.loc[stok_idx, "depo_stok"] = stok
                    else:
                        first_match_idx = stok_idx.idxmax()
                        depo_stok_df.loc[first_match_idx, "depo_stok"] = stok
                
                processed_groups += 1
                progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
    
    progress_bar.progress(100)
    status_text.text("✅ Hesaplama tamamlandı")
    
    # Sonuçları birleştir
    if sevk_listesi:
        sevk_df_result = pd.DataFrame(sevk_listesi)
        
        total_sevk = sevk_df_result.groupby(
            ["depo_id", "magaza_id", "urun_id", "klasmankod", "magaza_cover_grubu", "urun_cover_grubu"], 
            as_index=False
        ).agg({
            "sevk_miktar": "sum", "yolda": "first", "haftalik_satis": "first",
            "ihtiyac": "first", "mevcut_stok": "first", "cover": "first",
            "urun_cover": "first", "carpan": "first", "min_carpan": "first",
            "min_adet": "first", "maks_adet": "first", "hedef_hafta": "first", "tur": "first"
        })
        
        min_tamamlama = sevk_df_result[sevk_df_result['tur'] == 2]['sevk_miktar'].sum()
        toplam_sevk = sevk_df_result['sevk_miktar'].sum()
        min_yuzde = (min_tamamlama / toplam_sevk * 100) if toplam_sevk > 0 else 0
        
        st.session_state.min_tamamlama = min_tamamlama
        st.session_state.min_yuzde = min_yuzde
        st.session_state.toplam_sevk = toplam_sevk
        st.session_state.sevk_df_result = sevk_df_result
        
        st.write(f"✅ Toplam: {toplam_sevk:,} adet | Min: {min_tamamlama:,} ({min_yuzde:.1f}%)")
        logger.info(f"Hesaplama OK: {toplam_sevk} adet")
        
    else:
        sevk_df_result = pd.DataFrame()
        total_sevk = pd.DataFrame()
        st.session_state.min_tamamlama = 0
        st.session_state.min_yuzde = 0
        st.session_state.toplam_sevk = 0
        st.session_state.sevk_df_result = pd.DataFrame()
        st.warning("⚠️ Sevkiyat yok!")
    
    return sevk_df_result, total_sevk, depo_stok_df, original_sevkiyat_df

# -------------------------------
# RAPORLAR - EKSİKSİZ
# -------------------------------

def show_reports():
    """Raporlar - TAM VERSİYON"""
    st.title("📊 Raporlar ve Analizler")
    
    if 'total_sevk' not in st.session_state or st.session_state.total_sevk.empty:
        st.warning("ℹ️ Henüz hesaplama yapılmadı.")
        return
    
    total_sevk = st.session_state.total_sevk.copy()
    sevk_df = st.session_state.get('sevk_df', pd.DataFrame())
    sevk_df_result = st.session_state.get('sevk_df_result', pd.DataFrame())
    original_sevkiyat_df = st.session_state.get('original_sevkiyat_df', pd.DataFrame())
    depo_stok_df = st.session_state.get('depo_stok_df', pd.DataFrame())
    magazalar_df = st.session_state.get('magazalar_df', pd.DataFrame())
    urunler_df = st.session_state.get('urunler_df', pd.DataFrame())
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Özet", "🏪 Mağaza", "📦 Ürün", 
        "🛒 Alım", "🎯 Matris", "📋 Detay"
    ])
    
    # TAB 1: Özet
    with tab1:
        st.subheader("📈 Özet Metrikler")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        col1.metric("Toplam Sevkiyat", f"{st.session_state.toplam_sevk:,}")
        col2.metric("Mağaza", total_sevk['magaza_id'].nunique())
        col3.metric("Ürün", total_sevk['urun_id'].nunique())
        col4.metric("Ort. Mağaza Cover", f"{total_sevk['cover'].mean():.1f}")
        col5.metric("Ort. Ürün Cover", f"{total_sevk['urun_cover'].mean():.1f}")
        col6.metric("Min %", f"{st.session_state.min_yuzde:.1f}%")
    
   # TAB 2: Mağaza Analizi - EKSİKSİZ
    with tab2:
        st.subheader("🏪 Mağaza Analizi")
        
        if not total_sevk.empty:
            # Mağaza bazlı özet
            magaza_analiz = total_sevk.groupby(['magaza_id', 'magaza_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'cover': 'first',
                'haftalik_satis': 'sum',
                'urun_id': 'nunique'
            }).reset_index()
            
            magaza_analiz.columns = ['magaza_id', 'magaza_cover_grubu', 'sevk_miktar', 
                                     'ihtiyac', 'cover', 'haftalik_satis', 'urun_cesidi']
            
            # Mağaza adı ekle
            if not magazalar_df.empty:
                magazalar_df_copy = magazalar_df.copy()
                magazalar_df_copy['magaza_id'] = magazalar_df_copy['magaza_id'].astype(str).str.strip()
                magaza_analiz['magaza_id'] = magaza_analiz['magaza_id'].astype(str).str.strip()
                if 'magaza_adi' in magazalar_df_copy.columns:
                    magaza_analiz = pd.merge(
                        magaza_analiz,
                        magazalar_df_copy[['magaza_id', 'magaza_adi']],
                        on='magaza_id',
                        how='left'
                    )
                    # Sütun sırasını düzenle
                    cols = ['magaza_id', 'magaza_adi'] + [col for col in magaza_analiz.columns if col not in ['magaza_id', 'magaza_adi']]
                    magaza_analiz = magaza_analiz[cols]
            
            # Hesaplamalar
            magaza_analiz['ihtiyac_karsilama_%'] = (
                (magaza_analiz['sevk_miktar'] / magaza_analiz['ihtiyac'] * 100)
                .fillna(0)
                .replace([np.inf, -np.inf], 0)
                .round(1)
            )
            
            magaza_analiz['urun_basi_sevk'] = (
                magaza_analiz['sevk_miktar'] / magaza_analiz['urun_cesidi']
            ).round(1)
            
            magaza_analiz['haftalik_cover'] = (
                magaza_analiz['sevk_miktar'] / magaza_analiz['haftalik_satis']
            ).fillna(0).round(1)
            
            # Sıralama
            magaza_analiz = magaza_analiz.sort_values('sevk_miktar', ascending=False)
            
            # Genel Özet
            st.write("**📊 Mağaza Özet İstatistikleri:**")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Toplam Mağaza", len(magaza_analiz))
            col2.metric("Ortalama Sevkiyat", f"{magaza_analiz['sevk_miktar'].mean():,.0f}")
            col3.metric("En Yüksek Sevkiyat", f"{magaza_analiz['sevk_miktar'].max():,.0f}")
            col4.metric("Ort. Cover", f"{magaza_analiz['cover'].mean():.1f}")
            
            st.markdown("---")
            
            # Filtreler
            st.write("**🔍 Filtreler:**")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                cover_grubu_filter = st.multiselect(
                    "Cover Grubu",
                    options=magaza_analiz['magaza_cover_grubu'].unique(),
                    default=None,
                    key="magaza_cover_filter"
                )
            
            with filter_col2:
                min_sevk_filter = st.number_input(
                    "Min Sevkiyat",
                    min_value=0,
                    value=0,
                    step=10,
                    key="min_sevk_filter"
                )
            
            with filter_col3:
                arama = st.text_input("Mağaza Ara (ID veya Ad)", key="magaza_arama")
            
            # Filtreleme uygula
            filtered_magaza = magaza_analiz.copy()
            
            if cover_grubu_filter:
                filtered_magaza = filtered_magaza[filtered_magaza['magaza_cover_grubu'].isin(cover_grubu_filter)]
            
            if min_sevk_filter > 0:
                filtered_magaza = filtered_magaza[filtered_magaza['sevk_miktar'] >= min_sevk_filter]
            
            if arama:
                if 'magaza_adi' in filtered_magaza.columns:
                    filtered_magaza = filtered_magaza[
                        filtered_magaza['magaza_id'].astype(str).str.contains(arama, case=False) |
                        filtered_magaza['magaza_adi'].astype(str).str.contains(arama, case=False, na=False)
                    ]
                else:
                    filtered_magaza = filtered_magaza[
                        filtered_magaza['magaza_id'].astype(str).str.contains(arama, case=False)
                    ]
            
            st.write(f"**📋 Mağaza Detayları ({len(filtered_magaza)} mağaza):**")
            
            # Renkli gösterim için stil
            def highlight_low_coverage(row):
                if row['ihtiyac_karsilama_%'] < 50:
                    return ['background-color: #fee2e2'] * len(row)
                elif row['ihtiyac_karsilama_%'] < 80:
                    return ['background-color: #fef3c7'] * len(row)
                else:
                    return ['background-color: #d1fae5'] * len(row)
            
            styled_magaza = filtered_magaza.style\
                .format({
                    'sevk_miktar': '{:,.0f}',
                    'ihtiyac': '{:,.0f}',
                    'haftalik_satis': '{:,.0f}',
                    'cover': '{:.1f}',
                    'ihtiyac_karsilama_%': '{:.1f}%',
                    'urun_basi_sevk': '{:.1f}',
                    'haftalik_cover': '{:.1f}'
                })\
                .apply(highlight_low_coverage, axis=1)
            
            st.dataframe(styled_magaza, use_container_width=True, hide_index=True)
            
            # Cover Grubu Analizi
            st.markdown("---")
            st.subheader("📊 Mağaza Cover Grubu Bazlı Analiz")
            
            magaza_grup_analiz = magaza_analiz.groupby('magaza_cover_grubu').agg({
                'magaza_id': 'nunique',
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'haftalik_satis': 'sum',
                'cover': 'mean',
                'urun_cesidi': 'mean'
            }).reset_index()
            
            magaza_grup_analiz.columns = ['Cover Grubu', 'Mağaza Sayısı', 'Toplam Sevkiyat', 
                                          'Toplam İhtiyaç', 'Toplam Satış', 'Ort. Cover', 'Ort. Ürün Çeşidi']
            
            magaza_grup_analiz['Mağaza Başı Sevk'] = (
                magaza_grup_analiz['Toplam Sevkiyat'] / magaza_grup_analiz['Mağaza Sayısı']
            ).round(1)
            
            magaza_grup_analiz['İhtiyaç Karşılama %'] = (
                (magaza_grup_analiz['Toplam Sevkiyat'] / magaza_grup_analiz['Toplam İhtiyaç'] * 100)
                .fillna(0)
                .replace([np.inf, -np.inf], 0)
                .round(1)
            )
            
            st.dataframe(
                magaza_grup_analiz.style.format({
                    'Mağaza Sayısı': '{:,.0f}',
                    'Toplam Sevkiyat': '{:,.0f}',
                    'Toplam İhtiyaç': '{:,.0f}',
                    'Toplam Satış': '{:,.0f}',
                    'Ort. Cover': '{:.1f}',
                    'Ort. Ürün Çeşidi': '{:.1f}',
                    'Mağaza Başı Sevk': '{:.1f}',
                    'İhtiyaç Karşılama %': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Top 10 ve Bottom 10
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🏆 En Yüksek Sevkiyat (Top 10):**")
                top10 = filtered_magaza.head(10)[['magaza_id'] + 
                    (['magaza_adi'] if 'magaza_adi' in filtered_magaza.columns else []) +
                    ['sevk_miktar', 'cover', 'magaza_cover_grubu']]
                st.dataframe(top10, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**⚠️ En Düşük Sevkiyat (Bottom 10):**")
                bottom10 = filtered_magaza.tail(10)[['magaza_id'] + 
                    (['magaza_adi'] if 'magaza_adi' in filtered_magaza.columns else []) +
                    ['sevk_miktar', 'cover', 'magaza_cover_grubu']]
                st.dataframe(bottom10, use_container_width=True, hide_index=True)
            
            # İndirme
            csv_magaza = filtered_magaza.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 Mağaza Analizini İndir",
                csv_magaza,
                "magaza_analizi.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("Mağaza analizi için veri yok")
            
    # TAB 3: Ürün
    with tab3:
        st.subheader("📦 Ürün Analizi")
        st.info("Ürün detayları")
    
    # TAB 4: Alım
    with tab4:
        st.subheader("🛒 Alım İhtiyacı")
        
        try:
            alim_ihtiyaci = calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df)
            
            if not alim_ihtiyaci.empty:
                toplam_ihtiyac = alim_ihtiyaci['alim_siparis_miktari'].sum()
                st.metric("Toplam Alım", f"{toplam_ihtiyac:,.0f} adet")
                st.dataframe(alim_ihtiyaci.head(20), use_container_width=True)
                
                csv_alim = alim_ihtiyaci.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Alım İndir", csv_alim, "alim_ihtiyaci.csv", "text/csv")
            else:
                st.info("Alım ihtiyacı yok")
        except Exception as e:
            st.error(f"Alım hatası: {e}")
    
    # TAB 5: Matris
    with tab5:
        st.subheader("🎯 Matris Analizi")
        st.info("Matris performansı")
    
    # TAB 6: Detay
    with tab6:
        st.subheader("📋 Detaylı Rapor")
        st.dataframe(total_sevk, use_container_width=True)
        
        csv = total_sevk.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 Detay İndir", csv, "sevkiyat_detay.csv", "text/csv")

# -------------------------------
# ANA SAYFA
# -------------------------------

def show_main_page():
    """Ana sayfa"""
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%); color: white; border-radius: 15px; margin-bottom: 25px;">
        <h1>📦 EVE Sevkiyat Planlama</h1>
        <p>3 Matris Sistemi - TUR 1 + TUR 2 + ALIM</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Parametreler", "📁 Veri", "🚀 Hesaplama"])
    
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
            selected_file = st.selectbox("Önizleme:", list(file_data.keys()))
            if selected_file:
                st.dataframe(file_data[selected_file].head(10), use_container_width=True)
    
    with tab3:
        st.header("🚀 Hesaplama")
        
        if not st.session_state.get('file_data'):
            st.error("❌ Önce dosya yükleyin!")
            return
        
        if st.button("🎯 HESAPLA", type="primary", use_container_width=True):
            try:
                with st.spinner("Hesaplanıyor..."):
                    start_time = time.time()
                    
                    sevk_df, total_sevk, depo_stok_df, original_sevkiyat_df = calculate_shipment_optimized(
                        st.session_state.file_data,
                        st.session_state.params,
                        st.session_state.cover_gruplari
                    )
                    
                    st.session_state.sevk_df = sevk_df
                    st.session_state.total_sevk = total_sevk
                    st.session_state.depo_stok_df = depo_stok_df
                    st.session_state.original_sevkiyat_df = original_sevkiyat_df
                    
                    sure = time.time() - start_time
                    st.success(f"✅ Tamamlandı! ({sure:.1f}s)")
                    
                    # Özet
                    if not total_sevk.empty:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Sevkiyat", f"{st.session_state.toplam_sevk:,}")
                        col2.metric("Mağaza", total_sevk['magaza_id'].nunique())
                        col3.metric("Ürün", total_sevk['urun_id'].nunique())
                        col4.metric("Min %", f"{st.session_state.min_yuzde:.1f}%")
                        
                        st.dataframe(total_sevk.head(50), use_container_width=True)
                        
                        csv = total_sevk.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button("📥 Sevkiyat İndir", csv, "sevkiyat.csv", "text/csv")
                    
            except Exception as e:
                st.error(f"❌ Hata: {e}")
                logger.error(f"Hesaplama hatası: {e}", exc_info=True)

# -------------------------------
# MAIN
# -------------------------------

def main():
    """Ana uygulama"""
    st.set_page_config(
        page_title="EVE Sevkiyat - 3 Matris", 
        layout="wide"
    )
    
    st.markdown("""
    <style>
        .stMetric {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    main_tab1, main_tab2 = st.tabs(["🏠 Ana Sayfa", "📈 Raporlar"])
    
    with main_tab1:
        show_main_page()
    
    with main_tab2:
        show_reports()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b;">
        <p>EVE Sevkiyat v2.0 - 3 Matris Sistemi</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

