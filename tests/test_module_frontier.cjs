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
test("frontier edge counts exclude cycles, already reached modules and limited nodes",()=>{
 const regular=frontier(graph(),["R-JS-001:1"]);
 assert.equal(regular.traversed_static_edges,2);
 assert.equal(regular.examined_static_edges,3);
 const limited=frontier(graph(),["R-JS-001:1"],{nodeLimit:2});
 assert.equal(limited.traversed_static_edges,1);
 assert.equal(limited.examined_static_edges,2);
 assert.equal(limited.truncated_by_node_limit,true);
 assert.throws(()=>frontier(graph(),["R-JS-001:1","R-JS-001:2"],{nodeLimit:1}));
});
test("predecessor paths are source-local and depth boundaries exclude closed cycles",()=>{
 const report=frontier(graph(),["R-JS-001:1"]);
 const leaf=report.nodes.find(x=>x.source_ref==="R-JS-002"&&x.module_ordinal===1);
 assert.deepEqual(leaf.reached_via,{source_ref:"R-JS-001",module_ordinal:2});
 assert.equal(leaf.incoming_edge_classification,"static_import_candidate");
 assert.deepEqual(report.nodes.find(x=>x.depth===0).reached_via,null);
 assert.deepEqual(report.boundary_details,[]);
 const closed=frontier(graph(),["R-JS-002:1"],{depthLimit:0});
 assert.deepEqual(closed.boundary_details[0].reasons,["depth_limit"]);
 const g=graph();
 g.resolved_links=[{
  from_ref:"R-JS-001",from_module:1,to_ref:"R-JS-001",to_module:1,
  classification:"static_import_candidate",runtime_import_verified:false
 }];
 assert.deepEqual(frontier(g,["R-JS-001:1"],{depthLimit:0}).boundary_details,[]);
 const limited=frontier(graph(),["R-JS-001:1"],{nodeLimit:2});
 assert.deepEqual(limited.boundary_details[0].reasons,["node_limit"]);
});
test("depth and node limits retain an explicit frontier",()=>{
 const one=frontier(graph(),["R-JS-001:1"],{depthLimit:1});
 assert.equal(one.reached_module_count,2);
 assert.deepEqual(one.boundary_modules,[{source_ref:"R-JS-001",module_ordinal:2}]);
 const two=frontier(graph(),["R-JS-001:1"],{nodeLimit:2});
 assert.equal(two.truncated_by_node_limit,true);
 assert.ok(two.boundary_modules.length>0);
});
test("schema count fields are numeric and cannot echo private input",()=>{
 const g=graph();
 g.unresolved_import_candidates="PRIVATE_UNTRUSTED_COUNT";
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 const h=graph();
 h.ambiguous_import_candidates=NaN;
 assert.throws(()=>frontier(h,["R-JS-001:1"]));
 const inconsistent=graph();
 inconsistent.modules_total=999;
 assert.throws(()=>frontier(inconsistent,["R-JS-001:1"]));
 const partition=graph();
 partition.import_candidates=100;
 assert.throws(()=>frontier(partition,["R-JS-001:1"]));
 const dynamic=graph();
 dynamic.dynamic_boundary_count=1;
 dynamic.dynamic_boundary_candidates=[];
 assert.throws(()=>frontier(dynamic,["R-JS-001:1"]));
 const valid=graph();
 valid.modules_total=5;
 valid.unique_resolved_links=3;
 valid.import_candidates=6;
 assert.equal(frontier(valid,["R-JS-001:1"]).traversed_static_edges,2);
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
test("frontier paths and node limits are deterministic under permuted evidence",()=>{
 const a=graph();
 const b=graph();
 b.resolved_links.reverse();
 const roots=["R-JS-001:2","R-JS-001:1"];
 const reversed=[...roots].reverse();
 const first=frontier(a,roots,{nodeLimit:3});
 const second=frontier(b,reversed,{nodeLimit:3});
 assert.deepEqual(first,second);
 const full=frontier(b,roots);
 const fullReversed=frontier(a,reversed);
 assert.deepEqual(full,fullReversed);
 assert.deepEqual(full.roots,[
  {source_ref:"R-JS-001",module_ordinal:1},
  {source_ref:"R-JS-001",module_ordinal:2}
 ]);
});
test("multiple roots deduplicate, order-independent under fixed limits",()=>{
 const a=frontier(graph(),["R-JS-002:1","R-JS-001:1","R-JS-001:1"]);
 assert.equal(a.roots.length,2);
 assert.equal(a.reached_module_count,3);
 assert.equal(a.nodes.filter(x=>x.depth===0).length,2);
});

test("bootstrap root provenance distinguishes source contexts without claiming execution",()=>{
 const g=graph();
 g.bootstrap_runtime_verified=false;
 g.bootstrap_candidates=[
  {classification:"unique_registry_key_candidate",
   bootstrap_kind:"chunk_runtime_literal_call_candidate",
   target_ref:"R-JS-001",target_module:1,bootstrap_execution_verified:false},
  {classification:"unique_registry_key_candidate",
   bootstrap_kind:"top_level_literal_call_candidate",
   target_ref:"R-JS-001",target_module:1,bootstrap_execution_verified:false},
  {classification:"ambiguous_registry_key",bootstrap_execution_verified:false}
 ];
 const roots=candidateBootstrapRoots(g);
 assert.deepEqual(roots,["R-JS-001:1"]);
 const out=frontier(g,roots,{rootSource:"bootstrap_syntax_candidate"});
 assert.equal(out.bootstrap_root_provenance.length,1);
 assert.deepEqual(out.bootstrap_root_provenance[0].candidate_kinds,
  ["chunk_runtime_literal_call_candidate","top_level_literal_call_candidate"]);
 assert.equal(out.bootstrap_root_provenance[0].matching_static_calls,2);
 assert.equal(out.bootstrap_root_provenance[0].execution_verified,false);
 assert.throws(()=>frontier(g,["R-JS-001:2"],{rootSource:"bootstrap_syntax_candidate"}));
 g.bootstrap_candidates[0].bootstrap_kind="private_script_name";
 assert.throws(()=>candidateBootstrapRoots(g));
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

test("computed module-key candidates remain an untraversed dynamic boundary",()=>{
 const g=graph();
 g.dynamic_boundary_candidates=[{
   source_ref:"R-JS-001",module_ordinal:2,
   pattern:"computed_module_require_candidate",
   classification:"unresolved_dynamic_boundary",target_module_verified:false
 }];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reachable_dynamic_boundary_count,1);
 assert.equal(out.reachable_dynamic_boundaries[0].traversed,false);
 assert.equal(out.reached_module_count,3);
});

test("foreign-registry key collisions are untraversed review leads",()=>{
 const g=graph();
 g.foreign_registry_key_collision_count=1;
 g.foreign_registry_key_collisions=[{
  source_ref:"R-JS-001",module_ordinal:2,
  foreign_registry_definition_count:1,
  classification:"foreign_registry_key_collision",import_resolved:false
 }];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reachable_foreign_registry_collision_count,1);
 assert.equal(out.reachable_foreign_registry_collisions[0].traversed,false);
 assert.equal(out.reached_module_count,3);
 assert.equal(frontier(g,["R-JS-001:1"],{depthLimit:0})
  .reachable_foreign_registry_collision_count,0);
 g.foreign_registry_key_collisions[0].import_resolved=true;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("capture parser-coverage counters must reconcile before emitting frontier",()=>{
 const g=graph();
 g.modules_total=5;
 g.parsed_bundles=1;
 g.failed_bundles=1;
 g.archive_candidate_script_count=3;
 g.archive_oversize_script_count=1;
 g.archive_ast_input_script_count=2;
 g.archive_all_scripts_parsed=false;
 g.failed_parser_source_refs=["R-JS-002"];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.archive_all_scripts_parsed,false);
 assert.deepEqual(out.failed_parser_source_refs,["R-JS-002"]);
 assert.equal(out.archive_oversize_script_count,1);
 g.archive_all_scripts_parsed=true;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 g.archive_all_scripts_parsed=false;
 g.failed_parser_source_refs=["PRIVATE_SCRIPT_FILENAME"];
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("reachable unresolved import sites only describe visited nodes",()=>{
 const g=graph();
 g.unresolved_import_site_count=3;
 g.unresolved_import_sites=[
  {source_ref:"R-JS-001",module_ordinal:1,classification:"missing_saved_target",
   definition_candidates:0,import_resolved:false},
  {source_ref:"R-JS-002",module_ordinal:1,classification:"missing_saved_target",
   definition_candidates:0,import_resolved:false},
  {source_ref:"R-JS-002",module_ordinal:2,classification:"ambiguous_same_registry_target",
   definition_candidates:2,import_resolved:false}
 ];
 const whole=frontier(g,["R-JS-001:1"]);
 assert.equal(whole.reachable_unresolved_import_count,2);
 assert.equal(whole.total_unresolved_import_candidates,2);
 assert.equal(whole.total_ambiguous_import_candidates,1);
 const shallow=frontier(g,["R-JS-001:1"],{depthLimit:0});
 assert.equal(shallow.reachable_unresolved_import_count,1);
 g.unresolved_import_sites[0].classification="private-module-id";
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("direct function-valued exports belong to reached modules only",()=>{
 const graphData=graph();
 graphData.direct_function_export_site_count=2;
 graphData.direct_function_export_sites=[
  {source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:1,
   classification:"direct_function_export_assignment_candidate",
   runtime_invocation_verified:false},
  {source_ref:"R-JS-002",module_ordinal:2,export_function_ordinal:1,
   classification:"direct_function_export_assignment_candidate",
   runtime_invocation_verified:false}
 ];
 const shallow=frontier(graphData,["R-JS-001:1"],{depthLimit:1});
 assert.equal(shallow.reachable_direct_function_export_site_count,1);
 assert.equal(shallow.reachable_direct_function_export_sites[0].source.module_ordinal,2);
 const full=frontier(graphData,["R-JS-001:1"]);
 assert.equal(full.reachable_direct_function_export_site_count,1);
 assert.equal(full.reachable_direct_function_export_sites[0].runtime_invocation_verified,false);
 graphData.direct_function_export_sites[0].classification="private-key-name";
 assert.throws(()=>frontier(graphData,["R-JS-001:1"]));
});

test("whole-module function assignments remain a distinct source candidate",()=>{
 const g=graph();
 g.direct_function_export_site_count=1;
 g.direct_function_export_sites=[{
  source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:1,
  classification:"module_object_function_assignment_candidate",
  runtime_invocation_verified:false
 }];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reachable_direct_function_export_site_count,1);
 assert.equal(out.reachable_direct_function_export_sites[0].classification,
  "module_object_function_assignment_candidate");
 assert.equal(out.reachable_direct_function_export_sites[0].runtime_invocation_verified,false);
});

test("literal loader calls distinguish repeated syntax from distinct module keys",()=>{
 const g=graph();
 g.import_candidates=6;
 g.literal_module_loader_call_expression_count=8;
 g.literal_module_loader_call_site_counts=[
  {source_ref:"R-JS-001",module_ordinal:1,literal_call_expressions:5,
   distinct_literal_targets:3,classification:"static_literal_loader_calls",
   runtime_invocation_verified:false},
  {source_ref:"R-JS-002",module_ordinal:2,literal_call_expressions:3,
   distinct_literal_targets:3,classification:"static_literal_loader_calls",
   runtime_invocation_verified:false}
 ];
 const full=frontier(g,["R-JS-001:1"]);
 assert.equal(full.reachable_literal_module_loader_call_expression_count,5);
 assert.equal(full.reachable_literal_module_loader_call_sites.length,1);
 assert.equal(full.reachable_literal_module_loader_call_sites[0].runtime_invocation_verified,false);
 g.literal_module_loader_call_site_counts[0].literal_call_expressions="PrivateCallText";
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("nonfactory source entry census rejects impossible values",()=>{
 const g=graph();
 g.modules_total=5;
 g.registry_nonfactory_entry_count=1;
 assert.equal(frontier(g,["R-JS-001:1"]).registry_nonfactory_entry_count,1);
 g.registry_nonfactory_entry_count=6;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 g.registry_nonfactory_entry_count="PrivateNonFactory";
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("computed registry key coverage count is bounded and anonymous",()=>{
 const graphData=graph();
 graphData.modules_total=5;
 graphData.registry_unresolved_computed_key_count=2;
 assert.equal(frontier(graphData,["R-JS-001:1"]).registry_unresolved_computed_key_count,2);
 graphData.registry_unresolved_computed_key_count=9;
 assert.throws(()=>frontier(graphData,["R-JS-001:1"]));
 graphData.registry_unresolved_computed_key_count="computedPrivateKey";
 assert.throws(()=>frontier(graphData,["R-JS-001:1"]));
});

test("nested loader callsite count is a validated subset of root-local syntax",()=>{
 const g=graph();
 g.import_candidates=6;
 g.literal_module_loader_call_expression_count=8;
 g.nested_function_literal_module_loader_call_expression_count=3;
 g.literal_module_loader_call_site_counts=[
  {source_ref:"R-JS-001",module_ordinal:1,literal_call_expressions:5,
   nested_function_literal_call_expressions:3,distinct_literal_targets:3,
   classification:"static_literal_loader_calls",runtime_invocation_verified:false},
  {source_ref:"R-JS-002",module_ordinal:2,literal_call_expressions:3,
   nested_function_literal_call_expressions:0,distinct_literal_targets:3,
   classification:"static_literal_loader_calls",runtime_invocation_verified:false}
 ];
 const report=frontier(g,["R-JS-001:1"]);
 assert.equal(report.reachable_nested_function_literal_loader_call_expression_count,3);
 g.nested_function_literal_module_loader_call_expression_count=5;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("bootstrap definition counts must agree with their evidence classification",()=>{
 const g=graph();
 g.bootstrap_runtime_verified=false;
 g.bootstrap_candidates=[
  {classification:"unique_registry_key_candidate",
   target_ref:"R-JS-001",target_module:1,
   registry_definition_candidates:1,bootstrap_execution_verified:false}
 ];
 assert.deepEqual(candidateBootstrapRoots(g),["R-JS-001:1"]);
 g.bootstrap_candidates[0].registry_definition_candidates=2;
 assert.throws(()=>candidateBootstrapRoots(g));
});

test("function-export ordinals cannot contain duplicates or gaps",()=>{
 const g=graph();
 g.direct_function_export_site_count=2;
 g.direct_function_export_sites=[
  {source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:1,
   classification:"direct_function_export_assignment_candidate",
   runtime_invocation_verified:false},
  {source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:2,
   classification:"module_object_function_assignment_candidate",
   runtime_invocation_verified:false}
 ];
 assert.equal(frontier(g,["R-JS-001:1"]).reachable_direct_function_export_site_count,2);
 g.direct_function_export_sites[1].export_function_ordinal=1;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("bound-loader definition counts are consistent with candidate type",()=>{
 const g=graph();
 g.bound_import_candidate_count=1;
 g.bound_import_candidates=[{
  source_ref:"R-JS-001",module_ordinal:2,
  classification:"ambiguous_bound_import",definition_candidates:2,
  binding_executed_verified:false,target_module_loaded_verified:false
 }];
 assert.equal(frontier(g,["R-JS-001:1"]).reachable_bound_import_count,1);
 g.bound_import_candidates[0].definition_candidates=1;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("bootstrap root provenance includes only capture-local source ordinals",()=>{
 const g=graph();
 g.bootstrap_runtime_verified=false;
 g.bootstrap_candidates=[
  {classification:"unique_registry_key_candidate",
   bootstrap_kind:"top_level_literal_call_candidate",
   callsite_ref:"R-JS-001",target_ref:"R-JS-001",target_module:1,
   registry_definition_candidates:1,bootstrap_execution_verified:false},
  {classification:"unique_registry_key_candidate",
   bootstrap_kind:"chunk_runtime_literal_call_candidate",
   callsite_ref:"R-JS-002",target_ref:"R-JS-001",target_module:1,
   registry_definition_candidates:1,bootstrap_execution_verified:false}
 ];
 const roots=candidateBootstrapRoots(g);
 const out=frontier(g,roots,{rootSource:"bootstrap_syntax_candidate"});
 assert.deepEqual(out.bootstrap_root_provenance[0].static_callsite_resources,
  ["R-JS-001","R-JS-002"]);
 assert.equal(out.bootstrap_root_provenance[0].execution_verified,false);
 g.bootstrap_candidates[0].callsite_ref="PrivateOrigin.js";
 assert.throws(()=>candidateBootstrapRoots(g));
});

test("nested-only dependency edges remain static and root-local",()=>{
 const g=graph();
 g.resolved_links[0].factory_body_syntax_present=true;
 g.resolved_links[0].nested_function_syntax_present=true;
 g.resolved_links[1].factory_body_syntax_present=false;
 g.resolved_links[1].nested_function_syntax_present=true;
 g.resolved_links[2].factory_body_syntax_present=true;
 g.resolved_links[2].nested_function_syntax_present=false;
 g.nested_only_resolved_link_count=1;
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reached_source_nested_only_link_count,1);
 assert.equal(out.reached_source_nested_only_links[0].classification,
   "nested_function_only_static_import_candidate");
 assert.equal(out.reached_source_nested_only_links[0].runtime_import_verified,false);
 assert.equal(frontier(g,["R-JS-001:1"],{depthLimit:0})
   .reached_source_nested_only_link_count,0);
 g.resolved_links[1].factory_body_syntax_present=true;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("parsed resource without recognized modules is an explicit coverage gap",()=>{
 const g=graph();
 g.parsed_bundles=3;
 g.parsed_without_indexed_module_count=1;
 g.parsed_without_indexed_module_refs=["R-JS-003"];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.parsed_without_indexed_module_count,1);
 assert.deepEqual(out.parsed_without_indexed_module_refs,["R-JS-003"]);
 g.parsed_without_indexed_module_refs.push("R-JS-001");
 g.parsed_without_indexed_module_count=2;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 g.parsed_without_indexed_module_refs=["PrivateFileName"];
 g.parsed_without_indexed_module_count=1;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("nested callable export sites are tagged and checked separately",()=>{
 const g=graph();
 g.direct_function_export_site_count=2;
 g.nested_function_export_site_count=1;
 g.direct_function_export_sites=[
  {source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:1,
   classification:"direct_function_export_assignment_candidate",
   nested_function_syntax_present:false,runtime_invocation_verified:false},
  {source_ref:"R-JS-001",module_ordinal:2,export_function_ordinal:2,
   classification:"direct_function_export_assignment_candidate",
   nested_function_syntax_present:true,runtime_invocation_verified:false}
 ];
 const out=frontier(g,["R-JS-001:1"]);
 assert.equal(out.reachable_nested_function_export_site_count,1);
 assert.equal(out.reachable_direct_function_export_sites.length,2);
 g.nested_function_export_site_count=0;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});

test("failed parser resource ordinals reconcile and never overlap parsed sources",()=>{
 const g=graph();
 g.failed_bundles=1;
 g.failed_parser_source_refs=["R-JS-004"];
 assert.deepEqual(frontier(g,["R-JS-001:1"]).failed_parser_source_refs,["R-JS-004"]);
 g.failed_parser_source_refs=["R-JS-001"];
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 g.failed_parser_source_refs=["R-JS-004","R-JS-004"];
 g.failed_bundles=2;
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
 g.failed_parser_source_refs=["R-JS-004"];
 assert.throws(()=>frontier(g,["R-JS-001:1"]));
});
