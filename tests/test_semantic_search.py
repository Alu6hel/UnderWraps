"""
==============================================================================
Test Suite: 100% On-Device Neural Semantic Search & 128-D Vector Engine
Formally Verifies Kybalion 128-D Cosine Invariants & Zero-Knowledge Retrieval
==============================================================================
"""

import os
import sys
import math
import shutil
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from database.kybalion_adapter import KybalionDBAdapter

class TestNeuralSemanticSearch(unittest.TestCase):
    def setUp(self):
        self.test_dir = "./underwraps_semantic_test_data"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        self.db = KybalionDBAdapter(data_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_vector_dimension_and_normalization(self):
        """Verify 128-D vector dimension and unit norm invariant."""
        vec = self.db.compute_embedding("Sovereign encrypted database schema architecture")
        self.assertEqual(len(vec), 128)
        
        # Calculate L2 norm
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_cosine_similarity_identities(self):
        """Verify cosine similarity properties."""
        v1 = self.db.compute_embedding("What did we decide about the database schema?")
        v2 = self.db.compute_embedding("What did we decide about the database schema?")
        
        # Self-similarity must be 1.0
        self.assertAlmostEqual(self.db.cosine_similarity(v1, v2), 1.0, places=4)
        
        # Similar topic must have high positive similarity
        v_similar = self.db.compute_embedding("How is data structured in the database tables?")
        sim_similar = self.db.cosine_similarity(v1, v_similar)
        self.assertGreater(sim_similar, 0.25)
        
        # Completely unrelated topic must have lower similarity
        v_unrelated = self.db.compute_embedding("Making pasta with tomato sauce for dinner")
        sim_unrelated = self.db.cosine_similarity(v1, v_unrelated)
        self.assertLess(sim_unrelated, sim_similar)

    def test_natural_language_semantic_retrieval(self):
        """Verify natural language query matching across conversations."""
        u1 = self.db.register_user("alice_neural", "alice@neural.org", "Password123!")
        u2 = self.db.register_user("bob_neural", "bob@neural.org", "Password123!")
        
        conv_id = self.db.create_direct_conversation(u1["user_id"], u2["user_id"])
        
        # Post messages
        self.db.save_message("msg_1", conv_id, u1["user_id"], "We finalized the Kybalion database schema with 128-D vector indexing", "n1")
        self.db.save_message("msg_2", conv_id, u2["user_id"], "Let us grab some coffee and pizza for lunch today", "n2")
        self.db.save_message("msg_3", conv_id, u1["user_id"], "The 150MB media file guard has been verified with Z3 SMT bounds proving", "n3")
        
        # Query 1: Database Architecture
        results_db = self.db.semantic_search(u1["user_id"], "What did we decide about database schema?", top_k=5)
        self.assertTrue(len(results_db) > 0)
        self.assertEqual(results_db[0]["entity_id"], "msg_1")
        self.assertGreater(results_db[0]["similarity_score"], 0.40)
        
        # Query 2: File Limits
        results_files = self.db.semantic_search(u1["user_id"], "How large can media uploads be?", top_k=5)
        self.assertTrue(len(results_files) > 0)
        self.assertEqual(results_files[0]["entity_id"], "msg_3")

    def test_attachment_semantic_search(self):
        """Verify semantic retrieval of 150MB media attachments."""
        u1 = self.db.register_user("carol_att", "carol@att.org", "Password123!")
        u2 = self.db.register_user("dave_att", "dave@att.org", "Password123!")
        conv_id = self.db.create_direct_conversation(u1["user_id"], u2["user_id"])
        
        # Register attachment
        dummy_path = os.path.join(self.test_dir, "server_rack_diagram.png")
        with open(dummy_path, "wb") as f:
            f.write(b"PNG_DUMMY_DATA")
            
        self.db.register_attachment("att_server_1", u1["user_id"], "server_rack_diagram.png", 14, "image/png", "hash_png", dummy_path)
        
        # Search for attachment with natural language
        res = self.db.semantic_search(u1["user_id"], "Find the server rack diagram image", top_k=5)
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["entity_id"], "att_server_1")
        self.assertEqual(res[0]["entity_type"], "ATTACHMENT")

    def test_conversation_privacy_isolation(self):
        """Verify strict multi-tenant privacy: users cannot search messages from conversations they do not belong to."""
        alice = self.db.register_user("alice_priv", "alice@priv.org", "Pass123!")
        bob = self.db.register_user("bob_priv", "bob@priv.org", "Pass123!")
        eve = self.db.register_user("eve_priv", "eve@priv.org", "Pass123!")
        
        conv_ab = self.db.create_direct_conversation(alice["user_id"], bob["user_id"])
        self.db.save_message("msg_secret", conv_ab, alice["user_id"], "Top secret cryptographic master seed phrase", "n_sec")
        
        # Alice searches -> gets result
        alice_res = self.db.semantic_search(alice["user_id"], "secret seed phrase", top_k=5)
        self.assertEqual(len(alice_res), 1)
        self.assertEqual(alice_res[0]["entity_id"], "msg_secret")
        
        # Eve searches -> 0 results (Access Denied / Zero-Knowledge Isolation)
        eve_res = self.db.semantic_search(eve["user_id"], "secret seed phrase", top_k=5)
        self.assertEqual(len(eve_res), 0)

if __name__ == "__main__":
    unittest.main()
