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
 def test_stage_anchor_precision_and_cross_study_grounding(self):
  index=self.study["stage_anchor_provenance"]
  self.assertFalse(index["runtime_execution_verified"])
  self.assertEqual(len(index["stages"]),10)
  self.assertEqual([x["stage_id"] for x in index["stages"]],
                   [x["id"] for x in self.study["stages"]])
  self.assertEqual(sum(x["granularity"]=="resource_review_only"
                       for x in index["stages"]),4)
  get=lambda stem:json.loads((ROOT/("specimens/chatgpt-com/v0002/"+stem+".json")).read_text("utf8"))
  impl=get("chat_static_impl_trace")
  transport=get("chat_transport_trace")
  viewport=get("chat_viewport_virtualization_trace")
  module=get("chat_module_dependency_trace")
  anchor_by_id={a["stage_id"]:a for a in index["stages"]}
  self.assertTrue(any(x["function_ordinal"]==anchor_by_id["generation_dispatch"]["function_ordinal"]
                      and x["source_ref"]=="R-JS-018" for x in impl["reviewed_client_operations"]))
  self.assertEqual(anchor_by_id["completion_transport"]["function_ordinal"],
                   transport["generation_transport_bridge"]["caller_function_ordinal"])
  self.assertTrue(any(x["source_ref"]=="R-JS-066" and x["module_ordinal"]==9
                      for x in viewport["module_anchors"]))
  self.assertTrue(any(x["from_ref"]=="R-JS-072" and x["from_module"]==13
                      and x["to_ref"]=="R-JS-069" and x["to_module"]==12
                      for x in module["curated_verified_syntax_edges"]))
  for original,anchor in zip(self.study["stages"],index["stages"]):
   self.assertIn(anchor["source_ref"],original["source_refs"])
   self.assertTrue(anchor["scope"] and anchor["next"] and anchor["source_study"])
   if anchor["granularity"]=="resource_review_only":
    self.assertNotIn("module_ordinal",anchor)
    self.assertNotIn("function_ordinal",anchor)
 def test_no_private_source(self):
  text=PATH.read_text("utf8").lower()
  for forbidden in ("https://","http://",".js","raw_source","page-snapshot",
                    "authorization:","bearer ","source-dom","session_token",
                    "original_filename","request_body="):
   self.assertNotIn(forbidden,text)
if __name__=="__main__":
 unittest.main()
