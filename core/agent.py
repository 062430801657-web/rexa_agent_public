import json
import os
import time
import urllib.request
from pathlib import Path

import config
from openai import OpenAI


class LLMRouter:
    def __init__(self):
        if not config.API_KEY:
            raise ValueError("REXA_API_KEY belum diatur.")
        self.client = OpenAI(base_url=config.API_BASE_URL, api_key=config.API_KEY, timeout=60)
        self.fast_pool = [config.FAST_MODEL]
        self.deep_pool = [config.DEEP_REASONING_MODEL, config.FAST_MODEL]
        self.cooldowns = {}

    def complete(self, messages, tools=None, deep=False, temperature=0.3, on_status=None):
        errors = []
        for model in dict.fromkeys(self.deep_pool if deep else self.fast_pool):
            if self.cooldowns.get(model, 0) > time.time():
                continue
            if on_status:
                on_status(f"{config.AGENT_NAME} sedang berpikir...")
            try:
                kwargs = {"model": model, "messages": messages, "temperature": temperature}
                if tools:
                    kwargs.update(tools=tools, tool_choice="auto")
                response = self.client.chat.completions.create(**kwargs)
                if not response.choices or not response.choices[0].message:
                    raise ValueError(f"Model {model} memberi respons kosong.")
                return response.choices[0].message
            except Exception as exc:
                self.cooldowns[model] = time.time() + 180
                errors.append(f"{model}: {exc}")
        raise RuntimeError("Semua model gagal: " + " | ".join(errors[-2:]))


class MemoryManager:
    def __init__(self):
        import database
        database.init_db()
        if not database.get_all_memories():
            database.save_memory("profile", "owner_identity", f"Pemilik: {config.OWNER_NAME}", 5)
            database.save_memory("principle", "factual_truth", "Utamakan informasi terverifikasi; nyatakan ketidakpastian.", 5)

    def get_system_memory_context(self):
        import database
        return "\n".join(f"[{m['category']}] {m['key']}: {m['content']}" for m in database.get_all_memories())

    def store(self, category, key, content, importance=1):
        import database
        database.save_memory(category, key, content, importance)
        return f"Memori '{key}' tersimpan."

    def search(self, query):
        import database
        rows = database.search_memories(query)
        return "\n".join(f"[{r['category']}] {r['key']}: {r['content']}" for r in rows) or "Tidak ditemukan memori cocok."


class EvolutionEngine:
    def record(self, skill_name, description):
        import database
        database.log_evolution(skill_name, description)
        return "Catatan kemampuan tersimpan."


