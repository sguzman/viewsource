"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {frontier,parseRoot,candidateBootstrapRoots}=require("../scripts/trace_module_frontier.cjs");
const graph=()=>({
 format_version:1,scope:"private_saved_javascript_modules",
 source_executed:false,module_runtime_loaded_verified:false,
 module_census:[{source_ref:"R-JS-001",count:3},{source_ref:"R-JS-002",count:2}],
 unresolved_import_candidates:2,ambiguous_import_candidates:1,
 resolved_links:[
  {from_ref:"R-JS-001",from_module:1,to_ref:"R-JS-001",to_module:2,
   classification:"static_import_candidate",runtime_import_verified:false},
  {from_ref:"R-JS-001",from_module:2,to_ref:"R-JS-002",to_module:1,
   classification:"static_import_candidate",runtime_import_verified:false},
  {from_ref:"R-JS-002",from_module:1,to_ref:"R-JS-001",to_module:1,
   classification:"static_import_candidate",runtime_import_verified:false}
 ],
 export_shape_candidates:[{
  from_ref:"R-JS-002",from_module:1,to_ref:"R-JS-002",to_module:2,
  classification:"candidate_unique_export_interface",runtime_import_verified:false
 }]
});
test("BFS resolves cycles without promoting ambiguous candidates",()=>{
 const report=frontier(graph(),["R-JS-001:1"]);
 assert.deepEqual(report.depth_counts.map(x=>x.module_count),[1,1,1]);
 assert.equal(report.reached_module_count,3);
 assert.equal(report.export_shape_ambiguities.length,1);
 assert.ok(report.export_shape_ambiguities.every(x=>!x.traversed));
 assert.ok(!report.nodes.some(x=>x.source_ref==="R-JS-002"&&x.module_ordinal===2));
 assert.equal(report.total_unresolved_import_candidates,2);
 assert.equal(report.runtime_module_load_verified,false);
});
test("depth and node limits retain an explicit frontier",()=>{
 const one=frontier(graph(),["R-JS-001:1"],{depthLimit:1});
 assert.equal(one.reached_module_count,2);
 assert.deepEqual(one.boundary_modules,[{source_ref:"R-JS-001",module_ordinal:2}]);
 const two=frontier(graph(),["R-JS-001:1"],{nodeLimit:2});
 assert.equal(two.truncated_by_node_limit,true);
 assert.ok(two.boundary_modules.length>0);
});
test("malformed roots, out-of-scope data, and fake runtime imports are rejected",()=>{
 assert.throws(()=>parseRoot("R-JS-001:0"));
 assert.throws(()=>parseRoot("PRIVATE"));
 assert.throws(()=>frontier(graph(),["R-JS-001:4"]));
 const g=graph();g.resolved_links[0].runtime_import_verified=true;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 const h=graph();h.module_census.push({source_ref:"R-JS-001",count:3});
 assert.throws(()=>frontier(h,["R-JS-001:1"]));
});
test("multiple roots deduplicate, order-independent under fixed limits",()=>{
 const a=frontier(graph(),["R-JS-002:1","R-JS-001:1","R-JS-001:1"]);
 assert.equal(a.roots.length,2);
 assert.equal(a.reached_module_count,3);
 assert.equal(a.nodes.filter(x=>x.depth===0).length,2);
});

test("candidate bootstrap roots use only uniquely matched unexecuted syntax",()=>{
 const data=graph();
 data.bootstrap_runtime_verified=false;
 data.bootstrap_candidates=[
  {classification:"unique_registry_key_candidate",target_ref:"R-JS-001",
   target_module:1,bootstrap_execution_verified:false},
  {classification:"ambiguous_registry_key",bootstrap_execution_verified:false},
  {classification:"missing_saved_module",bootstrap_execution_verified:false}
 ];
 const roots=candidateBootstrapRoots(data);
 assert.deepEqual(roots,["R-JS-001:1"]);
 const result=frontier(data,roots,{rootSource:"bootstrap_syntax_candidate"});
 assert.equal(result.root_source,"bootstrap_syntax_candidate");
 assert.equal(result.runtime_module_load_verified,false);
 data.bootstrap_candidates[0].bootstrap_execution_verified=true;
 assert.throws(()=>candidateBootstrapRoots(data));
});

test("dynamic loading boundaries are visible but never expand reachability",()=>{
 const data=graph();
 data.dynamic_boundary_candidates=[{
  source_ref:"R-JS-002",module_ordinal:1,
  pattern:"dynamic_import_computed_candidate",
  classification:"unresolved_dynamic_boundary",target_module_verified:false
 }];
 const report=frontier(data,["R-JS-001:1"]);
 assert.equal(report.reachable_dynamic_boundary_count,1);
 assert.equal(report.reachable_dynamic_boundaries[0].module.source_ref,"R-JS-002");
 assert.equal(report.reachable_dynamic_boundaries[0].traversed,false);
 assert.equal(report.reached_module_count,3);
 const shallow=frontier(data,["R-JS-001:1"],{depthLimit:1});
 assert.equal(shallow.reachable_dynamic_boundary_count,0);
 data.dynamic_boundary_candidates[0].target_module_verified=true;
 assert.throws(()=>frontier(data,["R-JS-001:1"]));
});

test("bound loader callback candidates are visible but not traversed",()=>{
 const g=graph();
 g.bound_import_candidates=[{
   source_ref:"R-JS-002",module_ordinal:1,
   classification:"bound_import_target_candidate",
   candidate_target_ref:"R-JS-002",candidate_target_module:2,
   binding_executed_verified:false,target_module_loaded_verified:false
 }];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reachable_bound_import_count,1);
 assert.equal(out.reachable_bound_import_candidates[0].candidate_target.module_ordinal,2);
 assert.equal(out.reachable_bound_import_candidates[0].traversed,false);
 assert.equal(out.reached_module_count,3);
 g.bound_import_candidates[0].binding_executed_verified=true;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});
