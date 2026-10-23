"""The published atlas must contain only curated research and renderable assets."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("viewsource_site_builder", ROOT / "scripts/build_site.py")
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


class AtlasTests(unittest.TestCase):
    def test_atlas_build_and_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "atlas"
            result = builder.build(dest)
            self.assertEqual(len(result["specimens"]), 1)
            self.assertEqual(len(result["versions"]), 2)
            self.assertTrue((dest / "index.html").exists())
            self.assertTrue((dest / "app.css").exists())
            self.assertTrue((dest / "app.js").exists())
            self.assertTrue((dest / "explorer.js").exists())
            self.assertTrue((dest / "chat-graph.js").exists())
            self.assertTrue((dest / ".nojekyll").exists())
            data = json.loads((dest / "data/catalog.json").read_text(encoding="utf-8"))
            current = next(v for v in data["versions"] if v["version"] == 2)
            self.assertEqual(len(current["chapters"]), 14)
            self.assertEqual(len(current["visuals"]["technology"]["technologies"]), 11)
            self.assertEqual(len(current["visuals"]["page_map"]["nodes"]), 7)
            feature = current["visuals"]["feature_graph"]
            self.assertEqual(len(feature["machines"]), 3)
            self.assertEqual(len(feature["transitions"]), 20)
            self.assertEqual(len(feature["surfaces"]), 6)
            self.assertEqual(len(feature["domain_relations"]),8)
            self.assertEqual(current["visuals"]["chat_source_signals"]["summary"][0]["count"], 63)
            self.assertEqual(current["visuals"]["chat_source_signals"]["dom_controls"]["document"]["contenteditable_true"], 1)
            self.assertEqual(len(current["visuals"]["feature_research"]["tasks"]), 18)
            self.assertEqual(len(current["visuals"]["public_chat_actions"]["actions"]), 4)
            self.assertEqual(len(current["visuals"]["chat_export_format"]["fields"]), 4)
            self.assertEqual(len(current["visuals"]["chat_capabilities"]["entries"]), 8)

            self.assertTrue(all(t["evidence_status"] == "hypothesis" for t in feature["transitions"]))
            self.assertTrue((dest / feature["json_path"]).exists())
            self.assertEqual(json.loads((dest / feature["json_path"]).read_text(encoding="utf-8")), feature)

            self.assertEqual(current["visuals"]["module_imports"]["static_edges"], 236)
            self.assertEqual(len(current["visuals"]["module_imports"]["sources"]), 8)
            self.assertEqual(current["visuals"]["icons"]["matched_uses"], 92)
            self.assertEqual(current["visuals"]["css_system"]["distinct_tokens"], 2509)
            self.assertEqual(current["visuals"]["source_system"]["lexical_scopes"]["fetch_and_stream"], 5)
            source_queue = current["visuals"]["static_source_queue"]
            self.assertEqual(source_queue["task_count"], 33)
            self.assertEqual(source_queue["task_statuses"]["queued"], 23)
            self.assertEqual(source_queue["task_statuses"]["in_progress"], 10)
            self.assertEqual(len(source_queue["tasks"]), 33)
            branch = current["visuals"]["chat_branch_switch"]
            self.assertFalse(branch["live_selection_verified"])
            self.assertEqual(len(branch["stages"]),7)
            self.assertEqual(len(branch["relationships"]),10)
            self.assertEqual(len(branch["variant_derivation"]),5)
            self.assertEqual(branch["render_recomputation_link"]["source_ref"],"R-JS-072")
            self.assertEqual(set(branch["source_resources"]),{"R-JS-018","R-JS-069"})
            viewport = current["visuals"]["chat_virtual_viewport"]
            self.assertFalse(viewport["runtime_verified"])
            self.assertEqual(set(viewport["source_resources"]),{"R-JS-066","R-JS-069","R-JS-072"})
            self.assertEqual(len(viewport["windowing_rules"]),11)
            self.assertEqual(len(viewport["source_chain"]),7)
            self.assertEqual(len(viewport["module_anchors"]),4)
            self.assertEqual(len(viewport["branch_window"]["stages"]),4)
            self.assertEqual(len(viewport["composer_spacer"]["stages"]),4)
            self.assertFalse(viewport["composer_spacer"]["verified_runtime"])
            self.assertFalse(viewport["branch_window"]["verified_runtime"])
            transcript = current["visuals"]["chat_transcript_render_trace"]
            self.assertFalse(transcript["runtime_render_verified"])
            self.assertEqual(len(transcript["stages"]),7)
            self.assertEqual(len(transcript["relationships"]),16)
            self.assertIn("selected_current_node",
                          transcript["page_recomputation"]["dependency_roles"])
            self.assertEqual(len(transcript["action_bindings"]),3)
            self.assertEqual(len(transcript["presentation_rules"]),9)
            self.assertEqual(transcript["cross_module_call"]["target_ref"],"R-JS-069")
            self.assertEqual(set(transcript["source_resources"]),{"R-JS-018","R-JS-066","R-JS-069","R-JS-072"})
            selectors = current["visuals"]["chat_selector_consumers"]
            self.assertFalse(selectors["source_executed"])
            self.assertEqual(len(selectors["selectors"]),5)
            self.assertEqual(len(selectors["consumers"]),7)
            self.assertEqual(len(selectors["ui_action"]["paths"]),3)
            self.assertEqual(selectors["ui_action"]["selector"],"current_turn_path")
            self.assertEqual(selectors["selectors"][0]["id"], "full_selected_path")
            self.assertEqual(selectors["selectors"][1]["id"], "current_turn_path")
            graph_write = current["visuals"]["chat_graph_mutation"]
            self.assertEqual(graph_write["source_ref"],"R-JS-018")
            self.assertFalse(graph_write["source_executed"])
            self.assertEqual(len(graph_write["operations"]),12)
            self.assertEqual(len(graph_write["call_sequence"]),11)
            self.assertIn("selected_user_message_ancestry",
                          graph_write["state_projection"]["field_roles"])
            transport = current["visuals"]["chat_transport_trace"]
            self.assertEqual(transport["source_ref"], "R-JS-018")
            self.assertEqual(transport["reviewed_method_count"], 5)
            self.assertEqual(len(transport["static_edges"]), 13)
            self.assertEqual(len(transport["message_state_write"]["source_steps"]),5)
            self.assertEqual(len(transport["decoded_pipeline"]["sequence"]),5)
            self.assertEqual(transport["generation_bridge"]["caller_function_ordinal"],9032)
            self.assertIn("onDecodedEvent",transport["generation_bridge"]["callbacks"])
            self.assertFalse(transport["live_transport_verified"])
            trace = current["visuals"]["chat_static_impl_trace"]
            self.assertEqual((trace["match_count"], trace["matched_functions"]), (15, 14))
            self.assertEqual(len(trace["reviewed_operations"]), 7)
            self.assertEqual(len(trace["direct_calls"]), 6)
            self.assertEqual(len(trace["reviewed_module_exports"]), 9)
            self.assertTrue(trace["open_static_questions"])
            ast = current["visuals"]["chat_ast_followup"]
            self.assertEqual((ast["parsed_bundles"], ast["candidate_functions"],
                              ast["candidate_bundles"]), (144,333,41))
            self.assertFalse(ast["verified_live_behavior"])
            self.assertTrue(ast["unresolved"])
            self.assertEqual(len(current["visuals"]["source_system"]["event_signals"]), 6)
            self.assertEqual(len(current["visuals"]["source_system"]["state_signals"]), 7)
            self.assertEqual(len(current["visuals"]["source_system"]["network_signals"]), 6)
            self.assertEqual(len(current["visuals"]["css_system"]["token_groups"]), 8)
            self.assertEqual(current["visuals"]["landmarks"]["button_total"], 130)
            self.assertEqual(next(v for v in data["versions"] if v["version"] == 1)["visuals"], {})
            self.assertEqual(len(current["findings"]), 86)
            self.assertEqual(len(current["tasks"]), 124)
            self.assertGreaterEqual(len(current["components"]), 270)
            self.assertEqual(current["status"], "researching")
            self.assertEqual(len([t for t in current["tasks"] if "-followup-deep-" in t["id"]]), 57)
            previous = next(v for v in data["versions"] if v["version"] == 1)
            self.assertEqual(previous["status"], "reviewed")
            self.assertEqual(previous["chapters"], [])
            serialized = (dest / "data/catalog.json").read_text(encoding="utf-8").lower()
            for token in ("page-snapshot-chatgpt.com", "source-dom.html", "session_token",
                          "SYNTHETIC_PRIVATE_EMAIL_SENTINEL", "SYNTHETIC_PRIVATE_USER_SENTINEL"):
                self.assertNotIn(token, serialized)

    def test_appearance_controls_and_no_external_framework(self):
        html = (ROOT / "site/index.html").read_text(encoding="utf-8")
        js = (ROOT / "site/app.js").read_text(encoding="utf-8")
        css = (ROOT / "site/app.css").read_text(encoding="utf-8")
        for mode in ("system", "light", "dark"):
            self.assertIn('value="' + mode + '"', html)
        self.assertIn('data-theme="system"', html)
        self.assertIn('prefers-color-scheme: dark', css)
        self.assertIn('viewsource:theme', js)
        self.assertIn('document.createElement', js)
        self.assertNotIn("innerHTML", js)
        self.assertIn('data/catalog.json', js)


if __name__ == "__main__":
    unittest.main()
