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
    def test_top_level_bootstrap_excludes_shadowed_and_rebound_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-top-level-bootstrap-scopes.zip"
            key = "PrivateBootstrapModuleZ998"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js", "export const __webpack_modules__={"
                    + key + ":function(){}};"
                    "{const __webpack_require__=()=>0;"
                    "__webpack_require__('" + key + "')}"
                    "if(flag){__webpack_require__=()=>0}"
                    "__webpack_require__('" + key + "')")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            graph = json.loads(proc.stdout)
            self.assertEqual(graph["bootstrap_call_candidates"], 0)
            self.assertEqual(graph["modules_total"], 1)
            for value in (key, "fictional-top-level-bootstrap-scopes.zip"):
                self.assertNotIn(value, proc.stdout)

    def test_chunk_root_provenance_is_source_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "source-limited-chunk.zip"
            private_key = "webpackChunkSecretRootFixture"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("entry.js",
                    "(self." + private_key + "=self." + private_key + "||[]).push("
                    "[[1],{100:function(e,t,n){t.a=1}},function(n){n(100)}]);")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-frontier",
                 "--bootstrap-candidates"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["bootstrap_root_provenance"][0]["candidate_kinds"],
                             ["chunk_runtime_literal_call_candidate"])
            self.assertEqual(data["bootstrap_root_provenance"][0]["matching_static_calls"], 1)
            self.assertFalse(data["bootstrap_root_provenance"][0]["execution_verified"])
            for private in (private_key, "source-limited-chunk.zip", "entry.js"):
                self.assertNotIn(private, proc.stdout)

    def test_direct_iife_loader_reassignment_excludes_startup_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-iife-mutation.zip"
            private = "webpackChunkPrivateImmediatelyInvokedZ991"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js", "(self." + private + "=self." + private
                    + "||[]).push([[1],{100:function(e,t,n){t.a=1}},"
                    "function(n){(()=>{n=()=>1})();n(100)}]);")
            run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(run.returncode, 0)
            data = json.loads(run.stdout)
            self.assertEqual(data["bootstrap_call_candidates"], 0)
            for private_value in (private, "fictional-iife-mutation.zip"):
                self.assertNotIn(private_value, run.stdout)

    def test_chunk_loader_reassigned_by_iteration_or_destructuring(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-chunk-assignments.zip"
            base = "webpackChunkPrivateIterationZ985"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js", "(self." + base + "=self." + base
                    + "||[]).push([[1],{100:function(e,t,n){t.a=1}},"
                    "function(n){for(var n of [()=>1]){}n(100)}]);")
            run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(run.returncode, 0)
            data = json.loads(run.stdout)
            self.assertEqual(data["bootstrap_call_candidates"], 0)
            for private in (base, "fictional-chunk-assignments.zip"):
                self.assertNotIn(private, run.stdout)

    def test_block_local_chunk_loader_shadow_preserves_outer_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-shadowed-chunk-loader.zip"
            chunk = "webpackChunkShadowedRuntimeZ965"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js", "(self." + chunk + "=self." + chunk
                    + "||[]).push([[1],{100:function(e,t,n){t.a=1}},"
                    "function(n){if(true){const n=()=>1;n(999)}return n(100)}]);")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["bootstrap_call_candidates"], 1)
            self.assertEqual(data["bootstrap_candidates"][0]["classification"],
                             "unique_registry_key_candidate")
            for private in (chunk, "synthetic-shadowed-chunk-loader.zip"):
                self.assertNotIn(private, proc.stdout)

    def test_reassigned_chunk_runtime_loader_is_not_a_startup_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "reassigned-loader-fiction.zip"
            key = "webpackChunkReassignedPrivate"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js", "(self." + key + "=self." + key
                    + "||[]).push([[1],{100:function(e,t,n){t.a=1}},"
                    "function(n){if(Math.random())n=()=>1;return n(100)}]);")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertEqual(output["bootstrap_call_candidates"], 0)
            self.assertEqual(output["modules_total"], 1)
            for private in (key, "reassigned-loader-fiction.zip", "chunk.js"):
                self.assertNotIn(private, result.stdout)

    def test_chunk_runtime_callback_seeds_candidate_module_frontier(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-chunk-runtime.zip"
            private_name = "webpackChunkPrivateStartupFixtureZ"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js",
                    "(self." + private_name + "=self." + private_name
                    + "||[]).push([[1],{"
                    "100:function(e,t,n){const b=n(101)},"
                    "101:function(e,t,n){t.a=1}},"
                    "function(loader){return loader(100)}]);")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--bootstrap-candidates"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True,
                    check=False, timeout=40)
                self.assertEqual(proc.returncode, 0, proc.stderr[:100])
                report = json.loads(proc.stdout)
                if mode[0] == "--module-trace":
                    self.assertEqual(report["bootstrap_call_candidates"], 1)
                    self.assertEqual(report["bootstrap_candidates"][0]["bootstrap_kind"],
                                     "chunk_runtime_literal_call_candidate")
                    self.assertEqual(report["unique_resolved_links"], 1)
                    self.assertFalse(report["bootstrap_candidates"][0][
                        "bootstrap_execution_verified"])
                else:
                    self.assertEqual(report["reached_module_count"], 2)
                    self.assertEqual(report["root_source"], "bootstrap_syntax_candidate")
                    self.assertFalse(report["runtime_module_load_verified"])
                for token in (private_name, "invented-chunk-runtime.zip", "chunk.js"):
                    self.assertNotIn(token, proc.stdout)

    def test_module_coverage_records_parse_failure_and_skipped_large_js(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-coverage-census.zip"
            sentinel = "SYNTHETIC_CAPTURE_SECRETS_EXCLUDED"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js", "export const __webpack_modules__={"
                    "A:(function(e,t,n){t.x=1})};"
                    "__webpack_require__('A')")
                z.writestr("b.js", "const malformedPrivate = ; " + sentinel)
                z.writestr("c.js", " " * (8 * 1024 * 1024 + 1))
            for option in (["--module-trace"],
                           ["--module-frontier", "--bootstrap-candidates"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *option],
                    cwd=ROOT, capture_output=True, text=True,
                    check=False, timeout=50)
                self.assertEqual(proc.returncode, 0, proc.stderr[:100])
                report = json.loads(proc.stdout)
                self.assertEqual(report["archive_candidate_script_count"], 3)
                self.assertEqual(report["archive_oversize_script_count"], 1)
                self.assertFalse(report["archive_all_scripts_parsed"])
                self.assertEqual(report["failed_parser_source_refs"], ["R-JS-002"])
                if option[0] == "--module-trace":
                    self.assertEqual(report["parsed_bundles"], 1)
                    self.assertEqual(report["failed_bundles"], 1)
                    self.assertEqual(report["archive_ast_input_script_count"], 2)
                else:
                    self.assertEqual(report["reached_module_count"], 1)
                for term in (sentinel, "invented-coverage-census.zip",
                             "a.js", "b.js", "c.js"):
                    self.assertNotIn(term, proc.stdout)

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
                    "async prepareCompletionStream(e,opt={}){let{shouldPrepare,"
                    "shouldRetry,signal}=opt;signal?.throwIfAborted();"
                    "if(shouldPrepare?.()===false)return;try{return await "
                    "Request.safePost('fictional',{})}catch(err){if(e.partial_query"
                    "&&shouldRetry?.()){await new Promise(done=>setTimeout(done,"
                    "250+250*Math.random()));return this.prepareCompletionStream("
                    "{...e,client_prepare_dispatch:'immediate'},"
                    "{...opt,shouldRetry:void 0,shouldPrepare:()=>true})}throw err}}"
                    "};const unused='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--transport-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic transport probe failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["parsed_bundles"], 1)
            self.assertEqual(report["failed_bundles"], 0)
            self.assertEqual(len(report["method_records"]), 6)
            methods = {m["method"]: m for m in report["method_records"]}
            self.assertIn("stream_post", methods["startCompletionStream"]["operations"])
            self.assertIn("topic_start", methods["resumeCompletionStream"]["operations"])
            self.assertIn("request_cancel", methods["cancelStream"]["operations"])
            self.assertIn("event_decoder", methods["getStreamOptions"]["operations"])
            self.assertIn("retry_configuration",
                          methods["createCompletionStreamHandlers"]["operations"])
            self.assertIn("partial_query_fallback_candidate",
                          methods["prepareCompletionStream"]["operations"])
            self.assertIn("one_shot_fallback_flag",
                          methods["prepareCompletionStream"]["operations"])
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

    def test_bootstrap_candidates_are_ordinals_not_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bootstrap-fiction.zip"
            sentinel = "SYNTHETIC_MODULE_PRIVATE_VALUE"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js",
                    "export const __webpack_modules__={"
                    "Entry:(function(e,t,n){t.a='" + sentinel + "'}),"
                    "Dormant:(function(e,t,n){const b=n('Entry');})};"
                    "__webpack_require__('Entry');"
                    "function unused(){__webpack_require__('Dormant')}")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic startup probe failed")
            graph = json.loads(result.stdout)
            self.assertEqual(graph["bootstrap_call_candidates"], 1)
            self.assertEqual(graph["bootstrap_candidates"][0]["classification"],
                             "unique_registry_key_candidate")
            self.assertEqual(graph["bootstrap_candidates"][0]["target_module"], 1)
            self.assertFalse(graph["bootstrap_runtime_verified"])
            self.assertFalse(graph["bootstrap_candidates"][0]["bootstrap_execution_verified"])
            for term in ("Entry", "Dormant", sentinel, "bootstrap-fiction.zip"):
                self.assertNotIn(term, result.stdout)

    def test_bootstrap_seed_to_bounded_frontier_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "invented-bootstrap.zip"
            sentinel = "SYNTHETIC_PRIVATE_BOOTSTRAP_SENTINEL"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("client/a.js",
                    "export const __webpack_modules__={"
                    "Root:(function(e,t,n){const child=n('Child');t.a=child.a}),"
                    "Child:(function(e,t,n){t.a='" + sentinel + "'}),"
                    "Unused:(function(e,t,n){t.a=0})};"
                    "__webpack_require__('Root')")
            probe = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(zip_path), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(probe.returncode, 0, "Module archive probe rejected synthetic ZIP")
            report = json.loads(probe.stdout)
            self.assertEqual(report["bootstrap_call_candidates"], 1)
            private_report = root / "private-ordinal-graph.json"
            private_report.write_text(probe.stdout, encoding="utf-8")
            analyzed = subprocess.run(
                ["node", str(ROOT / "scripts/trace_module_frontier.cjs"),
                 "--input", str(private_report),
                 "--bootstrap-candidates", "--max-depth", "3"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(analyzed.returncode, 0, "Bootstrap frontier rejected synthetic graph")
            summary = json.loads(analyzed.stdout)
            self.assertEqual(summary["root_source"], "bootstrap_syntax_candidate")
            self.assertEqual(summary["reached_module_count"], 2)
            self.assertEqual(summary["depth_counts"][0]["module_count"], 1)
            self.assertFalse(summary["source_executed"])
            self.assertFalse(summary["runtime_module_load_verified"])
            for private in ("Root", "Child", "Unused", sentinel, "invented-bootstrap.zip",
                            "private-ordinal-graph.json"):
                self.assertNotIn(private, analyzed.stdout)

    def test_module_exports_property_function_has_distinct_source_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-module-property-functions.zip"
            key = "PrivateModuleExportsPropertyZ992"
            secret = "PrivateShadowedModulePropertyZ992"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Caller:(function(m,t,n){const q=n('" + key + "');q.handler()}),"
                    + key + ":(function(m,t,n){m.exports.handler=()=>1;"
                    "function unused(m){m.exports." + secret + "=()=>2}})};")
                z.writestr("two.js", "export const __webpack_modules__={"
                    + key + ":(function(m,t,n){t.alternate=()=>3})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True,
                    check=False, timeout=40)
                self.assertEqual(proc.returncode, 0, proc.stderr[:100])
                data = json.loads(proc.stdout)
                if mode[0] == "--module-trace":
                    self.assertEqual(data["export_shape_candidate_count"], 1)
                    self.assertEqual(data["direct_function_export_site_count"], 2)
                    kinds = [x["classification"] for x in data["direct_function_export_sites"]]
                    self.assertIn("module_exports_property_function_candidate", kinds)
                else:
                    self.assertEqual(data["reached_module_count"], 1)
                    self.assertEqual(data["reachable_direct_function_export_site_count"], 0)
                for token in (key, secret, "synthetic-module-property-functions.zip"):
                    self.assertNotIn(token, proc.stdout)

    def test_replacing_module_exports_detaches_original_exports_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-detached-exports.zip"
            key = "PrivateDetachedModuleZ997"
            obsolete = "PrivateObsoletePropertyZ997"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Consumer:(function(e,t,n){const item=n('" + key + "');"
                    "item." + obsolete + "()}),"
                    + key + ":(function(e,t,n){t." + obsolete + "=()=>1;"
                    "e.exports=function(){return 1};t.later=()=>2})};")
                z.writestr("two.js", "export const __webpack_modules__={"
                    + key + ":(function(e,t,n){t.other=()=>1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            graph = json.loads(proc.stdout)
            self.assertEqual(graph["ambiguous_import_candidates"], 1)
            self.assertEqual(graph["export_shape_candidate_count"], 0)
            self.assertEqual(graph["direct_function_export_site_count"], 2)
            self.assertEqual(
                graph["direct_function_export_sites"][0]["classification"],
                "module_object_function_assignment_candidate")
            for secret in (key, obsolete, "synthetic-detached-exports.zip"):
                self.assertNotIn(secret, proc.stdout)

    def test_module_exports_function_candidate_is_not_shadowed_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-commonjs-exports.zip"
            sentinel = "PrivateFunctionOwner999"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "One:(function(module,exports,require){"
                    "module.exports=function(){return 1};"
                    "function unused(module){module.exports=()=>99}"
                    "}),"
                    "Two:(function(module,exports,require){"
                    "exports." + sentinel + "=()=>2})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["direct_function_export_site_count"], 2)
            self.assertEqual(
                [x["classification"] for x in report["direct_function_export_sites"]],
                ["module_object_function_assignment_candidate",
                 "direct_function_export_assignment_candidate"])
            for item in ("One", "Two", sentinel, "invented-commonjs-exports.zip"):
                self.assertNotIn(item, proc.stdout)

    def test_computed_registry_identifier_is_not_literal_module_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-computed-registry.zip"
            key = "PrivateComputedModuleKeyZ951"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){n('" + key + "');n(987654321)}),"
                    "[" + key + "]:(function(e,t,n){n(987654321)}),"
                    "[987654321]:(function(e,t){t.a=1})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
                self.assertEqual(proc.returncode, 0)
                report = json.loads(proc.stdout)
                self.assertEqual(report["registry_unresolved_computed_key_count"], 1)
                self.assertEqual(report["registry_nonfactory_entry_count"], 0)
                if mode[0] == "--module-trace":
                    self.assertEqual(report["unique_resolved_links"], 2)
                    self.assertEqual(report["unresolved_import_candidates"], 1)
                else:
                    self.assertEqual(report["reached_module_count"], 2)
                    self.assertEqual(report["reachable_unresolved_import_count"], 1)
                for private in (key, "Caller", "invented-computed-registry.zip"):
                    self.assertNotIn(private, proc.stdout)

    def test_nonfunction_registry_entry_is_not_an_import_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-nonfactory.zip"
            token = "PrivateNonCallableRegistryEntryZ"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){const a=n('" + token + "');"
                    "const b=n('ValidFactory')}),"
                    + token + ":42,"
                    "ValidFactory:(function(e,t){t.a=1})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
                self.assertEqual(proc.returncode, 0)
                report = json.loads(proc.stdout)
                self.assertEqual(report["registry_nonfactory_entry_count"], 1)
                if mode[0] == "--module-trace":
                    self.assertEqual(report["unique_resolved_links"], 1)
                    self.assertEqual(report["unresolved_import_candidates"], 1)
                else:
                    self.assertEqual(report["reached_module_count"], 2)
                    self.assertEqual(report["reachable_unresolved_import_count"], 1)
                for private in (token, "ValidFactory", "Caller", "invented-nonfactory.zip"):
                    self.assertNotIn(private, proc.stdout)

    def test_nested_loader_callsite_syntax_is_reported_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-nested-require.zip"
            sentinel = "NestedDeferredTargetFixtureZ954"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){n('" + sentinel + "');"
                    "function deferred(){n('" + sentinel + "');n('" + sentinel + "')}"
                    "function shadow(n){n('PrivateShadowedRequire')} }),"
                    + sentinel + ":(function(e,t){t.a=1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["literal_module_loader_call_expression_count"], 3)
            self.assertEqual(
                report["nested_function_literal_module_loader_call_expression_count"], 2)
            self.assertEqual(report["import_candidates"], 1)
            for private in (sentinel, "PrivateShadowedRequire",
                            "synthetic-nested-require.zip"):
                self.assertNotIn(private, proc.stdout)

    def test_literal_module_calls_count_repeated_syntax_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-literal-calls.zip"
            secret = "PrivateLiteralModuleKeyZ938"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){n('" + secret + "');n('" + secret + "')"
                    "}),"
                    + secret + ":(function(e,t,n){t.a=1})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
                self.assertEqual(proc.returncode, 0)
                report = json.loads(proc.stdout)
                if mode[0] == "--module-trace":
                    self.assertEqual(report["import_candidates"], 1)
                    self.assertEqual(report["literal_module_loader_call_expression_count"], 2)
                else:
                    self.assertEqual(
                        report["reachable_literal_module_loader_call_expression_count"], 2)
                    self.assertEqual(report["reached_module_count"], 2)
                for private in (secret, "invented-literal-calls.zip", "Caller"):
                    self.assertNotIn(private, proc.stdout)

    def test_direct_function_exports_exclude_shadowed_and_getter_functions(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-export-ownership.zip"
            sentinel = "SyntheticHiddenFunctionIdentifier"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){const m=n('Module');m.start()}),"
                    "Module:(function(e,t,n){"
                    "t.start=function(){return 1};"
                    "t.stop=()=>2;"
                    "function local(t){t." + sentinel + "=()=>3}"
                    "n.d(t,{wrapped:()=>local})})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True,
                    check=False, timeout=40)
                self.assertEqual(proc.returncode, 0)
                report = json.loads(proc.stdout)
                count = ("direct_function_export_site_count"
                         if mode[0] == "--module-trace"
                         else "reachable_direct_function_export_site_count")
                self.assertEqual(report[count], 2)
                for private in (sentinel, "Module", "Caller",
                                "fictional-export-ownership.zip"):
                    self.assertNotIn(private, proc.stdout)

    def test_unresolved_import_sites_are_ordinal_only_and_frontier_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-unresolved-sites.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js", "export const __webpack_modules__={"
                    "Root:(function(e,t,n){const a=n('MissingPrivateTarget');"
                    "const b=n('DuplicatePrivateTarget')}),"
                    "DuplicatePrivateTarget:(function(e,t,n){t.a=1})};")
                z.writestr("b.js", "export const __webpack_modules__={"
                    "DuplicatePrivateTarget:(function(e,t,n){t.b=1})};")
            for mode in (["--module-trace"],
                         ["--module-frontier", "--root", "R-JS-001:1"]):
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                     "--input", str(archive), *mode],
                    cwd=ROOT, capture_output=True, text=True,
                    check=False, timeout=40)
                self.assertEqual(proc.returncode, 0)
                report = json.loads(proc.stdout)
                if mode[0] == "--module-trace":
                    self.assertEqual(report["unresolved_import_site_count"], 2)
                    self.assertEqual(report["unresolved_import_candidates"], 1)
                    self.assertEqual(report["ambiguous_import_candidates"], 1)
                    categories = {x["classification"]
                                  for x in report["unresolved_import_sites"]}
                else:
                    self.assertEqual(report["reachable_unresolved_import_count"], 2)
                    self.assertEqual(report["reached_module_count"], 1)
                    categories = {x["classification"]
                                  for x in report["reachable_unresolved_import_sites"]}
                self.assertEqual(categories,
                                 {"missing_saved_target",
                                  "ambiguous_same_registry_target"})
                for private in ("Root", "MissingPrivateTarget",
                                "DuplicatePrivateTarget", "invented-unresolved-sites.zip"):
                    self.assertNotIn(private, proc.stdout)

    def test_foreign_chunk_keys_are_diagnostics_not_resolved_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "unrelated-chunk-fixture.zip"
            chunk_a = "webpackChunkPrivateOne"
            chunk_b = "webpackChunkPrivateTwo"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js",
                    "(self." + chunk_a + "=self." + chunk_a + "||[]).push([[1],{"
                    "100:function(e,t,n){const x=n(200)}}]);")
                z.writestr("b.js",
                    "(self." + chunk_b + "=self." + chunk_b + "||[]).push([[2],{"
                    "200:function(e,t,n){t.a=1}}]);")
            graph_run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(graph_run.returncode, 0)
            graph = json.loads(graph_run.stdout)
            self.assertEqual(graph["unresolved_import_candidates"], 1)
            self.assertEqual(graph["unique_resolved_links"], 0)
            self.assertEqual(graph["foreign_registry_key_collision_count"], 1)
            self.assertFalse(graph["foreign_registry_key_collisions"][0]["import_resolved"])
            for private in (chunk_a, chunk_b, "unrelated-chunk-fixture.zip"):
                self.assertNotIn(private, graph_run.stdout)

    def test_chunk_runtime_namespace_separates_reused_module_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-cross-runtime.zip"
            chunk_a = "webpackChunkFixtureAlphaPrivate"
            chunk_b = "webpackChunkFixtureBetaPrivate"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js",
                    "(self." + chunk_a + "=self." + chunk_a + "||[]).push([[1],{"
                    "100:function(e,t,n){const x=n(200)},"
                    "200:function(e,t,n){t.a=1}}]);")
                z.writestr("b.js",
                    "(window." + chunk_b + "=window." + chunk_b + "||[]).push([[2],{"
                    "200:function(e,t,n){t.b=1},"
                    "300:function(e,t,n){const x=n(100)}}]);")
                z.writestr("c.js",
                    "(globalThis." + chunk_a + "=globalThis." + chunk_a
                    + "||[]).push([[3],{"
                    "400:function(e,t,n){const x=n(200)}}]);")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["modules_total"], 5)
            self.assertEqual(report["registry_runtime_scope_count"], 2)
            self.assertTrue(report["chunk_runtime_isolation_applied"])
            self.assertEqual(report["import_candidates"], 3)
            self.assertEqual(report["unique_resolved_links"], 2)
            self.assertEqual(report["unresolved_import_candidates"], 1)
            self.assertEqual(report["ambiguous_import_candidates"], 0)
            self.assertEqual(report["cross_bundle_links"], 1)
            for secret in (chunk_a, chunk_b, "invented-cross-runtime.zip",
                           "a.js", "b.js", "c.js"):
                self.assertNotIn(secret, proc.stdout)

    def test_web_pack_chunk_registration_yields_only_anonymous_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-chunk-fixture.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("chunk.js",
                    "(self['webpackChunkFixtureSecret']=" 
                    "self['webpackChunkFixtureSecret']||[]).push([[7],{"
                    "901234:function(e,t,n){const x=n(901235)},"
                    "901235:function(e,t,n){t.a=1}}]);")
            run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(run.returncode, 0)
            report = json.loads(run.stdout)
            self.assertEqual(report["modules_total"], 2)
            self.assertEqual(report["unique_resolved_links"], 1)
            self.assertFalse(report["module_runtime_loaded_verified"])
            for token in ("webpackChunkFixtureSecret", "901234", "901235",
                          "invented-chunk-fixture.zip", "chunk.js"):
                self.assertNotIn(token, run.stdout)

    def test_ordinary_top_level_registry_declaration_is_analyzed(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-declarations.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "var __webpack_modules__={"
                    "Alpha:function(e,t,n){const x=n('Beta')},"
                    "Beta:function(e,t,n){t.a=1}};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["modules_total"], 2)
            self.assertEqual(data["unique_resolved_links"], 1)
            for item in ("Alpha", "Beta", "bundle.js", "invented-declarations.zip"):
                self.assertNotIn(item, proc.stdout)

    def test_integer_registry_keys_resolve_without_publishing_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "integer-module-specimen.zip"
            keys = ("871997334455", "871997334456")
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("synthetic.js", "export const __webpack_modules__={"
                    + keys[0] + ":(function(e,t,n){const x=n(" + keys[1] + ");"
                    "const later=n.bind(n," + keys[1] + ")}),"
                    + keys[1] + ":(function(e,t,n){t.a=1})};"
                    "__webpack_require__(" + keys[0] + ");")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["unique_resolved_links"], 1)
            self.assertEqual(report["bootstrap_call_candidates"], 1)
            self.assertEqual(report["bound_import_candidate_count"], 1)
            self.assertEqual(report["dynamic_boundary_count"], 0)
            for private in (*keys, "integer-module-specimen.zip", "synthetic.js"):
                self.assertNotIn(private, proc.stdout)

    def test_computed_module_keys_cannot_be_mistaken_for_resolved_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-dynamic-require.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("script.js", "export const __webpack_modules__={"
                    "Main:(function(e,t,n){const x=n(t.privateKey);"
                    "function unrelated(n){n(t.otherKey);n.e('unused')}})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["import_candidates"], 0)
            self.assertEqual(data["dynamic_boundary_count"], 1)
            self.assertEqual(data["dynamic_boundary_candidates"][0]["pattern"],
                             "computed_module_require_candidate")
            self.assertNotIn("privateKey", proc.stdout)
            self.assertNotIn("invented-dynamic-require.zip", proc.stdout)

    def test_dynamic_import_boundaries_remain_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private-dynamic-fixture.zip"
            sentinel = "PRIVATE_DYNAMIC_CHUNK_SENTINEL"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("unknown.js",
                    "export const __webpack_modules__={"
                    "PrivateModuleSyntheticZ:(function(e,t,n){"
                    "const a=import('private-module');"
                    "const b=import(t.dynamicName);"
                    "const c=n.e('" + sentinel + "');"
                    "return [a,b,c]})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["dynamic_boundary_count"], 3)
            self.assertTrue(all(x["classification"] == "unresolved_dynamic_boundary"
                                and not x["target_module_verified"]
                                and x["source_ref"] == "R-JS-001"
                                for x in report["dynamic_boundary_candidates"]))
            for private in ("private-module", sentinel, "dynamicName", "PrivateModuleSyntheticZ",
                            "unknown.js", "private-dynamic-fixture.zip"):
                self.assertNotIn(private, result.stdout)

    def test_module_frontier_mode_has_no_intermediate_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private-frontier-fixture.zip"
            sentinel = "PRIVATE_MODULE_FRONTIER_SYNTHETIC_SENTINEL"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("client.js",
                    "export const __webpack_modules__={"
                    "Seed:(function(e,t,n){t.a=n('Linked')}),"
                    "Linked:(function(e,t,n){t.a='" + sentinel + "'})};"
                    "__webpack_require__('Seed')")
            call = ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                    "--input", str(archive), "--module-frontier",
                    "--bootstrap-candidates", "--max-depth", "2"]
            result = subprocess.run(
                call, cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Private pipeline failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["root_source"], "bootstrap_syntax_candidate")
            self.assertEqual(report["reached_module_count"], 2)
            self.assertFalse(report["runtime_module_load_verified"])
            self.assertTrue(all(x["source_ref"] == "R-JS-001"
                                for x in report["nodes"]))
            for forbidden in (sentinel, "Seed", "Linked", "client.js",
                              "private-frontier-fixture.zip"):
                self.assertNotIn(forbidden, result.stdout)
            bad = subprocess.run(
                call + ["--root", "R-JS-001:1"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=20)
            self.assertNotEqual(bad.returncode, 0)
            self.assertNotIn("private-frontier-fixture.zip", bad.stderr)

    def test_colliding_module_keys_yield_candidate_export_shape_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-collision.zip"
            sentinel = "PRIVATE_COLLISION_SENTINEL_NO_PUBLICATION"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Consumer:(function(e,t,n){const recovery=n('Collision');"
                    "recovery.h();recovery.p()}),"
                    "Collision:(function(e,t,n){n.d(t,{h:()=>1,p:()=>2})})};")
                z.writestr("two.js", "export const __webpack_modules__={"
                    "Collision:(function(e,t){t.a='" + sentinel + "'})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Synthetic shape scan failed")
            graph=json.loads(result.stdout)
            self.assertEqual(graph["parsed_bundles"],2)
            self.assertEqual(graph["ambiguous_import_candidates"],1)
            self.assertEqual(graph["unique_resolved_links"],0)
            self.assertEqual(graph["export_shape_candidate_count"],1)
            candidate=graph["export_shape_candidates"][0]
            self.assertEqual((candidate["from_ref"],candidate["to_ref"]),
                             ("R-JS-001","R-JS-001"))
            self.assertEqual(candidate["required_export_count"],2)
            self.assertEqual(candidate["classification"],
                             "candidate_unique_export_interface")
            self.assertFalse(candidate["runtime_import_verified"])
            for private in (sentinel,"Collision","Consumer",str(archive),
                            "one.js","two.js"):
                self.assertNotIn(private,result.stdout)

    def test_catch_shadowing_does_not_create_fake_import_or_export_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-catch-scope.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js", "export const __webpack_modules__={"
                    "Reader:(function(e,t,n){try{throw 1}catch(n){n('Ghost')}"
                    "const imported=n('Collision');"
                    "try{throw 1}catch(imported){imported.h()}}),"
                    "Collision:(function(e,t,n){try{throw 1}catch(t){t.h=1}})};")
                z.writestr("b.js", "export const __webpack_modules__={"
                    "Collision:(function(e,t,n){t.x=1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["import_candidates"], 1)
            self.assertEqual(report["ambiguous_import_candidates"], 1)
            self.assertEqual(report["export_shape_candidate_count"], 0)
            for private in ("Reader", "Ghost", "Collision", "invented-catch-scope.zip"):
                self.assertNotIn(private, proc.stdout)

    def test_imported_object_writes_are_not_export_interface_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-import-object-write.zip"
            identifier = "ImportedWriteCandidateZ984"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Reader:(function(e,t,n){const x=n('" + identifier + "');"
                    "x.key=1;x.key++;delete x.key;"
                    "for(x.key of [1]){};({p:x.key}={p:2})}),"
                    + identifier + ":(function(e,t,n){t.key=()=>1})};")
                z.writestr("two.js", "export const __webpack_modules__={"
                    + identifier + ":(function(e,t,n){t.other=1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["ambiguous_import_candidates"], 1)
            self.assertEqual(data["export_shape_candidate_count"], 0)
            for forbidden in (identifier, "Reader",
                              "synthetic-import-object-write.zip"):
                self.assertNotIn(forbidden, proc.stdout)

    def test_shadowed_export_target_does_not_break_registry_key_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-export-shadow.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("a.js", "export const __webpack_modules__={"
                    "Caller:(function(e,t,n){const x=n('ExptargetFixtureZ9');x.h()}),"
                    "ExptargetFixtureZ9:(function(e,t,n){function fake(t){t.h=1}t.x=1})};")
                z.writestr("b.js", "export const __webpack_modules__={"
                    "ExptargetFixtureZ9:(function(e,t,n){t.y=1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["ambiguous_import_candidates"], 1)
            self.assertEqual(data["export_shape_candidate_count"], 0)
            for item in ("Caller", "ExptargetFixtureZ9", "synthetic-export-shadow.zip"):
                self.assertNotIn(item, proc.stdout)

    def test_var_binding_is_function_scoped_not_block_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fictional-var-shadow.zip"
            key = "PrivateVarCandidateZ978"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Assigned:(function(e,t,n){if(t.flag){var n=()=>1}"
                    "n('" + key + "')}),"
                    "Redeclared:(function(e,t,n){if(t.flag){var n}"
                    "n('" + key + "')}),"
                    "Iterated:(function(e,t,n){for(var n of [()=>1]){}"
                    "n('" + key + "')}),"
                    + key + ":(function(e,t){t.a=1})};")
            run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(run.returncode, 0)
            report = json.loads(run.stdout)
            self.assertEqual(report["import_candidates"], 1)
            self.assertEqual(report["unique_resolved_links"], 1)
            self.assertEqual(report["resolved_links"][0]["from_module"], 2)
            for private in (key, "fictional-var-shadow.zip"):
                self.assertNotIn(private, run.stdout)

    def test_loop_switch_and_catch_outer_rebinding_is_conservative(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-controlflow-rebindings.zip"
            private = "PrivateControlFlowTargetZ961"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Loop:(function(e,t,n){for(let i=0;i<1;i++){n=()=>1}"
                    "n('" + private + "')}),"
                    "Switch:(function(e,t,n){switch(t.flag){case 1:n=()=>1;break}"
                    "n('" + private + "')}),"
                    "Catch:(function(e,t,n){try{throw 1}catch(e){n=()=>1}"
                    "n('" + private + "')}),"
                    "Shadow:(function(e,t,n){for(let n of [()=>1]){n('LocalOnly')}"
                    "try{throw 1}catch(n){n('LocalOnly')}n('" + private + "')}),"
                    + private + ":(function(e,t){t.a=1})};")
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True,
                check=False, timeout=40)
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["import_candidates"], 1)
            self.assertEqual(report["unique_resolved_links"], 1)
            self.assertEqual(report["resolved_links"][0]["from_module"], 4)
            self.assertEqual(report["resolved_links"][0]["to_module"], 5)
            for term in (private, "LocalOnly", "invented-controlflow-rebindings.zip"):
                self.assertNotIn(term, proc.stdout)

    def test_conditional_outer_reassignment_invalidates_static_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-branch-invalidation.zip"
            private_key = "PrivateBranchKeyZ949"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Owner:(function(e,t,n){if(t.flag){n=()=>1}"
                    "n('" + private_key + "');"
                    "const imported=n('Another');"
                    "if(t.flag){imported={x:1}}imported.y();"
                    "if(t.flag){t={}}t.handler=()=>1}),"
                    + private_key + ":(function(e,t,n){t.a=1}),"
                    "Another:(function(e,t,n){t.b=1})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["import_candidates"], 0)
            self.assertEqual(report["direct_function_export_site_count"], 0)
            for term in (private_key, "Another", "Owner",
                         "invented-branch-invalidation.zip"):
                self.assertNotIn(term, result.stdout)

    def test_loop_and_switch_scopes_do_not_leak_module_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-loop-scope.zip"
            sentinel = "PrivateScopeKeyZ999"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bundle.js", "export const __webpack_modules__={"
                    "Consumer:(function(e,t,n){"
                    "const imported=n('Target');"
                    "for(let imported of [{z:()=>1}]){imported.z()}"
                    "imported.x();"
                    "for(let n of [()=>1]){n('" + sentinel + "')}"
                    "switch(1){case 1:const n=()=>1;n('" + sentinel + "');break}"
                    "}),Target:(function(e,t,n){t.x=1})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            graph = json.loads(result.stdout)
            self.assertEqual(graph["import_candidates"], 1)
            self.assertEqual(graph["unique_resolved_links"], 1)
            self.assertEqual(graph["unresolved_import_candidates"], 0)
            for private in (sentinel, "Consumer", "Target", "invented-loop-scope.zip"):
                self.assertNotIn(private, result.stdout)

    def test_nested_parameter_shadowing_cannot_create_module_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-shadowed-loader.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("synthetic.js", "export const __webpack_modules__={"
                    "Root:(function(e,t,n){"
                    "function unrelated(n){const x=n('HiddenModule');return x.h()}"
                    "function bound(n){return n.bind(n,'HiddenModule')}}),"
                    "HiddenModule:(function(e,t,n){t.h=1})};")
            report_run = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(report_run.returncode, 0)
            report = json.loads(report_run.stdout)
            self.assertEqual(report["modules_total"], 2)
            self.assertEqual(report["import_candidates"], 0)
            self.assertEqual(report["bound_import_candidate_count"], 0)
            self.assertEqual(report["export_shape_candidate_count"], 0)
            for private in ("HiddenModule", "Root", "invented-shadowed-loader.zip"):
                self.assertNotIn(private, report_run.stdout)

    def test_bound_imports_are_future_use_candidates_not_direct_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-bound-fixture.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Source:(function(e,t,n){const later=n.bind(n,'HiddenTarget')}),"
                    "HiddenTarget:(function(e,t,n){t.a=1})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["bound_import_candidate_count"], 1)
            self.assertEqual(report["unique_resolved_links"], 0)
            candidate = report["bound_import_candidates"][0]
            self.assertEqual(candidate["classification"], "bound_import_target_candidate")
            self.assertEqual(candidate["candidate_target_module"], 2)
            self.assertFalse(candidate["binding_executed_verified"])
            self.assertFalse(candidate["target_module_loaded_verified"])
            for value in ("Source", "HiddenTarget", "synthetic-bound-fixture.zip"):
                self.assertNotIn(value, result.stdout)

    def test_shadowed_import_alias_does_not_disambiguate_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-scope-collision.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("one.js", "export const __webpack_modules__={"
                    "Consumer:(function(e,t,n){"
                    "function left(){const local=n('Collision')}"
                    "function right(){const local={h:()=>1};return local.h()}}),"
                    "Collision:(function(e,t,n){n.d(t,{h:()=>1})})};")
                z.writestr("two.js", "export const __webpack_modules__={"
                    "Collision:(function(e,t){t.a=1})};")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--module-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["ambiguous_import_candidates"], 1)
            self.assertEqual(report["export_shape_candidate_count"], 0)
            for token in ("Consumer", "Collision", "synthetic-scope-collision.zip"):
                self.assertNotIn(token, result.stdout)

    def test_styles_probe_summarizes_css_without_leaking_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic-style-capture.zip"
            sentinel = "SECRET_SYNTHETIC_STYLE_TOKEN"
            css = ("@media (prefers-reduced-motion:reduce)"
                   "{[data-state=open]:focus-visible{opacity:1}}"
                   "@container (min-width:1px){[data-testid=x] [role=button]{color:red}}"
                   ".app{max-width:var(--thread-content-max-width)}")
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("style/main.css", css)
                z.writestr("script/client.js", "const test='thread-content';"
                           "const privateSentinel='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--styles-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode,0,"Synthetic styles probe failed")
            report=json.loads(result.stdout)
            self.assertEqual(report["stylesheets_scanned"],1)
            self.assertEqual(report["javascript_bundles_scanned"],1)
            self.assertEqual(report["stylesheet_bytes"],len(css.encode("utf-8")))
            self.assertEqual(report["css_lexical_occurrences"]["media_at_rules"],1)
            self.assertEqual(report["css_lexical_occurrences"]["container_at_rules"],1)
            self.assertEqual(report["cross_resource_vocabulary"]["thread_content"]["javascript_bundle_count"],1)
            self.assertTrue(all(x==0 for x in report["exact_css_attribute_selectors"].values()))
            self.assertNotIn(sentinel,result.stdout)
            self.assertNotIn(str(archive),result.stdout)

    def test_feature_trace_is_ordinals_only_and_not_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-features.zip"
            sentinel = "PRIVATE_FEATURE_TEST_SENTINEL"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("invented/features.js",
                    "function find(x){return x.searchRequest({"
                    "searchQuery:x.queryText,searchResults:x.searchHits})}"
                    "function login(x){return x.loginForm&&x.authenticate(x.authSession)}"
                    "function refresh(x){return x.refreshToken+x.accessToken}"
                    "function playback(x){return x.currentTime+x.playbackState}"
                    "function editor(x){return x.editorState+x.applyTransaction}"
                    "const privateData='" + sentinel + "';")
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--feature-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(result.returncode, 0, "Fictional feature probe failed")
            report = json.loads(result.stdout)
            self.assertEqual(report["parsed_bundles"], 1)
            self.assertEqual(report["failed_bundles"], 0)
            for pattern in ("search_query_result_candidate",
                            "search_request_dispatch_candidate",
                            "auth_signin_candidate", "auth_refresh_candidate",
                            "media_progress_candidate",
                            "editor_transaction_candidate"):
                self.assertEqual(report["pattern_counts"][pattern], 1)
            self.assertTrue(all(x["source_ref"] == "R-JS-001"
                                and x["classification"] == "syntactic_candidate"
                                and not x["feature_ownership_verified"]
                                and not x["runtime_behavior_verified"]
                                for x in report["matches"]))
            for private in (sentinel, "invented-features.zip", "features.js", "queryText"):
                self.assertNotIn(private, result.stdout)

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
