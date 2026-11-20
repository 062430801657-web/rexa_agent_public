import datetime
import database

class EvolutionEngine:
    def __init__(self):
        database.init_db()

    def record_evolution(self, skill_name, description, growth_rate="+10%"):
        database.log_evolution(skill_name, description, growth_rate)
        return f"🚀 Evolusi tercatat: Skill '{skill_name}' ditambahkan dengan peningkatan kecerdasan {growth_rate}!"

    def get_evolution_report(self):
        history = database.get_evolution_history(limit=15)
        if not history:
            return "Belum ada riwayat evolusi yang tercatat."

        today = datetime.date.today().isoformat()
        today_skills = [h for h in history if h['date'] == today]

        report = [
            "📈 ========================================================",
            f"🧠 DASHBOARD EVOLUSI KECERDASAN REXA (TARGET: +10%/HARI)",
            "========================================================",
            f"📅 Tanggal Hari Ini : {today}",
            f"⚡ Skill Baru Hari Ini : {len(today_skills)} kemampuan",
            f"📊 Total Riwayat Catatan: {len(history)} entri evolusi",
            "--------------------------------------------------------",
            "Daftar Pencapaian Evolusi Terbaru:"
        ]

        for h in history:
            report.append(f"• [{h['date']}] {h['growth_rate']} - {h['skill_name']}: {h['description']}")

        report.append("========================================================\n")
        return "\n".join(report)
