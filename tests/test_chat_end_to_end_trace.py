"""Ensure static client lifecycle remains evidence-graded and private."""
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"specimens/chatgpt-com/v0002/chat_end_to_end_trace.json"
class StaticLifecycleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.study=json.loads(PATH.read_text("utf8"))
 def test_source_lifecycle_and_alternatives(self):
  d=self.study
  self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
  self.assertFalse(d["live_execution_verified"])
  self.assertFalse(d["server_contract_verified"])
  self.assertFalse(d["message_durability_verified"])
  self.assertEqual(len(d["stages"]),10)
  self.assertEqual(len(d["connections"]),9)
  self.assertEqual(len(d["alternative_paths"]),5)
  ids={x["id"] for x in d["stages"]}
  self.assertEqual(len(ids),10)
  self.assertTrue(all(x["source_refs"] and x["evidence_refs"] for x in d["stages"]))
  self.assertTrue(all(x["from"] in ids and x["to"] in ids and
                      x["evidence_kind"] and x["limits"] for x in d["connections"]))
  self.assertTrue(d["open_static_questions"] and d["limits"])
 def test_no_private_source(self):
  text=PATH.read_text("utf8").lower()
  for forbidden in ("https://","http://",".js","raw_source","page-snapshot",
                    "authorization:","bearer ","source-dom","session_token",
                    "original_filename","request_body="):
   self.assertNotIn(forbidden,text)
if __name__=="__main__":
 unittest.main()
