"""
Filtreleme Modülü
Junior/entry-level pozisyonlar için akıllı filtreleme işlemleri
Regex tabanlı kelime sınırı kontrolü ile yanlış pozitifleri önler
"""

# Standard Library
import logging
import re

logger = logging.getLogger(__name__)


def _create_regex_pattern(blacklist_words):
    """
    Blacklist kelimelerinden regex pattern oluştur
    Kelime sınırlarını (\b) kullanarak tam kelime eşleşmesi sağlar

    Args:
        blacklist_words: Filtrelenecek kelimeler listesi

    Returns:
        Compiled regex pattern
    """
    # Her kelimeyi kelime sınırları ile çevreleyerek regex pattern oluştur
    # re.escape kullanarak özel karakterleri güvenli hale getir
    pattern_parts = [r"\b" + re.escape(word.lower()) + r"\b" for word in blacklist_words]
    pattern = "|".join(pattern_parts)

    return re.compile(pattern, re.IGNORECASE)


def filter_junior_suitable_jobs(jobs_list, filter_config, debug=False):
    """
    Junior/Entry-level pozisyonlar için uygun olmayan ilanları filtreler
    YBS öğrencisinin kariyer hedefleri (ERP, Proje Yönetimi, İş Analizi) göz önünde bulundurularak optimizasyon
    """
    # Filtreleme listelerini config'den al
    title_blacklist = filter_config.get("title_blacklist", [])
    experience_blacklist = filter_config.get("experience_blacklist", [])
    responsibility_blacklist = filter_config.get("responsibility_blacklist", [])
    out_of_scope_blacklist = filter_config.get("out_of_scope_blacklist", [])

    # Regex pattern'lerini oluştur
    title_pattern = _create_regex_pattern(title_blacklist)
    experience_pattern = _create_regex_pattern(experience_blacklist)
    responsibility_pattern = _create_regex_pattern(responsibility_blacklist)
    out_of_scope_pattern = _create_regex_pattern(out_of_scope_blacklist)

    filtered_jobs = []
    rejected_jobs_log = []  # Reddedilen işleri loglamak için

    logger.info(f"🔍 {len(jobs_list)} iş ilanı regex tabanlı filtrelemeden geçiriliyor...")

    for job in jobs_list:
        title = job.get("title", "").lower()
        description = str(job.get("description", "")).lower()
        full_text = title + " " + description

        rejection_reasons = []

        # 1. Başlık filtresi (Kesin Senior/Yönetici Rolleri)
        if title_pattern.search(title):
            rejection_reasons.append(f"Başlıkta yasaklı kelime: '{title_pattern.search(title).group(0)}'")

        # 2. Kapsam Dışı Roller (İlgisiz Alanlar)
        if out_of_scope_pattern.search(title):
            rejection_reasons.append(f"Kapsam dışı rol: '{out_of_scope_pattern.search(title).group(0)}'")

        # 3. Deneyim ve Sorumluluk Filtresi (Açıklama metni içinde)
        if experience_pattern.search(full_text):
            rejection_reasons.append(f"Yüksek deneyim şartı: '{experience_pattern.search(full_text).group(0)}'")

        if responsibility_pattern.search(full_text):
            rejection_reasons.append(f"Üst düzey sorumluluk: '{responsibility_pattern.search(full_text).group(0)}'")

        if not rejection_reasons:
            filtered_jobs.append(job)
        else:
            # Reddedilen işleri ve nedenlerini kaydet
            rejected_jobs_log.append({"title": job.get("title"), "reasons": rejection_reasons})

    if debug:
        logger.info("--- FİLTRELEME DEBUG RAPORU ---")
        logger.info(f"Toplam {len(jobs_list)} ilan analiz edildi.")
        logger.info(f"{len(filtered_jobs)} ilan uygun bulundu.")
        logger.info(f"{len(rejected_jobs_log)} ilan reddedildi.")
        for rejected in rejected_jobs_log[:10]:  # İlk 10 reddedilen ilanı göster
            logger.info(f"- Reddedildi: {rejected['title']} -> Nedenler: {rejected['reasons']}")
        logger.info("---------------------------------")

    return filtered_jobs
