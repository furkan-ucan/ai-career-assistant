"""
Filtreleme Modülü
Junior/entry-level pozisyonlar için akıllı filtreleme işlemleri
"""

import re
from datetime import datetime, timedelta

def extract_days_from_date_posted(date_posted_str):
    """
    date_posted string'inden gün sayısını çıkarır
    Örnekler: "3 days ago", "1 day ago", "yesterday", "today"
    Return: gün sayısı (int) veya None
    """
    if not date_posted_str:
        return None

    date_str = date_posted_str.lower().strip()

    # "today" durumu
    if "today" in date_str or "bugün" in date_str:
        return 0

    # "yesterday" durumu
    if "yesterday" in date_str or "dün" in date_str:
        return 1

    # "X days ago" veya "X day ago" pattern'i
    day_pattern = r'(\d+)\s*day[s]?\s*ago'
    match = re.search(day_pattern, date_str)
    if match:
        return int(match.group(1))

    # Türkçe "X gün önce" pattern'i
    turkish_pattern = r'(\d+)\s*gün\s*önce'
    match = re.search(turkish_pattern, date_str)
    if match:
        return int(match.group(1))

    # Eğer hiçbiri bulunamazsa, None döndür
    return None

def filter_jobs_by_date(jobs_list, max_days=None, debug=False):
    """
    İş ilanlarını tarih kriterine göre filtreler

    Args:
        jobs_list: İş ilanları listesi
        max_days: Maksimum gün sayısı (None = filtre yok)
        debug: Debug çıktısı

    Returns:
        Filtrelenmiş iş ilanları listesi
    """
    if max_days is None:
        if debug:
            print("📅 Tarih filtresi atlandı (max_days=None)")
        return jobs_list

    filtered_jobs = []
    date_stats = {'passed': 0, 'filtered': 0, 'no_date': 0}

    for job in jobs_list:
        date_posted = job.get('date_posted', '')
        days_ago = extract_days_from_date_posted(date_posted)

        if days_ago is None:
            # Tarih bilgisi yok - varsayılan olarak geçir
            date_stats['no_date'] += 1
            filtered_jobs.append(job)
            if debug:
                print(f"📅 Tarih bilgisi yok (geçirildi): {job.get('title', 'N/A')} - {date_posted}")
        elif days_ago <= max_days:
            # Tarih kriteri geçti
            date_stats['passed'] += 1
            filtered_jobs.append(job)
            if debug:
                print(f"✅ Tarih OK ({days_ago} gün): {job.get('title', 'N/A')}")
        else:
            # Tarih kriteri geçmedi
            date_stats['filtered'] += 1
            if debug:
                print(f"🔥 Tarih filtresi ({days_ago} > {max_days} gün): {job.get('title', 'N/A')}")

    # İstatistikler
    total = len(jobs_list)
    if debug or total > 0:
        print(f"\n📅 Tarih Filtresi İstatistikleri (≤{max_days} gün):")
        print(f"   Toplam işlenen: {total}")
        print(f"   ✅ Geçen: {date_stats['passed']}")
        print(f"   🔥 Filtrelenen: {date_stats['filtered']}")
        print(f"   ❓ Tarih bilgisi yok: {date_stats['no_date']}")
        print(f"   📈 Başarı oranı: %{((date_stats['passed'] + date_stats['no_date'])/total)*100:.1f}")

    return filtered_jobs

