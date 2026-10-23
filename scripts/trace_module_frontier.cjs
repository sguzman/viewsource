#!/usr/bin/env node
"use strict";
/* Review a sanitized static import graph. Never read or execute captured JavaScript.
 * Input must be the ordinal-only --module-trace report, kept in the private workspace.
 */
const fs=require("node:fs");
const assert=require("node:assert/strict");
const REF=/^R-JS-[0-9]{3,4}$/;
const ROOT=/^(R-JS-[0-9]{3,4}):([1-9][0-9]*)$/;
const LIMIT=8000;
const MAX_BYTES=64*1024*1024;
const NODE_LIMIT=50000;

function ordinal(ref,module) {
  if(typeof ref!=="string"||!REF.test(ref)||!Number.isSafeInteger(module)||
      module<1||module>NODE_LIMIT)throw Error("Invalid ordinal");
  return ref+":"+module;
}
function parseRoot(value) {
  const match=ROOT.exec(value||"");
  if(!match)throw Error("Invalid root ordinal");
  return ordinal(match[1],Number(match[2]));
}
function indexGraph(graph) {
  if(graph?.format_version!==1||graph.scope!=="private_saved_javascript_modules"||
     graph.source_executed!==false||graph.module_runtime_loaded_verified!==false||
     !Array.isArray(graph.module_census)||!Array.isArray(graph.resolved_links)||
     !Array.isArray(graph.export_shape_candidates))throw Error("Invalid graph scope");
  const safeCount=(value,label)=>{
    if(!Number.isSafeInteger(value)||value<0||value>250000)
      throw Error("Invalid "+label);
    return value;
  };
  safeCount(graph.unresolved_import_candidates,"unresolved count");
  safeCount(graph.ambiguous_import_candidates,"ambiguous count");
  for(const [field,array] of [
    ["modules_total",null],
    ["unique_resolved_links","resolved_links"],
    ["export_shape_candidate_count","export_shape_candidates"],
    ["dynamic_boundary_count","dynamic_boundary_candidates"],
    ["bound_import_candidate_count","bound_import_candidates"],
    ["bootstrap_call_candidates","bootstrap_candidates"],
    ["foreign_registry_key_collision_count","foreign_registry_key_collisions"],
    ["archive_candidate_script_count",null],
    ["archive_oversize_script_count",null],
    ["archive_ast_input_script_count",null]
  ]){
    if(graph[field]===undefined)continue;
    const value=safeCount(graph[field],field);
    if(array&&(!Array.isArray(graph[array])||value!==graph[array].length))
      throw Error("Graph count inconsistent");
  }
  if(graph.failed_parser_source_refs!==undefined){
    if(!Array.isArray(graph.failed_parser_source_refs)||
       graph.failed_parser_source_refs.length>NODE_LIMIT||
       graph.failed_parser_source_refs.some(ref=>typeof ref!=="string"||!REF.test(ref)))
      throw Error("Invalid failed parser resource ordinals");
  }
  if(graph.archive_candidate_script_count!==undefined){
    const total=graph.archive_candidate_script_count;
    const excluded=graph.archive_oversize_script_count;
    const inputs=graph.archive_ast_input_script_count;
    if(typeof graph.archive_all_scripts_parsed!=="boolean"||
       !Number.isSafeInteger(excluded)||excluded<0||
       !Number.isSafeInteger(inputs)||inputs<0||
       total!==inputs+excluded||
       graph.archive_all_scripts_parsed!==(excluded===0&&graph.failed_bundles===0))
      throw Error("Invalid capture coverage census");
    if(graph.parsed_bundles+graph.failed_bundles!==inputs)
      throw Error("Incomplete parser coverage census");
  }
  if(graph.import_candidates!==undefined){
    const total=safeCount(graph.import_candidates,"import_candidates");
    if(total!==graph.resolved_links.length+
       graph.unresolved_import_candidates+graph.ambiguous_import_candidates)
      throw Error("Import partition inconsistent");
  }
  const census=new Map();
  for(const item of graph.module_census){
    if(!REF.test(item.source_ref)||!Number.isSafeInteger(item.count)||
       item.count<0||item.count>NODE_LIMIT||census.has(item.source_ref))
      throw Error("Invalid module census");
    census.set(item.source_ref,item.count);
  }
  const censusTotal=[...census.values()].reduce((sum,count)=>sum+count,0);
  if(censusTotal>NODE_LIMIT||(graph.modules_total!==undefined&&
      graph.modules_total!==censusTotal))throw Error("Module census inconsistent");
  const known=(ref,n)=>ordinal(ref,n)&&census.has(ref)&&n<=census.get(ref);
  const adjacency=new Map();
  let scanned=0;
  for(const edge of graph.resolved_links) {
    scanned++;
    if(scanned>250000)throw Error("Graph too large");
    if(edge.classification!=="static_import_candidate"||edge.runtime_import_verified!==false||
       !known(edge.from_ref,edge.from_module)||!known(edge.to_ref,edge.to_module))
      throw Error("Invalid static edge");
    const a=ordinal(edge.from_ref,edge.from_module),b=ordinal(edge.to_ref,edge.to_module);
    if(!adjacency.has(a))adjacency.set(a,new Set());
    adjacency.get(a).add(b);
  }
  const ambiguous=new Map();
  for(const edge of graph.export_shape_candidates){
    if(edge.classification!=="candidate_unique_export_interface"||
       edge.runtime_import_verified!==false||
       !known(edge.from_ref,edge.from_module)||!known(edge.to_ref,edge.to_module))
      throw Error("Invalid candidate edge");
    const a=ordinal(edge.from_ref,edge.from_module),b=ordinal(edge.to_ref,edge.to_module);
    if(!ambiguous.has(a))ambiguous.set(a,new Set());
    ambiguous.get(a).add(b);
  }
  const dynamic=new Map();
  const vocabulary=new Set(["dynamic_import_literal_candidate",
    "dynamic_import_computed_candidate","bundler_chunk_loader_candidate",
    "computed_module_require_candidate"]);
  if(graph.dynamic_boundary_candidates!==undefined){
    if(!Array.isArray(graph.dynamic_boundary_candidates))
      throw Error("Invalid dynamic boundaries");
    for(const edge of graph.dynamic_boundary_candidates){
      if(edge.classification!=="unresolved_dynamic_boundary"||
         edge.target_module_verified!==false||!vocabulary.has(edge.pattern)||
         !known(edge.source_ref,edge.module_ordinal))
        throw Error("Invalid dynamic boundary candidate");
      const id=ordinal(edge.source_ref,edge.module_ordinal);
      if(!dynamic.has(id))dynamic.set(id,new Set());
      dynamic.get(id).add(edge.pattern);
    }
  }
  const bound=new Map();
  if(graph.bound_import_candidates!==undefined){
    if(!Array.isArray(graph.bound_import_candidates))
      throw Error("Invalid bound loader candidate list");
    for(const item of graph.bound_import_candidates){
      if(!["bound_import_target_candidate","ambiguous_bound_import",
            "missing_bound_import_target"].includes(item.classification)||
         item.binding_executed_verified!==false||
         item.target_module_loaded_verified!==false||
         !known(item.source_ref,item.module_ordinal))
        throw Error("Invalid bound loader candidate");
      if(item.classification==="bound_import_target_candidate"&&
         !known(item.candidate_target_ref,item.candidate_target_module))
        throw Error("Invalid bound target");
      const from=ordinal(item.source_ref,item.module_ordinal);
      if(!bound.has(from))bound.set(from,[]);
      bound.get(from).push({
        classification:item.classification,
        target:item.classification==="bound_import_target_candidate"?
          ordinal(item.candidate_target_ref,item.candidate_target_module):null
      });
    }
  }
  const foreign=new Map();
  if(graph.foreign_registry_key_collisions!==undefined){
    if(!Array.isArray(graph.foreign_registry_key_collisions))
      throw Error("Invalid foreign registry collision report");
    for(const item of graph.foreign_registry_key_collisions){
      if(item.classification!=="foreign_registry_key_collision"||
         item.import_resolved!==false||
         !known(item.source_ref,item.module_ordinal)||
         !Number.isSafeInteger(item.foreign_registry_definition_count)||
         item.foreign_registry_definition_count<1||
         item.foreign_registry_definition_count>NODE_LIMIT)
        throw Error("Invalid foreign registry collision");
      const id=ordinal(item.source_ref,item.module_ordinal);
      if(!foreign.has(id))foreign.set(id,0);
      foreign.set(id,foreign.get(id)+item.foreign_registry_definition_count);
    }
  }
  return {census,adjacency,ambiguous,dynamic,bound,foreign};
}
function candidateBootstrapRoots(graph) {
 if(graph?.bootstrap_runtime_verified!==false||!Array.isArray(graph.bootstrap_candidates))
  throw Error("Missing candidate bootstrap classification");
 const roots=[];
 for(const item of graph.bootstrap_candidates) {
  if(item?.bootstrap_execution_verified!==false)throw Error("Invalid candidate execution");
  if(item.classification==="unique_registry_key_candidate") {
   roots.push(ordinal(item.target_ref,item.target_module));
  }else if(!["ambiguous_registry_key","missing_saved_module"].includes(item.classification)) {
   throw Error("Invalid candidate class");
  }
 }
 if(!roots.length)throw Error("No uniquely resolved bootstrap candidates");
 return [...new Set(roots)];
}
function frontier(graph, roots, options={}) {
  const depthLimit=options.depthLimit??6, nodeLimit=options.nodeLimit??2000;
  const provenance=options.rootSource??"explicit_ordinal_selection";
  if(!["explicit_ordinal_selection","bootstrap_syntax_candidate"].includes(provenance))
    throw Error("Invalid root provenance");
  if(!Number.isSafeInteger(depthLimit)||depthLimit<0||depthLimit>30||
     !Number.isSafeInteger(nodeLimit)||nodeLimit<1||nodeLimit>LIMIT)
    throw Error("Invalid traversal limit");
  const {census,adjacency,ambiguous,dynamic,bound,foreign}=indexGraph(graph);
  if(!Array.isArray(roots)||!roots.length||roots.length>20)throw Error("Invalid roots");
  const seeds=[...new Set(roots.map(parseRoot))];
  if(seeds.length>nodeLimit)throw Error("Initial roots exceed node limit");
  for(const id of seeds) {
    const [ref,n]=id.split(":");
    if(!census.has(ref)||Number(n)>census.get(ref))throw Error("Root outside saved module census");
  }
  const queue=seeds.map(id=>({id,depth:0}));
  const visited=new Map(queue.map(({id})=>[id,0]));
  const predecessors=new Map(seeds.map(id=>[id,null]));
  const counts=new Map([[0,queue.length]]);
  const boundary=new Map();
  function markBoundary(id,reason){
    if(!boundary.has(id))boundary.set(id,new Set());
    boundary.get(id).add(reason);
  }
  const ambiguousCandidates=new Map();
  let traversed=0,examined=0,limited=false;
  for(let i=0;i<queue.length;i++){
    const {id,depth}=queue[i];
    const candidates=ambiguous.get(id)||new Set();
    for(const candidate of candidates){
      if(!ambiguousCandidates.has(id))ambiguousCandidates.set(id,new Set());
      ambiguousCandidates.get(id).add(candidate);
    }
    const links=adjacency.get(id)||new Set();
    if(depth===depthLimit){
      if([...links].some(next=>!visited.has(next)))
        markBoundary(id,"depth_limit");
      continue;
    }
    for(const next of links) {
      examined++;
      if(visited.has(next))continue;
      if(visited.size===nodeLimit) {
        limited=true;markBoundary(id,"node_limit");continue;
      }
      traversed++;
      visited.set(next,depth+1);
      predecessors.set(next,id);
      counts.set(depth+1,(counts.get(depth+1)||0)+1);
      queue.push({id:next,depth:depth+1});
    }
  }
  function asNode(id){
    const [source_ref,n]=id.split(":");
    return {source_ref,module_ordinal:Number(n)};
  }
  const layerCounts=[...counts.entries()].sort((a,b)=>a[0]-b[0])
    .map(([depth,count])=>({depth,module_count:count}));
  const ambiguities=[...ambiguousCandidates].sort(([a],[b])=>a.localeCompare(b))
    .flatMap(([id,targets])=>[...targets].sort().map(target=>({
      from:asNode(id),candidate_target:asNode(target),
      classification:"unresolved_candidate_only",traversed:false
    })));
  const unresolvedDynamic=[...visited.keys()].sort().flatMap(id=>
    [...(dynamic.get(id)||new Set())].sort().map(pattern=>({
      module:asNode(id),pattern,
      classification:"unresolved_dynamic_boundary",traversed:false
    })));
  const unresolvedBound=[...visited.keys()].sort().flatMap(id=>
    (bound.get(id)||[]).map(item=>({
      source:asNode(id),
      classification:item.classification,
      candidate_target:item.target?asNode(item.target):null,
      traversed:false
    })));
  const foreignCollisions=[...visited.keys()].sort()
    .filter(id=>foreign.has(id)).map(id=>({
      source:asNode(id),foreign_registry_definition_count:foreign.get(id),
      classification:"foreign_registry_key_collision",traversed:false
    }));
  const nodes=[...visited].sort((a,b)=>a[1]-b[1]||a[0].localeCompare(b[0]))
    .map(([id,depth])=>({...asNode(id),depth,
      reached_via:predecessors.get(id)?asNode(predecessors.get(id)):null,
      incoming_edge_classification:predecessors.get(id)?"static_import_candidate":null,
      outgoing_unique_static_imports:(adjacency.get(id)||new Set()).size}));
  return {
    format_version:1,scope:"private_static_module_frontier",
    source_executed:false,runtime_module_load_verified:false,
    roots:seeds.map(asNode),root_source:provenance,
    archive_candidate_script_count:graph.archive_candidate_script_count??null,
    archive_oversize_script_count:graph.archive_oversize_script_count??null,
    archive_all_scripts_parsed:graph.archive_all_scripts_parsed??null,
    failed_parser_source_refs:graph.failed_parser_source_refs||[],
    depth_limit:depthLimit,node_limit:nodeLimit,
    reached_module_count:nodes.length,traversed_static_edges:traversed,
    examined_static_edges:examined,
    depth_counts:layerCounts,nodes,
    boundary_modules:[...boundary.keys()].sort().map(asNode),
    boundary_details:[...boundary].sort(([a],[b])=>a.localeCompare(b))
      .map(([id,reasons])=>({...asNode(id),reasons:[...reasons].sort()})),
    export_shape_ambiguities:ambiguities,
    reachable_dynamic_boundary_count:unresolvedDynamic.length,
    reachable_dynamic_boundaries:unresolvedDynamic,
    reachable_bound_import_count:unresolvedBound.length,
    reachable_bound_import_candidates:unresolvedBound,
    reachable_foreign_registry_collision_count:foreignCollisions.length,
    reachable_foreign_registry_collisions:foreignCollisions,
    truncated_by_node_limit:limited,
    total_unresolved_import_candidates:graph.unresolved_import_candidates,
    total_ambiguous_import_candidates:graph.ambiguous_import_candidates,
    limitations:[
      "Reachability follows only statically resolved literal imports; it is not runtime module execution.",
      "Export-shape matches are shown separately and are NEVER traversed as verified edges.",
      "Dynamic loading syntax in reached modules is a separate unresolved boundary and is NEVER traversed.",
      "Bound loader callbacks remain future-use candidates and NEVER expand the resolved graph.",
      "Registry keys seen exclusively in other named runtime namespaces remain unresolved and are NEVER imported.",
      "Unresolved import counts cover the entire capture, not only these roots.",
      "Conditional imports, lazy chunks, dynamic keys, and unarchived modules can hide branches.",
      "Source and module ordinals are specific to one capture; no source keys, paths or code are emitted.",
      "A successful parse is not evidence of feature ownership or complete recognition of bundled source patterns."
    ]
  };
}
function selfTest() {
  const graph={format_version:1,scope:"private_saved_javascript_modules",
    source_executed:false,module_runtime_loaded_verified:false,
    module_census:[{source_ref:"R-JS-001",count:3},{source_ref:"R-JS-002",count:2}],
    unresolved_import_candidates:1,ambiguous_import_candidates:1,
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
    }]};
  const result=frontier(graph,["R-JS-001:1"]);
  assert.equal(result.reached_module_count,3);
  assert.deepEqual(result.depth_counts.map(x=>x.module_count),[1,1,1]);
  assert.equal(result.export_shape_ambiguities.length,1);
  assert(!result.nodes.some(x=>x.source_ref==="R-JS-002"&&x.module_ordinal===2));
  assert.equal(frontier(graph,["R-JS-001:1"],{depthLimit:1}).boundary_modules.length,1);
  assert.equal(result.nodes[0].reached_via,null);
  assert.deepEqual(result.nodes[2].reached_via,
    {source_ref:"R-JS-001",module_ordinal:2});
  assert.equal(frontier(graph,["R-JS-001:1"],{nodeLimit:2}).truncated_by_node_limit,true);
  assert.throws(()=>frontier(graph,["R-JS-001:100"]));
  assert.throws(()=>frontier(graph,["R-JS-001:1"],{depthLimit:-1}));
  assert(!JSON.stringify(result).includes("private-secret"));
  const seeded={...graph,bootstrap_runtime_verified:false,
    bootstrap_candidates:[
      {classification:"unique_registry_key_candidate",target_ref:"R-JS-001",
       target_module:1,bootstrap_execution_verified:false},
      {classification:"ambiguous_registry_key",bootstrap_execution_verified:false}
    ]};
  assert.deepEqual(candidateBootstrapRoots(seeded),["R-JS-001:1"]);
  assert.equal(frontier(seeded,candidateBootstrapRoots(seeded),
    {rootSource:"bootstrap_syntax_candidate"}).root_source,"bootstrap_syntax_candidate");
}
function main(argv) {
  if(argv.length===1&&argv[0]==="--self-test"){selfTest();console.log("Synthetic module frontier passed");return;}
  let input=null,roots=[],depthLimit=6,nodeLimit=2000,seedBootstrap=false,fromStdin=false;
  for(let i=0;i<argv.length;i++){
    const arg=argv[i];
    if(arg==="--input")input=argv[++i];
    else if(arg==="--stdin")fromStdin=true;
    else if(arg==="--root")roots.push(argv[++i]);
    else if(arg==="--bootstrap-candidates")seedBootstrap=true;
    else if(arg==="--max-depth")depthLimit=Number(argv[++i]);
    else if(arg==="--max-nodes")nodeLimit=Number(argv[++i]);
    else throw Error("Invalid argument");
  }
  if((!!input===fromStdin)||(!seedBootstrap&&!roots.length)||
     (seedBootstrap&&roots.length))throw Error("Missing or conflicting input/roots");
  if(input&&fs.statSync(input).size>MAX_BYTES)throw Error("Graph too large");
  const json=fs.readFileSync(fromStdin?0:input,"utf8");
  if(Buffer.byteLength(json,"utf8")>MAX_BYTES)throw Error("Graph too large");
  const graph=JSON.parse(json);
  const seeds=seedBootstrap?candidateBootstrapRoots(graph):roots;
  const output=frontier(graph,seeds,{depthLimit,nodeLimit,
    rootSource:seedBootstrap?"bootstrap_syntax_candidate":"explicit_ordinal_selection"});
  process.stdout.write(JSON.stringify(output,null,2)+"\n");
}
if(require.main===module){
  try{main(process.argv.slice(2));}
  catch(_){process.stderr.write("Module frontier rejected (input or roots invalid; details suppressed)\n");process.exitCode=2;}
}
module.exports={frontier,indexGraph,parseRoot,candidateBootstrapRoots,selfTest};
