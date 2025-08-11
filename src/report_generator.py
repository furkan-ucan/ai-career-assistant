# src/report_generator.py
"""
Strategic Career Report Generator - Creates comprehensive markdown reports
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StrategicReportGenerator:
    """Generates comprehensive career analysis reports in markdown format."""

    def __init__(self, output_dir: str | Path = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self,
        final_results: list[dict],
        ai_metadata: dict[str, Any] | None,
        raw_jobs_count: int,
        threshold: float,
    ) -> Path:
        """Generate a comprehensive career analysis report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"career_analysis_{timestamp}.md"

        report_content = self._build_report_content(final_results, ai_metadata, raw_jobs_count, threshold)

        try:
            with report_file.open("w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"📝 Stratejik kariyer raporu oluşturuldu: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"❌ Rapor oluşturulurken hata: {e}")
            raise

    def _build_report_content(
        self,
        final_results: list[dict],
        ai_metadata: dict[str, Any] | None,
        raw_jobs_count: int,
        threshold: float,
    ) -> str:
        """Build the complete markdown report content."""
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        content = f"""# 🎯 Stratejik Kariyer Analizi Raporu

**Oluşturulma Tarihi:** {timestamp}
**Toplam Analiz Edilen İlan:** {raw_jobs_count}
**Kaliteli Fırsat Sayısı:** {len(final_results)}
**Eşik Değeri:** {threshold}%

---

## 📊 Özet Değerlendirme

Bu rapor, CV'niz detaylı analiz edilerek oluşturulmuş kişiselleştirilmiş bir kariyer yol haritasıdır.

"""

        # CV Analizi Bölümü
        if ai_metadata:
            content += self._build_cv_analysis_section(ai_metadata)

        # En İyi Fırsatlar Bölümü
        content += self._build_opportunities_section(final_results)

        # Stratejik Öneriler
        content += self._build_strategic_recommendations(final_results, ai_metadata)

        # İstatistikler
        content += self._build_statistics_section(final_results)

        content += self._build_footer()

        return content

    def _build_cv_analysis_section(self, ai_metadata: dict[str, Any]) -> str:
        """Build the CV analysis section."""
        content = "## 🔍 CV Analizi ve Profil Değerlendirmesi\n\n"

        if summary := ai_metadata.get("cv_summary"):
            content += f"### 📝 Profil Özeti\n{summary}\n\n"

        if skills := ai_metadata.get("key_skills"):
            content += "### 💪 En Güçlü Yetenekleriniz\n\n"
            skill_importance = ai_metadata.get("skill_importance", [])
            for i, skill in enumerate(skills[:8]):
                importance = skill_importance[i] if i < len(skill_importance) else 0.8
                percentage = int(importance * 100)
                content += f"- **{skill}** ({percentage}% önem)\n"
            content += "\n"

        if targets := ai_metadata.get("target_job_titles"):
            content += "### 🎯 Hedef Pozisyonlar\n\n"
            for title in targets[:5]:
                content += f"- {title}\n"
            content += "\n"

        return content

    def _build_opportunities_section(self, final_results: list[dict]) -> str:
        """Build the job opportunities section."""
        content = "## 🚀 En İyi Kariyer Fırsatları\n\n"

        if not final_results:
            return content + "Henüz analiz edilmiş fırsat bulunmuyor.\n\n"

        # En iyi 10 fırsatı detaylandır
        for i, job in enumerate(final_results[:10], 1):
            content += self._format_job_opportunity(job, i)

        return content

    def _format_job_opportunity(self, job: dict, index: int) -> str:
        """Format a single job opportunity."""
        title = job.get("title", "Başlık Belirtilmemiş")
        company = job.get("company", "Şirket Belirtilmemiş")
        location = job.get("location", "Lokasyon Belirtilmemiş")

        content = f"### {index}. {title} - {company}\n\n"
        content += f"**📍 Lokasyon:** {location}  \n"

        # AI analizi varsa ekle
        if fit_score := job.get("fit_score"):
            is_recommended = job.get("is_recommended", False)
            recommendation = "✅ TAVSİYE EDİLİR" if is_recommended else "⚠️ ŞARTLI TAVSİYE"
            content += f"**📊 Uygunluk Skoru:** {fit_score}/100 ({recommendation})  \n"

            if reasoning := job.get("reasoning"):
                content += f"**💡 AI Değerlendirmesi:** {reasoning}  \n"

            if matching := job.get("matching_keywords"):
                content += f"**✅ Eşleşen Yetenekler:** {', '.join(matching)}  \n"

            if missing := job.get("missing_keywords"):
                content += f"**⚠️ Gelişim Alanları:** {', '.join(missing)}  \n"
        else:
            # Fallback similarity score
            sim_score = job.get("score", 0)
            content += f"**📊 Benzerlik Skoru:** {sim_score:.1f}  \n"

        # İlan detayları
        if source := job.get("source_site"):
            content += f"**🌐 Kaynak:** {source}  \n"

        if persona := job.get("persona_source"):
            content += f"**👤 Bulunan Persona:** {persona}  \n"

        if url := job.get("url", job.get("job_url")):
            content += f"**🔗 İlan Linki:** [Başvuru Yap]({url})  \n"

        content += "\n---\n\n"
        return content

    def _build_strategic_recommendations(self, final_results: list[dict], ai_metadata: dict[str, Any] | None) -> str:
        """Build strategic recommendations section."""
        content = "## 💡 Stratejik Kariyer Önerileri\n\n"

        # En sık eksik olan yetenekleri topla
        missing_skills = []
        for job in final_results[:15]:
            if job_missing := job.get("missing_keywords"):
                missing_skills.extend(job_missing)

        if missing_skills:
            # En sık eksik olan 5 yeteneği bul
            from collections import Counter

            skill_counts = Counter(missing_skills)
            top_missing = skill_counts.most_common(5)

            content += "### 🎯 Öncelikli Gelişim Alanları\n\n"
            content += "Analiz edilen pozisyonlarda en sık aranan ama CV'nizde eksik olan yetenekler:\n\n"

            for skill, count in top_missing:
                percentage = (count / len(final_results[:15])) * 100
                content += f"- **{skill}** ({count} pozisyonda isteniyor, %{percentage:.1f})\n"

            content += "\n"

        # Başarı analizi
        if final_results:
            high_fit_jobs = [j for j in final_results if j.get("fit_score", 0) >= 80]
            if high_fit_jobs:
                content += "### ✅ Güçlü Yanlarınız\n\n"
                content += f"Analiz edilen {len(final_results)} pozisyonun {len(high_fit_jobs)} tanesinde "
                content += "yüksek uygunluk (%80+) gösteriyorsunuz. Bu, mevcut yeteneklerinizin piyasada değerli olduğunu gösterir.\n\n"

        # Kişiselleştirilmiş öneriler
        content += "### 🚀 Kişiselleştirilmiş Aksiyon Planı\n\n"
        content += "1. **Hemen Başvurabilecekleriniz:** İlk 3-5 pozisyon için bugün başvuru yapın\n"
        content += "2. **Gelişim Odaklı:** Eksik yetenekleri 2-3 ay içinde kazanmayı hedefleyin\n"
        content += "3. **Ağ Genişletme:** Hedef şirketlerde çalışan kişilerle bağlantı kurun\n"
        content += "4. **Sürekli Takip:** Bu analizi 2 haftada bir tekrarlayın\n\n"

        return content

    def _build_statistics_section(self, final_results: list[dict]) -> str:
        """Build the statistics section."""
        content = "## 📈 Detaylı İstatistikler\n\n"

        if not final_results:
            return content + "İstatistik hesaplanacak veri bulunmuyor.\n\n"

        # Kaynak site dağılımı
        from collections import Counter

        sites = [job.get("source_site", "Bilinmiyor") for job in final_results]
        site_counts = Counter(sites)

        content += "### 🌐 Fırsat Kaynakları\n\n"
        for site, count in site_counts.most_common():
            percentage = (count / len(final_results)) * 100
            content += f"- **{site}:** {count} pozisyon (%{percentage:.1f})\n"

        content += "\n"

        # Skor dağılımı
        if any(job.get("fit_score") for job in final_results):
            content += "### 📊 Uygunluk Skoru Dağılımı\n\n"
            high_scores = len([j for j in final_results if j.get("fit_score", 0) >= 80])
            medium_scores = len([j for j in final_results if 60 <= j.get("fit_score", 0) < 80])
            low_scores = len([j for j in final_results if j.get("fit_score", 0) < 60])

            content += f"- **Yüksek Uygunluk (80+):** {high_scores} pozisyon\n"
            content += f"- **Orta Uygunluk (60-79):** {medium_scores} pozisyon\n"
            content += f"- **Düşük Uygunluk (<60):** {low_scores} pozisyon\n\n"

        return content

    def _build_footer(self) -> str:
        """Build the report footer."""
        return """---

## 📞 Sonraki Adımlar

Bu rapor AI destekli analiz sonucu oluşturulmuştur. Kariyer hedeflerinize ulaşmanız için:

1. **Öncelikli pozisyonlara odaklanın** (yüksek skor alanlar)
2. **Eksik yetenekleri geliştirin** (missing keywords)
3. **CV'nizi güçlü yönlerinize odaklayarak güncelleyin**
4. **Düzenli analiz yapın** (yeni fırsatlar için)

Bu analiz sadece bir başlangıçtır. Kariyer yolculuğunuzda başarılar dileriz! 🚀

---
*Bu rapor Akıllı Kariyer Asistanı tarafından otomatik olarak oluşturulmuştur.*
"""
