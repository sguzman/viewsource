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
 def test_every_source_and_finding_reference_exists(self):
  resources=json.loads((ROOT/"specimens/chatgpt-com/v0002/resource_inventory.json").read_text("utf8"))
  record=json.loads((ROOT/"specimens/chatgpt-com/v0002/record.json").read_text("utf8"))
  resource_ids={x["id"] for x in resources["resources"]}
  evidence_ids={x["evidence"]["evidence_ref"] for x in record["findings"]}
  self.assertEqual(len(evidence_ids),len(record["findings"]))
  study=self.study
  for stage in study["stages"]:
   self.assertTrue(set(stage["source_refs"]) <= resource_ids)
   self.assertTrue(set(stage["evidence_refs"]) <= evidence_ids)
   self.assertTrue(all(ref.startswith("E2-") for ref in stage["evidence_refs"]))
  for path in study["alternative_paths"]:
   self.assertTrue(path["evidence_refs"])
   self.assertTrue(set(path["evidence_refs"]) <= evidence_ids)
  self.assertEqual(len({x["id"] for x in study["stages"]}),len(study["stages"]))
 def test_no_private_source(self):
  text=PATH.read_text("utf8").lower()
  for forbidden in ("https://","http://",".js","raw_source","page-snapshot",
                    "authorization:","bearer ","source-dom","session_token",
                    "original_filename","request_body="):
   self.assertNotIn(forbidden,text)
if __name__=="__main__":
 unittest.main()
