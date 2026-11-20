import database

class MemoryManager:
    def __init__(self):
        database.init_db()
        self._seed_default_memories_if_empty()

    def _seed_default_memories_if_empty(self):
        existing = database.get_all_memories()
        if not existing:
            # Seed foundational identity
            database.save_memory(
                category="profile",
                key="owner_identity",
                content="Gunakan nama dan preferensi pemilik yang dikonfigurasi secara lokal.",
                importance=5
            )
            database.save_memory(
                category="principle",
                key="factual_truth",
                content="Prinsip Rexa: Berpikir mandiri dan objektif, tidak berhalusinasi (no fake data). Jika jelek katakan jelek, jika bagus katakan bagus berdasarkan verifikasi data nyata.",
                importance=5
            )
            database.save_memory(
                category="principle",
                key="continuous_evolution",
                content="Prinsip Evolusi Berkelanjutan: Wajib berkembang minimal 10% lebih pintar setiap hari, proaktif memperluas skill teknis, dan mengasah intelijen otonom secara mandiri.",
                importance=5
            )
            database.save_memory(
                category="system",
                key="independence",
                content="Rexa adalah asisten AI yang dapat dikonfigurasi oleh pemilik instalasi.",
                importance=4
            )

    def get_system_memory_context(self):
        memories = database.get_all_memories()
        if not memories:
            return ""

        lines = ["\n## MEMORI AKTIF REXA (DATABASE TANPA BATAS):"]
        for m in memories:
            lines.append(f"• [{m['category'].upper()}] {m['key']}: {m['content']}")
        return "\n".join(lines)

    def store(self, category, key, content, importance=1):
        database.save_memory(category, key, content, importance)
        return f"Memori '{key}' ({category}) berhasil disimpan ke database abadi."

    def search(self, query):
        results = database.search_memories(query)
        if not results:
            return f"Tidak ditemukan memori yang cocok dengan kueri: '{query}'."
        out = [f"Hasil pencarian memori untuk '{query}':"]
        for r in results:
            out.append(f"• [{r['category']}] {r['key']}: {r['content']}")
        return "\n".join(out)
