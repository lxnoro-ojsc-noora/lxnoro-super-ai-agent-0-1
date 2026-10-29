import unittest
import os
import shutil
from agent_memory import (
    init_db, store_long_term_memory, get_long_term_memories,
    search_long_term_memories, update_long_term_memory,
    delete_long_term_memory, clear_long_term_memories,
    get_relevant_memory_context, DB_DIR
)

class TestLongTermMemory(unittest.TestCase):

    def setUp(self):
        # Clear or reset test db
        if os.path.exists(DB_DIR):
            try:
                shutil.rmtree(DB_DIR)
            except Exception:
                pass
        init_db()

    def tearDown(self):
        if os.path.exists(DB_DIR):
            try:
                shutil.rmtree(DB_DIR)
            except Exception:
                pass

    def test_init_and_storage(self):
        mem_id = store_long_term_memory("preference", "ui_theme", "Dark mode preferred", importance=2)
        self.assertGreater(mem_id, 0)

        mems = get_long_term_memories()
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["memory_key"], "ui_theme")
        self.assertEqual(mems[0]["content"], "Dark mode preferred")
        self.assertEqual(mems[0]["category"], "preference")
        self.assertEqual(mems[0]["importance"], 2)

    def test_deduplication_and_conflict_resolution(self):
        # Store initial memory
        store_long_term_memory("project_context", "tech_stack", "Python 3.10", importance=1)
        # Upsert with same key (conflict resolution / update outdated info)
        store_long_term_memory("project_context", "tech_stack", "Python 3.11 with Streamlit", importance=3)

        mems = get_long_term_memories()
        self.assertEqual(len(mems), 1)  # No duplicate
        self.assertEqual(mems[0]["content"], "Python 3.11 with Streamlit")
        self.assertEqual(mems[0]["importance"], 3)

    def test_categorization_and_filtering(self):
        store_long_term_memory("preference", "editor", "VS Code", 1)
        store_long_term_memory("fact", "db_type", "SQLite", 2)

        prefs = get_long_term_memories("preference")
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["memory_key"], "editor")

        facts = get_long_term_memories("fact")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["memory_key"], "db_type")

        all_mems = get_long_term_memories("All")
        self.assertEqual(len(all_mems), 2)

    def test_local_relevance_scoring(self):
        store_long_term_memory("fact", "python_version", "Using Python 3.11 for development", 1)
        store_long_term_memory("preference", "formatting", "Always use Black formatter", 2)

        results = search_long_term_memories("Python development")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["memory_key"], "python_version")

    def test_context_injection_and_size_limits(self):
        store_long_term_memory("instruction", "rule_1", "Never execute arbitrary shell commands.", 5)
        store_long_term_memory("instruction", "rule_2", "Always validate paths.", 4)

        context_str = get_relevant_memory_context("shell commands security", max_chars=300)
        self.assertIn("<long_term_memory_context>", context_str)
        self.assertIn("Never execute arbitrary shell commands", context_str)
        self.assertIn("</long_term_memory_context>", context_str)

    def test_update_and_deletion(self):
        m_id = store_long_term_memory("decision", "framework", "Flask", 1)
        success = update_long_term_memory(m_id, "decision", "framework", "Streamlit", 3)
        self.assertTrue(success)

        mems = get_long_term_memories()
        self.assertEqual(mems[0]["content"], "Streamlit")
        self.assertEqual(mems[0]["importance"], 3)

        # Single delete
        delete_long_term_memory(m_id)
        self.assertEqual(len(get_long_term_memories()), 0)

        # Bulk clear
        store_long_term_memory("fact", "a", "b", 1)
        store_long_term_memory("fact", "c", "d", 1)
        self.assertEqual(len(get_long_term_memories()), 2)
        clear_long_term_memories()
        self.assertEqual(len(get_long_term_memories()), 0)

if __name__ == "__main__":
    unittest.main()
