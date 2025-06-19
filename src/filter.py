"""
Filtreleme Modülü
Junior/entry-level pozisyonlar için akıllı filtreleme işlemleri
"""

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
    ]

    # Deneyim blacklist - Sadece çok net ve yüksek yıl ifadeleri
    experience_blacklist = [
        '5+ yıl', '5 yıl', '5+ years', '5 years', '6+ yıl', '7+ yıl',
        '8+ yıl', '10+ yıl', 'en az 5 yıl', 'minimum 5 years',
        'minimum 6', 'en az 6', 'minimum 7', 'en az 7'
    ]

    # Sorumluluk blacklist - Sadece doğrudan personel yönetimi içerenler
    responsibility_blacklist = [
        'takım yönetimi', 'team management', 'personel yönetimi',
        'bütçe yönetimi', 'budget responsibility', 'işe alım', 'hiring',
        'direct reports', 'performans değerlendirme', 'team building'
    ]

    # Rol dışı blacklist - Kariyer hedefleriyle ilgisiz pozisyonlar
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
        experience_rejected = any(exp in description for exp in experience_blacklist)

        # 3. Sorumluluk kontrolü
        responsibility_rejected = any(resp in description for resp in responsibility_blacklist)

        # 4. Rol dışı kontrol
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
                print(f"✅ Geçti: {job.get('title', 'N/A')}")

    # Filtreleme istatistikleri
    total_processed = len(jobs_list)
    print(f"\n📊 Filtreleme İstatistikleri:")
    print(f"   Toplam işlenen: {total_processed}")
    print(f"   🔥 Başlık filtresi: {filter_stats['title']}")
    print(f"   🔥 Deneyim filtresi: {filter_stats['experience']}")
    print(f"   🔥 Sorumluluk filtresi: {filter_stats['responsibility']}")
    print(f"   🔥 Rol dışı filtresi: {filter_stats['out_of_scope']}")
    print(f"   ✅ Geçen: {filter_stats['passed']}")
    print(f"   📈 Başarı oranı: %{(filter_stats['passed']/total_processed)*100:.1f}")

    return filtered_jobs
