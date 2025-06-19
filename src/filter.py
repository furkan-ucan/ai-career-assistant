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


def filter_junior_suitable_jobs(jobs_list, debug=False):
    """
    Junior/Entry-level pozisyonlar için uygun olmayan ilanları filtreler
    YBS öğrencisinin kariyer hedefleri (ERP, Proje Yönetimi, İş Analizi) göz önünde bulundurularak optimizasyon
    """
    # Başlık blacklist - SADECE kesinlikle senior olanları hedefler
    title_blacklist = [
        "senior",
        "sr.",
        "sr ",
        "lead",
        "principal",
        "manager",
        "direktör",
        "müdür",
        "chief",
        "head",
        "supervisor",
        "team lead",
        "tech lead",
        "kıdemli",
        "başkan",
        "architect",
        "baş ",
        "lider",
        "leader",
    ]

    # Deneyim blacklist - Sadece çok net ve yüksek yıl ifadeleri
    experience_blacklist = [
        "5+ yıl",
        "5 yıl",
        "5+ years",
        "5 years",
        "6+ yıl",
        "7+ yıl",
        "8+ yıl",
        "10+ yıl",
        "en az 5 yıl",
        "minimum 5 years",
        "minimum 6",
        "en az 6",
        "minimum 7",
        "en az 7",
    ]

    # Sorumluluk blacklist - Sadece doğrudan personel yönetimi içerenler
    responsibility_blacklist = [
        "takım yönetimi",
        "team management",
        "personel yönetimi",
        "bütçe yönetimi",
        "budget responsibility",
        "işe alım",
        "hiring",
        "direct reports",
        "performans değerlendirme",
        "team building",
    ]

    # Rol dışı blacklist - Kariyer hedefleriyle ilgisiz pozisyonlar
    out_of_scope_blacklist = [
        "avukat",
        "hukuk",
        "legal",
        "asistan",
        "assistant",
        "e-ticaret",
        "e-commerce",
        "insan kaynakları",
        "human resources",
        "pazarlama",
        "marketing",
        "satış",
        "sales",
        "grafik",
        "graphic",
        "tasarım",
        "design",
        "muhasebe",
        "accounting",
        "finans uzmanı",
        "customer service",
        "müşteri hizmetleri",
        "çağrı merkezi",
        "güvenlik",
        "security guard",
        "temizlik",
        "cleaning",
        "çevre",
        "üretim operatör",
        "fabrika",
        "manufacturing operator",
    ]

    # Regex pattern'leri oluştur (kelime sınırları ile)
    title_pattern = _create_regex_pattern(title_blacklist)
    experience_pattern = _create_regex_pattern(experience_blacklist)
    responsibility_pattern = _create_regex_pattern(responsibility_blacklist)
    out_of_scope_pattern = _create_regex_pattern(out_of_scope_blacklist)

    filtered_jobs = []
    filter_stats = {"title": 0, "experience": 0, "responsibility": 0, "out_of_scope": 0, "passed": 0}

    logger.info(f"🔍 {len(jobs_list)} iş ilanı regex tabanlı filtrelemeden geçiriliyor...")

    for job in jobs_list:
        title = job.get("title", "")
        description = job.get("description", "")

        # 1. Başlık kontrolü (regex ile kelime sınırı kontrolü)
        title_rejected = bool(title_pattern.search(title))

        # 2. Deneyim kontrolü (regex ile kelime sınırı kontrolü)
        experience_rejected = bool(experience_pattern.search(description))

        # 3. Sorumluluk kontrolü (regex ile kelime sınırı kontrolü)
        responsibility_rejected = bool(responsibility_pattern.search(description))

        # 4. Rol dışı kontrol (regex ile kelime sınırı kontrolü)
        out_of_scope_rejected = bool(out_of_scope_pattern.search(title))  # Filtreleme kararı
        if title_rejected:
            filter_stats["title"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (başlık regex): {job.get('title', 'N/A')}")
        elif experience_rejected:
            filter_stats["experience"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (deneyim regex): {job.get('title', 'N/A')}")
        elif responsibility_rejected:
            filter_stats["responsibility"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (sorumluluk regex): {job.get('title', 'N/A')}")
        elif out_of_scope_rejected:
            filter_stats["out_of_scope"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (rol dışı regex): {job.get('title', 'N/A')}")
        else:
            # Geçti - listeye ekle
            filtered_jobs.append(job)
            filter_stats["passed"] += 1
            if debug:
                logger.debug(f"✅ Geçti (regex kontrolü): {job.get('title', 'N/A')}")  # Filtreleme istatistikleri
    total_processed = len(jobs_list)
    logger.info("\n📊 Regex Tabanlı Filtreleme İstatistikleri:")
    logger.info(f"   Toplam işlenen: {total_processed}")
    logger.info(f"   🔥 Başlık filtresi (regex): {filter_stats['title']}")
    logger.info(f"   🔥 Deneyim filtresi (regex): {filter_stats['experience']}")
    logger.info(f"   🔥 Sorumluluk filtresi (regex): {filter_stats['responsibility']}")
    logger.info(f"   🔥 Rol dışı filtresi (regex): {filter_stats['out_of_scope']}")
    logger.info(f"   ✅ Geçen (kelime sınırı korumalı): {filter_stats['passed']}")
    logger.info(f"   📈 Başarı oranı: %{(filter_stats['passed'] / total_processed) * 100:.1f}")

    return filtered_jobs
