"""Bound source-observed transport recovery without claiming executed retries."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"specimens/chatgpt-com/v0002/chat_transport_failure_trace.json"
class TransportFailureTraceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads(PATH.read_text("utf8"))
 def test_recovery_stages_and_defaults(self):
  d=self.d
  self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
  self.assertFalse(d["live_failure_observed"])
  self.assertFalse(d["server_retry_semantics_verified"])
  self.assertEqual(len(d["observations"]),10)
  self.assertEqual(len(d["reviewed_relationships"]),11)
  self.assertEqual(d["captured_default_fallbacks"]["max_resume_retry_count"],12)
  self.assertEqual(d["captured_default_fallbacks"]["min_resume_retry_delay_ms"],300)
  self.assertEqual(d["captured_default_fallbacks"]["max_resume_retry_delay_ms"],5000)
  self.assertEqual(d["captured_default_fallbacks"]["resume_retry_backoff_factor"],1.5)
  self.assertIn("may be overridden",d["fallback_scope"])
  self.assertTrue(all(x["boundary"] for x in d["observations"]))
  self.assertTrue(d["open_questions"])
  fallback=d["preparation_fallback"]
  self.assertEqual(fallback["source_ref"],"R-JS-018")
  self.assertEqual(fallback["method"],"prepareCompletionStream")
  self.assertFalse(fallback["client_execution_observed"])
  self.assertEqual((fallback["minimum_delay_ms"],fallback["maximum_delay_exclusive_ms"]),(250,500))
  self.assertEqual(len(fallback["required_conditions"]),5)
  self.assertIn("additional_retry_disabled",fallback["fallback_changes"])
  self.assertIn("completion_stream_resume_recovery",fallback["distinguished_from"])
  self.assertIn("same-capture",fallback["limit"])
  predicate=d["preparation_error_eligibility"]
  self.assertEqual(predicate["source_ref"],"R-JS-018")
  self.assertEqual(predicate["resolved_import"]["definition_matches_in_saved_assets"],1)
  self.assertEqual(predicate["typed_status_allowlist"],[408,409,425,502,504])
  self.assertTrue(predicate["explicit_structured_retry_veto"])
  self.assertEqual(len(predicate["decision_order"]),6)
  self.assertFalse(d["live_failure_observed"])
  self.assertIn("separately",predicate["scope"])
 def test_nonpublication(self):
  s=PATH.read_text("utf8").lower()
  for forbidden in ("http://","https://",".js","session_token","bearer ",
                    "raw_source","request_url","original_filename","page-snapshot",
                    "authorization:","secret_message","source-dom"):
   self.assertNotIn(forbidden,s)
if __name__=="__main__":
 unittest.main()
