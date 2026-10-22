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

    def test_selected_leaf_is_cleared_after_a_child_is_added(self):
        graph=core.ConversationGraph("synthetic")
        graph.add("root",None,"user")
        graph.select("root")
        graph.add("reply","root","assistant")
        self.assertIsNone(graph.selected_leaf)
        self.assertEqual(graph.select("reply"),("root","reply"))

    def test_cross_chat_cycle_is_rejected(self):
        forest=core.ConversationForest()
        a=forest.new_chat("a")
        b=forest.new_chat("b")
        c=forest.new_chat("c")
        a.add("a1",None,"user")
        b.add("b1",None,"user")
        c.add("c1",None,"user")
        forest.annotate_candidate_fork("a","a1","b")
        forest.annotate_candidate_fork("b","b1","c")
        with self.assertRaises(core.GraphError):
            forest.annotate_candidate_fork("c","c1","a")
        self.assertEqual(len(forest.forks),2)

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


    def test_anonymous_topology_does_not_retain_input_keys(self):
        chat=core.ConversationGraph("caller-supplied-chat-key")
        chat.add("caller-supplied-first",None,"user")
        chat.add("caller-supplied-second","caller-supplied-first","assistant")
        chat.select("caller-supplied-second")
        exported=chat.anonymous_topology()
        self.assertEqual(exported["selected_path"],["n0001","n0002"])
        self.assertEqual(exported["nodes"][1]["parent"],"n0001")
        self.assertEqual(exported["node_count"],2)
        import json
        serialized=json.dumps(exported)
        self.assertNotIn("caller-supplied",serialized)

    def test_structural_equivalence_ignores_arbitrary_local_keys(self):
        a=core.ConversationGraph("synthetic-a")
        a.add("first",None,"user")
        a.add("response-one","first","assistant")
        a.add("response-two","first","assistant")
        a.select("response-two")
        b=core.ConversationGraph("synthetic-b")
        b.add("alpha",None,"user")
        b.add("beta","alpha","assistant")
        b.add("gamma","alpha","assistant")
        b.select("gamma")
        self.assertEqual(a.anonymous_topology(),b.anonymous_topology())
        self.assertEqual(a.anonymous_topology(),a.anonymous_topology())

    def test_cross_chat_projection_contains_only_ordinal_links(self):
        forest=core.ConversationForest()
        original=forest.new_chat("private-placeholder-origin")
        original.add("node-placeholder",None,"user")
        branch=forest.new_chat("private-placeholder-branch")
        branch.add("other-node",None,"user")
        forest.annotate_candidate_fork("private-placeholder-origin",
                                       "node-placeholder","private-placeholder-branch")
        exported=forest.anonymous_topology()
        self.assertEqual(exported["conversation_count"],2)
        self.assertEqual(exported["candidate_forks"],[
            {"source_chat":"c0001","source_node":"n0001","destination_chat":"c0002"}])
        import json
        self.assertNotIn("private-placeholder",json.dumps(exported))


    def test_structural_count_deltas_without_input_keys(self):
        chat=core.ConversationGraph("invented-conversation")
        before=chat.topology_metrics()
        chat.add("first-opaque-key",None,"user")
        chat.add("first-answer-key","first-opaque-key","assistant")
        chat.select("first-answer-key")
        middle=chat.topology_metrics()
        chat.add("alternative-answer-key","first-opaque-key","assistant")
        after=chat.topology_metrics()
        self.assertEqual(before["node_count"],0)
        self.assertEqual(middle["parent_edge_count"],1)
        self.assertEqual(after["branch_point_count"],1)
        self.assertEqual(after["alternative_child_count"],1)
        self.assertEqual(after["selected_path_length"],0)
        compared=core.compare_topology_metrics(middle,after)
        self.assertEqual(compared["changes"]["node_count"],1)
        self.assertEqual(compared["changes"]["alternative_child_count"],1)
        self.assertEqual(compared["changes"]["selected_path_length"],-2)
        self.assertFalse(compared["website_behavior_verified"])
        import json
        self.assertNotIn("opaque-key",json.dumps(compared))

    def test_topology_metrics_ignore_arbitrary_keys_and_insertion_order(self):
        chat_a=core.ConversationGraph("invented-alpha")
        chat_a.add("root",None,"user")
        chat_a.add("left","root","assistant")
        chat_a.add("right","root","assistant")
        chat_b=core.ConversationGraph("invented-beta")
        chat_b.add("other-root",None,"user")
        chat_b.add("other-right","other-root","assistant")
        chat_b.add("other-left","other-root","assistant")
        self.assertEqual(chat_a.topology_metrics(),chat_b.topology_metrics())

    def test_forest_metric_counts_forks_without_names(self):
        forest=core.ConversationForest()
        first=forest.new_chat("fictional-first")
        first.add("root",None,"user")
        second=forest.new_chat("fictional-second")
        before=forest.topology_metrics()
        forest.annotate_candidate_fork("fictional-first","root","fictional-second")
        after=forest.topology_metrics()
        self.assertEqual(after["conversation_count"],2)
        self.assertEqual(after["candidate_fork_count"],1)
        self.assertEqual(
            core.compare_topology_metrics(before,after)["changes"]["candidate_fork_count"],1)

    def test_reject_extra_fields_in_structural_comparison(self):
        graph=core.ConversationGraph("fiction")
        metrics=graph.topology_metrics()
        with self.assertRaises(core.GraphError):
            core.compare_topology_metrics(metrics,{**metrics,"original_message_id":1})
        with self.assertRaises(core.GraphError):
            core.compare_topology_metrics(metrics,{**metrics,"node_count":True})
        with self.assertRaises(core.GraphError):
            core.compare_topology_metrics(metrics,{**metrics,"node_count":-1})


if __name__=="__main__":
    unittest.main()