class ToolRegistry:
    """Toolset dasar mandiri; skills tambahan dimuat hanya dari direktori instalasi."""
    def __init__(self, memory_mgr, evolution_engine):
        self.memory_mgr = memory_mgr
        self.evolution_engine = evolution_engine
        self.root = Path(__file__).resolve().parents[1]
        self.skills_root = Path(os.environ.get("REXA_SKILLS_DIR", self.root / "skills")).expanduser().resolve()
        self.tools_schema = [
            self._schema("web_search", "Cari web via Exa MCP", {"query": {"type": "string"}}, ["query"]),
            self._schema("web_extract", "Ambil teks dari URL", {"url": {"type": "string"}}, ["url"]),
            self._schema("memory_save", "Simpan memori lokal", {"category": {"type": "string"}, "key": {"type": "string"}, "content": {"type": "string"}}, ["category", "key", "content"]),
            self._schema("memory_search", "Cari memori lokal", {"query": {"type": "string"}}, ["query"]),
            self._schema("todo_list", "Kelola daftar tugas SQLite", {"action": {"type": "string", "enum": ["add", "complete", "clear", "list"]}, "task": {"type": "string"}}, ["action"]),
            self._schema("skill_list", "Daftar skill lokal yang tersedia", {}, []),
            self._schema("skill_view", "Baca skill lokal berdasarkan nama", {"name": {"type": "string"}}, ["name"]),
        ]

    @staticmethod
    def _schema(name, description, properties, required):
        return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}}

    def get_scoped_tools(self, query=""):
        return self.tools_schema

    def execute(self, name, args):
        if name == "memory_save":
            return self.memory_mgr.store(args["category"], args["key"], args["content"])
        if name == "memory_search":
            return self.memory_mgr.search(args["query"])
        if name == "web_search":
            return self._exa("web_search_exa", {"query": args["query"], "numResults": max(1, min(int(args.get("limit", 5)), 10))})
        if name == "web_extract":
            return self._exa("web_fetch_exa", {"urls": [args["url"]]})
        if name == "skill_list":
            return "\n".join(sorted(p.name for p in self.skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())) if self.skills_root.is_dir() else "Belum ada skills/ terpasang."
        if name == "skill_view":
            skill = (self.skills_root / args["name"] / "SKILL.md").resolve()
            if self.skills_root not in skill.parents or not skill.is_file():
                return "Skill tidak ditemukan."
            return skill.read_text(encoding="utf-8")[:20000]
        if name == "todo_list":
            import database
            conn = database.get_db()
            try:
                with conn:
                    action, task = args["action"], args.get("task", "")
                    if action == "add" and task:
                        conn.execute("INSERT INTO tasks (task_id,title,details,status,created_at) VALUES (lower(hex(randomblob(8))),?,?, 'PENDING',datetime('now'))", (task, ""))
                        return "Tugas ditambahkan."
                    if action == "complete" and task:
                        conn.execute("UPDATE tasks SET status='COMPLETED',completed_at=datetime('now') WHERE task_id=? OR title=?", (task, task))
                        return "Tugas diperbarui."
                    if action == "clear":
                        conn.execute("DELETE FROM tasks")
                        return "Daftar tugas dibersihkan."
                    return "\n".join(f"[{r['task_id']}] ({r['status']}) {r['title']}" for r in conn.execute("SELECT task_id,title,status FROM tasks ORDER BY created_at")) or "Daftar tugas kosong."
            finally:
                conn.close()
        return f"Tool tidak dikenal: {name}"

    @staticmethod
    def _exa(tool, arguments):
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}}
        req = urllib.request.Request("https://mcp.exa.ai/mcp", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8", "replace")
            chunks = []
            for line in body.splitlines():
                if line.startswith("data: "):
                    try:
                        result = json.loads(line[6:]).get("result", {}).get("content", [])
                        chunks.extend(item.get("text", "") for item in result if item.get("type") == "text")
                    except (ValueError, AttributeError):
                        continue
            return "\n\n".join(chunks)[:12000] or body[:12000]
        except Exception as exc:
            return f"Pencarian web gagal: {exc}"


class RexaAgent:
    def __init__(self, deep_reasoning=False):
        self.deep_reasoning = deep_reasoning
        self.memory_mgr = MemoryManager()
        self.evolution_engine = EvolutionEngine()
        self.tool_registry = ToolRegistry(self.memory_mgr, self.evolution_engine)
        self.llm = LLMRouter()

    def run(self, user_message, max_turns=8, verbose=False, on_status=None, session_id="default"):
        import database
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT + "\n" + self.memory_mgr.get_system_memory_context()}]
        messages.extend({"role": m["role"], "content": m["content"] or ""} for m in database.get_session_messages(session_id, 20))
        messages.append({"role": "user", "content": user_message})
        for _ in range(max_turns):
            msg = self.llm.complete(messages, self.tool_registry.get_scoped_tools(user_message), self.deep_reasoning, on_status=on_status)
            calls = getattr(msg, "tool_calls", None) or []
            if not calls:
                answer = (msg.content or "").strip() or "Model memberi respons kosong."
                database.save_message(session_id, "user", user_message)
                database.save_message(session_id, "assistant", answer)
                return answer
            messages.append(msg)
            for call in calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                    result = self.tool_registry.execute(call.function.name, args)
                except Exception as exc:
                    result = f"Tool gagal: {exc}"
                messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)[:12000]})
        return "Batas putaran tercapai; kirim permintaan lanjutan untuk meneruskan."


def _is_tool_needed(user_message):
    return bool(user_message and user_message.strip())


__all__ = ["RexaAgent", "ToolRegistry", "MemoryManager", "EvolutionEngine", "LLMRouter"]
