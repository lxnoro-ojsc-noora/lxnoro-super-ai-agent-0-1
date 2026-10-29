import os
import sqlite3
import unittest
from agent_memory import init_db, create_task, get_steps, DB_PATH
from execution_engine import get_next_eligible_step, execute_step, recover_interrupted_steps

class TestExecutionEngine(unittest.TestCase):

    def setUp(self):
        init_db()
        # Clean tasks/steps for testing
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM steps")
        cursor.execute("DELETE FROM memory_logs")
        conn.commit()
        conn.close()

    def test_next_eligible_step_and_dependency(self):
        task_id = create_task("Test Goal", 3)
        steps = get_steps(task_id)
        
        # Step 1 should be eligible (no deps)
        next_step = get_next_eligible_step(task_id)
        self.assertIsNotNone(next_step)
        self.assertEqual(next_step['step_number'], 1)
        
        # Try executing Step 2 before Step 1 is completed -> should be blocked by dependency
        step2 = steps[1]
        success, msg = execute_step(step2['id'], command_runner_enabled=False)
        self.assertFalse(success)
        self.assertIn("BLOCKED", msg)

        # Execute Step 1 successfully
        success, msg = execute_step(next_step['id'], command_runner_enabled=False)
        self.assertTrue(success)
        
        # Now Step 2 should be eligible
        next_step_2 = get_next_eligible_step(task_id)
        self.assertIsNotNone(next_step_2)
        self.assertEqual(next_step_2['step_number'], 2)

    def test_startup_recovery(self):
        task_id = create_task("Recovery Test", 2)
        steps = get_steps(task_id)
        
        # Force Step 1 into RUNNING state to simulate interruption
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE steps SET status = 'RUNNING' WHERE id = ?", (steps[0]['id'],))
        conn.commit()
        conn.close()
        
        # Run recovery check
        recover_interrupted_steps(task_id)
        
        # Verify Step 1 recovered to PENDING
        steps_after = get_steps(task_id)
        self.assertEqual(steps_after[0]['status'], 'PENDING')

    def test_bounded_retries(self):
        task_id = create_task("Retry Test", 1)
        steps = get_steps(task_id)
        step_id = steps[0]['id']
        
        # Force simulate failure behavior by forcing an invalid condition or testing retry increment
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE steps SET status = 'FAILED', retry_count = 2 WHERE id = ?", (step_id,))
        conn.commit()
        conn.close()
        
        # Next retry (attempt 3) should be allowed, then max out
        next_step = get_next_eligible_step(task_id)
        self.assertIsNotNone(next_step)
        self.assertEqual(next_step['retry_count'], 2)

if __name__ == "__main__":
    unittest.main()
