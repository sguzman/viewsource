#!/usr/bin/env node
"use strict";
/* Offline, source-ordinal-only JS syntax investigation; never execute site assets.
 * Candidate syntax is not proof of domain ownership, network outcomes or runtime.
 */
const fs=require("node:fs"), path=require("node:path"), assert=require("node:assert/strict");
const acorn=require("acorn");
const fnTypes=new Set(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"]);
const loopTypes=new Set(["ForStatement","WhileStatement","DoWhileStatement","ForOfStatement","ForInStatement"]);
const vocabulary=["selected_ancestry_walk","branch_transport_call","mapping_ancestry_reconciliation"];

function member(n){
  if(!n||n.type!=="MemberExpression")return null;
  if(!n.computed&&n.property?.type==="Identifier")return n.property.name;
  if(n.computed&&n.property?.type==="Literal"&&typeof n.property.value==="string")return n.property.value;
  return null;
}
function property(n){
  if(!n||n.computed)return null;
  if(n.key?.type==="Identifier")return n.key.name;
  if(n.key?.type==="Literal"&&typeof n.key.value==="string")return n.key.value;
  return null;
}
function inspect(fn){
  const reads=new Set(),writes=new Set(),fields=new Set();
  let loops=0,branch=0;
  const stack=[fn.body];
  while(stack.length){
    const n=stack.pop();
    if(!n||typeof n!=="object")continue;
    if(n!==fn.body&&fnTypes.has(n.type))continue;
    if(n.type==="MemberExpression"){const k=member(n);if(k)reads.add(k);}
    if(n.type==="Property"){const k=property(n);if(k)fields.add(k);}
    if(n.type==="AssignmentExpression"&&n.left?.type==="MemberExpression"){
      const k=member(n.left);if(k)writes.add(k);
    }
    if(loopTypes.has(n.type))loops++;
    if(n.type==="CallExpression"&&member(n.callee)==="branch"&&
       n.arguments[0]?.type==="ObjectExpression"){
      const args=new Set(n.arguments[0].properties.map(property).filter(Boolean));
      if(args.has("conversationId")&&args.has("messageId"))branch++;
    }
    for(const [k,v] of Object.entries(n)){
      if(["start","end","loc","raw"].includes(k))continue;
      if(Array.isArray(v)){
        for(const x of v)if(x&&typeof x==="object")stack.push(x);
      }else if(v&&typeof v==="object")stack.push(v);
    }
  }
  const result=[];
  if(loops&&reads.has("current_node")&&reads.has("mapping")&&reads.has("parent"))
    result.push("selected_ancestry_walk");
  if(branch)result.push("branch_transport_call");
  if(reads.has("mapping")&&reads.has("children")&&reads.has("parent")&&
     (reads.has("current_node")||reads.has("currentNode"))&&
     (writes.has("parent")||fields.has("parent")))
    result.push("mapping_ancestry_reconciliation");
  return result;
}
function analyzeSource(text,ordinal){
  const ast=acorn.parse(text,{ecmaVersion:"latest",sourceType:"module",
    allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
  const candidates=[];
  let index=0;
  function walk(n,enclosing){
    if(!n||typeof n!=="object")return;
    if(fnTypes.has(n.type)){
      const k=index++;
      for(const pattern of inspect(n)){
        candidates.push({source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
          function_ordinal:k+1,parent_ordinal:enclosing===null?null:enclosing+1,
          pattern,evidence_status:"observed_static_syntax",
          domain_ownership_verified:false});
      }
      enclosing=k;
    }
    for(const [key,value] of Object.entries(n)){
      if(["start","end","loc","raw"].includes(key))continue;
      if(Array.isArray(value)){
        for(const child of value)walk(child,enclosing);
      }else if(value&&typeof value==="object")walk(value,enclosing);
    }
  }
  walk(ast,null);
  return {candidate_functions:candidates,function_nodes:index};
}
function collect(dir){
  const names=fs.readdirSync(dir).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
  if(names.length>2000)throw Error("Unsupported source count");
  const result={format_version:1,source_scope:"saved_static_javascript",
    assessment:"syntactic_client_implementation_candidates",
    live_behavior_verified:false,source_code_published:false,
    pattern_vocabulary:vocabulary,parsed_bundles:0,failed_bundles:0,
    skipped_oversize:0,function_nodes:0,matches:[],
    limitations:[
      "Syntax matches can originate in unrelated bundled dependencies.",
      "Lexical containment is not a function call edge; minified names are not correlated.",
      "Pattern detection cannot prove network outcomes or server-side storage.",
      "No captured source, strings, filenames, locations or identifiers are emitted."
    ]};
  for(const name of names){
    const loc=path.join(dir,name),stat=fs.lstatSync(loc);
    if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported input");
    if(stat.size>8*1024*1024){result.skipped_oversize++;continue;}
    try{
      const ordinal=Number(name.match(/^bundle-([0-9]+)\.js$/)[1]);
      const record=analyzeSource(fs.readFileSync(loc,"utf8"),ordinal);
      result.parsed_bundles++;
      result.function_nodes+=record.function_nodes;
      result.matches.push(...record.candidate_functions);
      if(result.matches.length>4000)throw Error("Excessive matches");
    }catch(e){
      if(e.message==="Excessive matches")throw e;
      result.failed_bundles++;
    }
  }
  result.matches.sort((a,b)=>a.source_ref.localeCompare(b.source_ref)||
    a.function_ordinal-b.function_ordinal||a.pattern.localeCompare(b.pattern));
  result.pattern_counts=Object.fromEntries(vocabulary.map(x=>[x,
    result.matches.filter(y=>y.pattern===x).length]));
  return result;
}
function selfTest(){
  const text=[
    "function path(c){let id=c.current_node;for(;id;){const node=c.mapping[id];id=node.parent;}return id}",
    "async function fork(client,c,m){return client.branch({conversationId:c,messageId:m})}",
    "function merge(old,remote){let rows=old.mapping;for(let id in rows){rows[id]={parent:remote.mapping[id].parent,children:remote.mapping[id].children}}return {currentNode:old.currentNode,mapping:rows}}",
    "const secret='synthetic-secret-must-not-be-printed'"
  ].join(";");
  const result=analyzeSource(text,1);
  assert.deepEqual(result.candidate_functions.map(x=>x.pattern).sort(),vocabulary.slice().sort());
  assert.equal(result.function_nodes,3);
  assert(!JSON.stringify(result).includes("synthetic-secret-must-not-be-printed"));
  assert.equal(analyzeSource("function f(x){return x.branch({conversationId:1})}",2).candidate_functions.length,0);
}
if(require.main===module){
  if(process.argv.length===3&&process.argv[2]==="--self-test"){
    selfTest();console.log("Synthetic structural trace passed");
  }else if(process.argv.length===3){
    try{process.stdout.write(JSON.stringify(collect(process.argv[2]),null,2)+"\n");}
    catch(e){process.stderr.write("Static trace rejected (details suppressed)\n");process.exitCode=2;}
  }else{process.stderr.write("Usage: node scripts/trace_chat_impl.cjs <private-ordinal-js-directory>\n");process.exitCode=2;}
}
module.exports={analyzeSource,collect,selfTest};
