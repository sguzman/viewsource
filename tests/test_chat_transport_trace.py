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
        allowed=names|{"topic_based_stream","streaming_request",
                       "local_and_request_cancellation","resume_recovery"}
        edges=report["reviewed_static_edges"]
        self.assertEqual(len(edges),8)
        for row in edges:
            self.assertIn(row["from"],allowed)
            self.assertIn(row["to"],allowed)
            self.assertIn(row["kind"],{
                "direct_method_call","conditional_client_path",
                "direct_client_sequence","client_recovery_configuration"
            })
        self.assertTrue(report["still_unresolved"])

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
