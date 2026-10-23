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
  const census=new Map();
  for(const item of graph.module_census){
    if(!REF.test(item.source_ref)||!Number.isSafeInteger(item.count)||
       item.count<0||item.count>NODE_LIMIT||census.has(item.source_ref))
      throw Error("Invalid module census");
    census.set(item.source_ref,item.count);
  }
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
  return {census,adjacency,ambiguous};
}
function frontier(graph, roots, options={}) {
  const depthLimit=options.depthLimit??6, nodeLimit=options.nodeLimit??2000;
  if(!Number.isSafeInteger(depthLimit)||depthLimit<0||depthLimit>30||
     !Number.isSafeInteger(nodeLimit)||nodeLimit<1||nodeLimit>LIMIT)
    throw Error("Invalid traversal limit");
  const {census,adjacency,ambiguous}=indexGraph(graph);
  if(!Array.isArray(roots)||!roots.length||roots.length>20)throw Error("Invalid roots");
  const seeds=[...new Set(roots.map(parseRoot))];
  for(const id of seeds) {
    const [ref,n]=id.split(":");
    if(!census.has(ref)||Number(n)>census.get(ref))throw Error("Root outside saved module census");
  }
  const queue=seeds.map(id=>({id,depth:0}));
  const visited=new Map(queue.map(({id})=>[id,0]));
  const counts=new Map([[0,queue.length]]);
  const boundary=new Set();
  const ambiguousCandidates=new Map();
  let traversed=0,limited=false;
  for(let i=0;i<queue.length;i++){
    const {id,depth}=queue[i];
    const candidates=ambiguous.get(id)||new Set();
    for(const candidate of candidates){
      if(!ambiguousCandidates.has(id))ambiguousCandidates.set(id,new Set());
      ambiguousCandidates.get(id).add(candidate);
    }
    const links=adjacency.get(id)||new Set();
    if(depth===depthLimit){
      if(links.size)boundary.add(id);
      continue;
    }
    for(const next of links) {
      traversed++;
      if(visited.has(next))continue;
      if(visited.size===nodeLimit) {
        limited=true;boundary.add(id);continue;
      }
      visited.set(next,depth+1);
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
  const nodes=[...visited].sort((a,b)=>a[1]-b[1]||a[0].localeCompare(b[0]))
    .map(([id,depth])=>({...asNode(id),depth,
      outgoing_unique_static_imports:(adjacency.get(id)||new Set()).size}));
  return {
    format_version:1,scope:"private_static_module_frontier",
    source_executed:false,runtime_module_load_verified:false,
    roots:seeds.map(asNode),depth_limit:depthLimit,node_limit:nodeLimit,
    reached_module_count:nodes.length,traversed_static_edges:traversed,
    depth_counts:layerCounts,nodes,
    boundary_modules:[...boundary].sort().map(asNode),
    export_shape_ambiguities:ambiguities,
    truncated_by_node_limit:limited,
    total_unresolved_import_candidates:graph.unresolved_import_candidates,
    total_ambiguous_import_candidates:graph.ambiguous_import_candidates,
    limitations:[
      "Reachability follows only statically resolved literal imports; it is not runtime module execution.",
      "Export-shape matches are shown separately and are NEVER traversed as verified edges.",
      "Unresolved import counts cover the entire capture, not only these roots.",
      "Conditional imports, lazy chunks, dynamic keys, and unarchived modules can hide branches.",
      "Source and module ordinals are specific to one capture; no source keys, paths or code are emitted."
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
  assert.equal(frontier(graph,["R-JS-001:1"],{nodeLimit:2}).truncated_by_node_limit,true);
  assert.throws(()=>frontier(graph,["R-JS-001:100"]));
  assert.throws(()=>frontier(graph,["R-JS-001:1"],{depthLimit:-1}));
  assert(!JSON.stringify(result).includes("private-secret"));
}
function main(argv) {
  if(argv.length===1&&argv[0]==="--self-test"){selfTest();console.log("Synthetic module frontier passed");return;}
  let input=null,roots=[],depthLimit=6,nodeLimit=2000;
  for(let i=0;i<argv.length;i++){
    const arg=argv[i];
    if(arg==="--input")input=argv[++i];
    else if(arg==="--root")roots.push(argv[++i]);
    else if(arg==="--max-depth")depthLimit=Number(argv[++i]);
    else if(arg==="--max-nodes")nodeLimit=Number(argv[++i]);
    else throw Error("Invalid argument");
  }
  if(typeof input!=="string"||!input||!roots.length)throw Error("Missing input/roots");
  if(fs.statSync(input).size>MAX_BYTES)throw Error("Graph too large");
  const output=frontier(JSON.parse(fs.readFileSync(input,"utf8")),roots,{depthLimit,nodeLimit});
  process.stdout.write(JSON.stringify(output,null,2)+"\n");
}
if(require.main===module){
  try{main(process.argv.slice(2));}
  catch(_){process.stderr.write("Module frontier rejected (input or roots invalid; details suppressed)\n");process.exitCode=2;}
}
module.exports={frontier,indexGraph,parseRoot,selfTest};
