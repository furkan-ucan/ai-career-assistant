"""
Filtreleme Modülü
Junior/entry-level pozisyonlar için akıllı filtreleme işlemleri
"""

# Standard Library
import logging

logger = logging.getLogger(__name__)


def filter_junior_suitable_jobs(jobs_list, debug=False):
    """
    Junior/Entry-level pozisyonlar için uygun olmayan ilanları filtreler
    YBS öğrencisinin kariyer hedefleri (ERP, Proje Yönetimi, İş Analizi) göz önünde bulundurularak optimizasyon
    """
    if not jobs_list:
        logger.info("No jobs provided for filtering.")
        return []

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

    filtered_jobs = []
    filter_stats = {
        "title": 0,
        "experience": 0,
        "responsibility": 0,
        "out_of_scope": 0,
        "passed": 0,
    }

    for job in jobs_list:
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()

        # 1. Başlık kontrolü
        title_rejected = any(word in title for word in title_blacklist)

        # 2. Deneyim kontrolü
        experience_rejected = any(exp in description for exp in experience_blacklist)

        # 3. Sorumluluk kontrolü
        responsibility_rejected = any(
            resp in description for resp in responsibility_blacklist)

        # 4. Rol dışı kontrol
        out_of_scope_rejected = any(
            word in title for word in out_of_scope_blacklist)  # Filtreleme kararı
        if title_rejected:
            filter_stats["title"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (başlık): {job.get('title', 'N/A')}")
        elif experience_rejected:
            filter_stats["experience"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (deneyim): {job.get('title', 'N/A')}")
        elif responsibility_rejected:
            filter_stats["responsibility"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (sorumluluk): {job.get('title', 'N/A')}")
        elif out_of_scope_rejected:
            filter_stats["out_of_scope"] += 1
            if debug:
                logger.debug(f"🔥 Filtrelendi (rol dışı): {job.get('title', 'N/A')}")
        else:
            # Geçti - listeye ekle
            filtered_jobs.append(job)
            filter_stats["passed"] += 1
            if debug:
                # Filtreleme istatistikleri
                logger.debug(f"✅ Geçti: {job.get('title', 'N/A')}")
    total_processed = len(jobs_list)
    logger.info("\n📊 Filtreleme İstatistikleri:")
    logger.info(f"   Toplam işlenen: {total_processed}")
    logger.info(f"   🔥 Başlık filtresi: {filter_stats['title']}")
    logger.info(f"   🔥 Deneyim filtresi: {filter_stats['experience']}")
    logger.info(f"   🔥 Sorumluluk filtresi: {filter_stats['responsibility']}")
    logger.info(f"   🔥 Rol dışı filtresi: {filter_stats['out_of_scope']}")
    logger.info(f"   ✅ Geçen: {filter_stats['passed']}")

    if total_processed == 0:
        logger.info("   📈 Başarı oranı: %0.1f", 0.0)
        logger.info("No jobs were processed.")
    else:
        success_rate = (filter_stats["passed"] / total_processed) * 100
        logger.info(f"   📈 Başarı oranı: %{success_rate:.1f}")

    return filtered_jobs


def score_jobs(jobs_list, scoring_system, debug=False):
    """Apply intelligent scoring system and return jobs above threshold."""
    scored = []
    for job in jobs_list:
        total, details = scoring_system.score_job(job)
        job["score"] = total
        job["score_details"] = details
        if scoring_system.should_include(total):
            scored.append(job)
            if debug:
                logger.debug(
                    f"✅ Skor {total} ile kabul: {job.get('title', 'N/A')} - {details}")
        elif debug:
            logger.debug(
                f"🔥 Skor {total} ile reddedildi: {job.get('title', 'N/A')} - {details}")

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def compare_filters(jobs_list, scoring_system, debug=False):
    """Return comparison of legacy filter and intelligent scoring results."""
    old_filtered = filter_junior_suitable_jobs(jobs_list, debug=debug)
    new_filtered = score_jobs(jobs_list, scoring_system, debug=debug)

    old_titles = {job.get("title") for job in old_filtered}
    new_titles = {job.get("title") for job in new_filtered}

    return {
        "old_only": list(old_titles - new_titles),
        "new_only": list(new_titles - old_titles),
        "intersection": list(old_titles & new_titles),
    }
