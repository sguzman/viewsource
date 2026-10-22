"""Synthetic message graph invariants, independent of the examined website."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("chat_graph_core",ROOT / "scripts/chat_graph_core.py")
core=importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys
sys.modules[spec.name]=core
spec.loader.exec_module(core)


class ChatGraphCoreTests(unittest.TestCase):
    def example(self):
        graph=core.ConversationGraph("synthetic-chat")
        graph.add("root",None,"user")
        graph.add("reply-one","root","assistant")
        graph.add("reply-two","root","assistant")
        return graph

    def test_selected_visible_path(self):
        graph=self.example()
        self.assertEqual(graph.select("reply-two"),("root","reply-two"))
        self.assertEqual(graph.selected_leaf,"reply-two")
        self.assertEqual(graph.local_structure()["selected_path"],["root","reply-two"])

    def test_alternatives_preserved(self):
        graph=self.example()
        graph.select("reply-one")
        graph.select("reply-two")
        self.assertEqual(len(graph.nodes),3)
        self.assertEqual([n.local_key for n in graph.siblings("reply-one")],["reply-two"])
        self.assertEqual([n.local_key for n in graph.children("root")],["reply-one","reply-two"])

    def test_parent_before_child_and_duplicate_rejected(self):
        graph=core.ConversationGraph("synthetic")
        with self.assertRaises(core.GraphError):
            graph.add("orphan","absent","user")
        graph.add("root",None,"user")
        with self.assertRaises(core.GraphError):
            graph.add("root",None,"assistant")
        with self.assertRaises(core.GraphError):
            graph.add("invalid","root","system")

    def test_root_cannot_be_selected_as_leaf_with_children(self):
        graph=self.example()
        with self.assertRaises(core.GraphError):
            graph.select("root")
        self.assertEqual(graph.select(None),())

    def test_unknown_selection_is_error_not_new_node(self):
        graph=self.example()
        with self.assertRaises(core.GraphError):
            graph.select("not-in-model")
        self.assertEqual(len(graph.nodes),3)

    def test_fork_is_independent_root_not_implicit_copy(self):
        forest=core.ConversationForest()
        origin=forest.new_chat("synthetic-original")
        origin.add("root",None,"user")
        other=forest.new_chat("synthetic-branch")
        edge=forest.annotate_candidate_fork("synthetic-original","root","synthetic-branch")
        self.assertEqual(edge.source_message_key,"root")
        self.assertEqual(other.nodes,())
        with self.assertRaises(core.GraphError):
            forest.annotate_candidate_fork("synthetic-original","root","synthetic-branch")

    def test_cross_chat_links_require_existing_ids(self):
        forest=core.ConversationForest()
        forest.new_chat("original")
        forest.new_chat("fork")
        with self.assertRaises(core.GraphError):
            forest.annotate_candidate_fork("original","missing","fork")
        with self.assertRaises(core.GraphError):
            forest.annotate_candidate_fork("original","missing","unknown")
        with self.assertRaises(core.GraphError):
            forest.annotate_candidate_fork("original","missing","original")


if __name__=="__main__":
    unittest.main()
