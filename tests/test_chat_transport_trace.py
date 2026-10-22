"""Scope, privacy and graph integrity of the static transport evidence."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"specimens/chatgpt-com/v0002/chat_transport_trace.json"

class TransportTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text("utf-8"))

    def test_source_scope_and_relationships(self):
        report=self.report
        self.assertEqual((report["specimen_id"],report["version"]),("chatgpt-com",2))
        self.assertEqual(report["source_ref"],"R-JS-018")
        self.assertFalse(report["source_executed"])
        self.assertFalse(report["live_transport_verified"])
        self.assertFalse(report["server_protocol_verified"])
        names={row["method"] for row in report["method_observations"]}
        self.assertEqual(len(names),report["reviewed_method_count"])
        self.assertEqual(names,{
            "startCompletionStream","resumeCompletionStream","cancelStream",
            "getStreamOptions","createCompletionStreamHandlers"
        })
        allowed=names|{"generation_dispatcher","topic_based_stream","streaming_request",
                       "local_and_request_cancellation","resume_recovery",
                       "decoded_update_processor","message_update_callback"}
        edges=report["reviewed_static_edges"]
        self.assertEqual(len(edges),11)
        for row in edges:
            self.assertIn(row["from"],allowed)
            self.assertIn(row["to"],allowed)
            self.assertIn(row["kind"],{
                "direct_method_call","conditional_client_path",
                "direct_client_sequence","client_recovery_configuration",
                "scoped_service_method_call","static_callback_wiring"
            })
        self.assertTrue(report["still_unresolved"])

    def test_dispatcher_to_transport_bridge_is_source_reviewed(self):
        bridge=self.report["generation_transport_bridge"]
        self.assertEqual(bridge["source_ref"],"R-JS-018")
        self.assertEqual(bridge["caller_function_ordinal"],9032)
        self.assertEqual(bridge["callee_method"],"startCompletionStream")
        self.assertEqual(bridge["static_call_kind"],"scoped_service_method_call")
        self.assertTrue(bridge["reviewed_call"])
        self.assertEqual(bridge["evidence_class"],"observed_static")
        self.assertIn("onDecodedEvent",bridge["observed_callback_wiring"])
        self.assertIn("conversation_mapping",bridge["recovery_state_inputs"])
        self.assertIn("selected_message_node",bridge["recovery_state_inputs"])
        self.assertFalse(self.report["live_transport_verified"])

    def test_transport_decoded_event_to_message_update_wiring(self):
        pipeline=self.report["decoded_update_pipeline"]
        self.assertEqual(pipeline["source_ref"],"R-JS-018")
        self.assertEqual(pipeline["dispatcher_function_ordinal"],9032)
        self.assertEqual(pipeline["evidence_class"],"observed_static")
        self.assertEqual([x["stage"] for x in pipeline["sequence"]],[
            "transport_decoded_event","event_processor",
            "message_update","message_marker","terminal_or_metadata"
        ])
        self.assertTrue(pipeline["verification_boundary"])

    def test_no_capture_data_escapes_to_public_report(self):
        output=REPORT.read_text("utf-8").lower()
        for prohibited in (
            "http://","https://","backend-api","/f/conversation",
            "source-dom","page-snapshot-","session_token",
            "authorization:","set-cookie","bearer ",
            "raw_source","private_user","original_filename"
        ):
            self.assertNotIn(prohibited,output)
        for row in self.report["method_observations"]:
            self.assertEqual(row["source_ref"],"R-JS-018")
            self.assertTrue(row["verification_boundary"])

if __name__=="__main__":
    unittest.main()
