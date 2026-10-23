"""Private ZIP-to-AST integration tests with invented source, never a user capture."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def parser_installed() -> bool:
    if not shutil.which("node"):
        return False
    result = subprocess.run(
        ["node", "-e", "require.resolve('acorn')"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False, timeout=10)
    return result.returncode == 0


@unittest.skipUnless(parser_installed(), "Node.js Acorn dependency unavailable")
class StaticImplementationArchiveTests(unittest.TestCase):
    def test_private_zip_traces_are_ordinals_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-capture.zip"
            sentinel = "synthetic-private-message-not-for-publication"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("assets/b.js",
                    "async function branch(client,c,m){return client.branch("
                    "{conversationId:c,messageId:m})};")
                z.writestr("assets/a.js",
                    "function factory(){"
                    "function dispatch(x){for(let n=x.regenerateFromMessageId;"
                    "n;){n=x.parentMessageId;if(x.children.length)break;}}"
                    "function submit(x){return dispatch(x)}"
                    "}" + "const original='" + sentinel + "';")
            process = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--chat-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(process.returncode, 0, "AST integration probe failed")
            report = json.loads(process.stdout)
            self.assertEqual(report["parsed_bundles"], 2)
            self.assertEqual(report["failed_bundles"], 0)
            self.assertEqual(report["pattern_counts"]["branch_transport_call"], 1)
            self.assertEqual(report["pattern_counts"]["generation_parent_selection"], 1)
            edges = report["direct_call_candidates"]
            self.assertEqual(len(edges), 1)
            self.assertEqual(edges[0]["source_ref"], "R-JS-001")
            self.assertEqual(edges[0]["module_factory_ordinal"], 1)
            self.assertEqual(edges[0]["caller_function_ordinal"], 3)
            self.assertEqual(edges[0]["callee_function_ordinal"], 2)
            self.assertNotIn(sentinel, process.stdout)
            self.assertNotIn("assets/a.js", process.stdout)
            self.assertNotIn(str(archive), process.stdout)

    def test_transport_trace_extracts_methods_without_source_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-transport.zip"
            sentinel = "PRIVATE_ONLY_SYNTHETIC_TEST_SENTINEL"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("fictional/transport.js",
                    "class Transport {"
                    "startCompletionStream(x){"
                    "const h=this.createCompletionStreamHandlers({onEvent:x.onEvent});"
                    "return Request.streamPost('fictional',h)}"
                    "resumeCompletionStream(x){const h=this.createCompletionStreamHandlers("
                    "{resumeState:x,onResume:x.onResume});"
                    "return x.topic?h.startFromTopic(x.topic):Request.streamPost('fictional',h)}"
                    "cancelStream(x){this.completionCancellations.delete(x);"
                    "Request.cancelStream(x)}"
                    "getStreamOptions(){return {parseEventData:x=>x}}"
                    "createCompletionStreamHandlers(x){return {"
                    "onPrematureTermination:x.onPrematureTermination,retryConfig:{maxRetryCount:3}}}"
                    "};const unused='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--transport-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic transport probe failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["parsed_bundles"], 1)
            self.assertEqual(report["failed_bundles"], 0)
            self.assertEqual(len(report["method_records"]), 5)
            methods = {m["method"]: m for m in report["method_records"]}
            self.assertIn("stream_post", methods["startCompletionStream"]["operations"])
            self.assertIn("topic_start", methods["resumeCompletionStream"]["operations"])
            self.assertIn("request_cancel", methods["cancelStream"]["operations"])
            self.assertIn("event_decoder", methods["getStreamOptions"]["operations"])
            self.assertIn("retry_configuration",
                          methods["createCompletionStreamHandlers"]["operations"])
            self.assertNotIn(sentinel, result.stdout)
            self.assertNotIn(str(archive), result.stdout)

    def test_selector_probe_avoids_publishing_private_message_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "fictional-selected-messages.zip"
            sentinel = "SYNTHETIC_PRIVATE_SELECTOR_SENTINEL"
            with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("app.js",
                    "function messages(x){let p=x.current_node,a=[];"
                    "while(p){let n=x.mapping[p];a.push(n.message);p=n.parent}"
                    "return a.reverse().map(String)}"
                    "function refs(x){return x.metadata.automation_id?["
                    "{automationId:x.id,messageId:x.id,source:'metadata'}]:[]}"
                    "const privateText='" + sentinel + "';")
            test = subprocess.run(
                ["python3", str(ROOT/"scripts/trace_static_archive.py"),
                 "--input", str(source), "--selector-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(test.returncode,0, "Synthetic selector archive failed")
            result=json.loads(test.stdout)
            self.assertEqual(result["parsed_bundles"],1)
            self.assertEqual(result["failed_bundles"],0)
            self.assertEqual(result["pattern_counts"]["selected_ancestry_message_walk"],1)
            self.assertEqual(result["pattern_counts"]["automation_reference_extraction"],1)
            self.assertNotIn(sentinel,test.stdout)
            self.assertNotIn(str(source),test.stdout)

    def test_transcript_candidate_probe_uses_private_zip_ordinals(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-message-presentation.zip"
            sentinel = "SYNTHETIC_TRANSCRIPT_SECRET_DO_NOT_INCLUDE"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("fictional/app.js",
                    "function derive(){return {messages:[],turns:[],renderedTurns:[]}}"
                    "function prepare(){return {renderedConversation:{},renderedTurns:[],"
                    "showPendingLoadingMessage:false}}"
                    "function filter(e){let hidden=e.hideInitialUserMessage;"
                    "return e.turn.items.filter(x=>x.type==='user-message')}"
                    "function wrapper(e){return {'data-message-id':e.id,"
                    "'data-message-author-role':'user',"
                    "'data-source-message-ids':e.sources}}"
                    "function variants(x){return x.variantIds[x.activeVariantIndex]"
                    "+'Previous response'+'Next response'}"
                    "function persist(x){return API.safePatch('fictional',"
                    "{requestBody:{current_node_id:x.id}})}"
                    "function eligible(x){let p=x.parent,c=x.children;"
                    "return {rawVariantCount:c.length,variantIds:c,"
                    "activeVariantIndex:c.findIndex(Boolean)}}"
                    "function selection(e){const x='[data-markdown-text-style=assistant]';"
                    "const y='data-chatgpt-selection-message-id';"
                    "const z='[data-markdown-copy=exclude]';"
                    "return e.closest(x)&&e.intersectsNode(z)&&y}"
                    "function copy(e){const c=new AbortController();"
                    "if(e.copyLastCodeBlock&&e.codeBlockIndex)return c.abort()}"
                    "const secret='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--transcript-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Transcript ZIP probe failed")
            report=json.loads(result.stdout)
            self.assertEqual(report["parsed_bundles"], 1)
            self.assertEqual(report["failed_bundles"], 0)
            for pattern in ("render_turn_derivation", "pending_turn_preparation",
                            "first_user_item_filter", "message_dom_identity_wrapper",
                            "response_variant_navigation","response_selection_request",
                            "eligible_variant_derivation",
                            "selected_markdown_range_validation",
                            "code_block_copy_recovery"):
                self.assertEqual(report["pattern_counts"][pattern], 1)
            self.assertTrue(all(x["source_ref"]=="R-JS-001"
                                and x["classification"]=="candidate_static_syntax"
                                and not x["render_behavior_verified"]
                                for x in report["matches"]))
            self.assertNotIn(sentinel, result.stdout)
            self.assertNotIn(str(archive), result.stdout)

    def test_viewport_candidate_probe_has_no_source_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-viewport.zip"
            sentinel = "SYNTHETIC_ONLY_VIEWPORT_SENTINEL"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("fictional/window.js",
                    "function layout(){const estimatedHeightPx=250,"
                    "measuredHeightsByKey={},turnKey='local';"
                    "const overscanCount=2,viewportHeightPx=900,"
                    "bottomOffsetsPx=[],retainedTurnKeys=[],turnIndexByKey=new Map();"
                    "return [estimatedHeightPx,overscanCount,retainedTurnKeys]}"
                    "const onlyPrivate='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--viewport-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic viewport probe failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["parsed_bundles"], 1)
            self.assertEqual(report["failed_bundles"], 0)
            self.assertEqual(report["counts"]["measured_estimated_layout"], 1)
            self.assertEqual(report["counts"]["viewport_overscan_range"], 1)
            self.assertEqual(report["counts"]["retained_outside_window"], 1)
            self.assertTrue(all(item["classification"] == "syntactic_candidate"
                                and not item["domain_ownership_verified"]
                                for item in report["matches"]))
            self.assertNotIn(sentinel, result.stdout)
            self.assertNotIn(str(archive), result.stdout)

    def test_anonymous_module_graph_from_two_bundle_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-module-imports.zip"
            sentinel = "PRIVATE_MODULE_SENTINEL_NO_PUBLICATION"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js",
                    "export const __webpack_modules__={"
                    "Alpha:(function(e,t,n){const b=n('Beta');t.a=()=>b.a}),"
                    "Beta:(function(e,t,n){t.a=()=>'" + sentinel + "'})};")
                z.writestr("b.js",
                    "export const __webpack_modules__={"
                    "Gamma:(function(e,t,n){const a=n('Alpha');"
                    "const missing=n('External');t.a=a})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic module graph analysis failed")
            graph = json.loads(result.stdout)
            self.assertEqual(graph["parsed_bundles"], 2)
            self.assertEqual(graph["modules_total"], 3)
            self.assertEqual(graph["unique_resolved_links"], 2)
            self.assertEqual(graph["unresolved_import_candidates"], 1)
            self.assertEqual(graph["cross_bundle_links"], 1)
            self.assertTrue(all(not x["runtime_import_verified"]
                                for x in graph["resolved_links"]))
            for secret in (sentinel, "Alpha", "Beta", "Gamma", "External",
                           str(archive), "a.js", "b.js"):
                self.assertNotIn(secret, result.stdout)

    def test_non_zip_input_is_rejected_without_dumping_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "private-secret-invalid.zip"
            original.write_text("not a ZIP")
            process = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(original), "--chat-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=15)
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn("private-secret-invalid", process.stderr)


if __name__ == "__main__":
    unittest.main()