def filter_junior_suitable_jobs(jobs_list, debug=False):
    """
    Junior/Entry-level pozisyonlar için uygun olmayan ilanları filtreler
    YBS öğrencisinin kariyer hedefleri (ERP, Proje Yönetimi, İş Analizi) göz önünde bulundurularak optimizasyon
    """
    # Başlık blacklist - SADECE kesinlikle senior olanları hedefler
    title_blacklist = [
        'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager',
        'direktör', 'müdür', 'chief', 'head', 'supervisor',
        'team lead', 'tech lead', 'kıdemli', 'başkan',
        'architect', 'baş ', 'lider', 'leader'
        # 'uzman', 'consultant', 'sorumlu' ÇIKARILDI - YBS için gerekli!
    ]

    # Deneyim blacklist - Sadece çok net ve yüksek yıl ifadeleri
    experience_blacklist = [
        '5+ yıl', '5 yıl', '5+ years', '5 years', '6+ yıl', '7+ yıl',
        '8+ yıl', '10+ yıl', 'en az 5 yıl', 'minimum 5 years',
        'minimum 6', 'en az 6', 'minimum 7', 'en az 7'
        # 3-4 yıl ifadeleri ÇIKARILDI - entry-level için makul
    ]    # Sorumluluk blacklist - Sadece doğrudan personel yönetimi içerenler
    # "Proje Yönetimi" VE "ERP" ifadeleri ÇIKARILDI!
    responsibility_blacklist = [
        'takım yönetimi', 'team management', 'personel yönetimi',
        'bütçe yönetimi', 'budget responsibility', 'işe alım', 'hiring',
        'direct reports', 'performans değerlendirme', 'team building'
        # 'proje yönetimi', 'project management' ÇIKARILDI - YBS için kritik!
    ]

    # Rol dışı blacklist - Kariyer hedefleriyle ilgisiz pozisyonlar (YENİ EKLEME!)
    out_of_scope_blacklist = [
        'avukat', 'hukuk', 'legal', 'asistan', 'assistant',
        'e-ticaret', 'e-commerce', 'insan kaynakları', 'human resources',
        'pazarlama', 'marketing', 'satış', 'sales', 'grafik', 'graphic',
        'tasarım', 'design', 'muhasebe', 'accounting', 'finans uzmanı',
        'customer service', 'müşteri hizmetleri', 'çağrı merkezi',
        'güvenlik', 'security guard', 'temizlik', 'cleaning',
        'çevre', 'üretim operatör', 'fabrika', 'manufacturing operator'
    ]

    filtered_jobs = []
    filter_stats = {'title': 0, 'experience': 0, 'responsibility': 0, 'out_of_scope': 0, 'passed': 0}

    for job in jobs_list:
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        # 1. Başlık kontrolü
        title_rejected = any(word in title for word in title_blacklist)

        # 2. Deneyim kontrolü
        experience_rejected = any(exp in description for exp in experience_blacklist)        # 3. Sorumluluk kontrolü
        responsibility_rejected = any(resp in description for resp in responsibility_blacklist)

        # 4. Rol dışı kontrol (YENİ EKLEME!)
        out_of_scope_rejected = any(word in title for word in out_of_scope_blacklist)

        # Filtreleme kararı
        if title_rejected:
            filter_stats['title'] += 1
            if debug:
                print(f"🔥 Filtrelendi (başlık): {job.get('title', 'N/A')}")
        elif experience_rejected:
            filter_stats['experience'] += 1
            if debug:
                print(f"🔥 Filtrelendi (deneyim): {job.get('title', 'N/A')}")
        elif responsibility_rejected:
            filter_stats['responsibility'] += 1
            if debug:
                print(f"🔥 Filtrelendi (sorumluluk): {job.get('title', 'N/A')}")
        elif out_of_scope_rejected:
            filter_stats['out_of_scope'] += 1
            if debug:
                print(f"🔥 Filtrelendi (rol dışı): {job.get('title', 'N/A')}")
        else:
            # Geçti - listeye ekle
            filtered_jobs.append(job)
            filter_stats['passed'] += 1
            if debug:
                print(f"✅ Geçti: {job.get('title', 'N/A')}")    # Filtreleme istatistikleri
    total_processed = len(jobs_list)
    print(f"\n📊 Filtreleme İstatistikleri:")
    print(f"   Toplam işlenen: {total_processed}")
    print(f"   🔥 Başlık filtresi: {filter_stats['title']}")
    print(f"   🔥 Deneyim filtresi: {filter_stats['experience']}")
    print(f"   🔥 Sorumluluk filtresi: {filter_stats['responsibility']}")
    print(f"   🔥 Rol dışı filtresi: {filter_stats['out_of_scope']}")  # YENİ SATIR
    print(f"   ✅ Geçen: {filter_stats['passed']}")
    print(f"   📈 Başarı oranı: %{(filter_stats['passed']/total_processed)*100:.1f}")

    return filtered_jobs
