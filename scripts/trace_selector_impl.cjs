#!/usr/bin/env node
"use strict";
/* Offline, source-only candidate finder for selected-path message handling.
 * No captured code is evaluated, and only anonymous source/function ordinals
 * and fixed allowlisted classification labels can leave this module.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");
const FUNCTIONS=new Set(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"]);
const LOOPS=new Set(["ForStatement","ForOfStatement","ForInStatement",
                     "WhileStatement","DoWhileStatement"]);
const PATTERNS=[
  "selected_ancestry_message_walk",
  "user_ancestry_identity_walk",
  "automation_reference_extraction",
  "recent_turn_control_candidate"
];
function literalName(node){
  if(node?.type==="Identifier")return node.name;
  if(node?.type==="Literal"&&typeof node.value==="string")return node.value;
  return null;
}
function memberName(node){
  if(node?.type!=="MemberExpression")return null;
  return node.computed?
    node.property?.type==="Literal"?literalName(node.property):null:
    literalName(node.property);
}
function ownScope(fn){
  const reads=new Set(),keys=new Set(),literalTags=new Set(),calls=new Set();
  let loopCount=0;
  const stack=[fn.body];
  while(stack.length){
    const node=stack.pop();
    if(!node||typeof node!=="object")continue;
    if(node!==fn.body&&FUNCTIONS.has(node.type))continue;
    if(node.type==="MemberExpression"){
      const name=memberName(node);
      if(name)reads.add(name);
    }
    if(node.type==="Property"){
      const name=literalName(node.key);
      if(name)keys.add(name);
    }
    if(node.type==="CallExpression"){
      const name=memberName(node.callee);
      if(name)calls.add(name);
    }
    if(node.type==="Literal"&&typeof node.value==="string"){
      if(["answer_now","user"].includes(node.value))literalTags.add(node.value);
    }
    if(LOOPS.has(node.type))loopCount++;
    for(const [name,value] of Object.entries(node)){
      if(["start","end","raw","loc"].includes(name))continue;
      if(Array.isArray(value)){
        for(const child of value)if(child&&typeof child==="object")stack.push(child);
      }else if(value&&typeof value==="object")stack.push(value);
    }
  }
  const categories=[];
  if(loopCount&&reads.has("mapping")&&reads.has("current_node")&&
     reads.has("parent")&&calls.has("reverse")&&calls.has("map"))
    categories.push("selected_ancestry_message_walk");
  if(loopCount&&reads.has("parent")&&reads.has("role")&&
     literalTags.has("user")&&calls.has("reverse")&&reads.has("mapping"))
    categories.push("user_ancestry_identity_walk");
  if((reads.has("automation_id")||reads.has("metadata"))&&
     keys.has("automationId")&&keys.has("messageId")&&keys.has("source"))
    categories.push("automation_reference_extraction");
  if(keys.has("onBeforeAnswerNow")&&literalTags.has("answer_now")&&
     calls.has("filter"))
    categories.push("recent_turn_control_candidate");
  return categories;
}
function inspect(text,ordinal){
  const ast=acorn.parse(text,{ecmaVersion:"latest",sourceType:"module",
    allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
  let functionOrdinal=0;
  const matches=[],stack=[ast];
  while(stack.length){
    const node=stack.pop();
    if(!node||typeof node!=="object")continue;
    if(FUNCTIONS.has(node.type)){
      functionOrdinal++;
      for(const pattern of ownScope(node)){
        matches.push({source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
          function_ordinal:functionOrdinal,pattern,
          evidence_class:"observed_static_syntax",
          domain_ownership_verified:false});
      }
    }
    for(const [name,value] of Object.entries(node)){
      if(["start","end","raw","loc"].includes(name))continue;
      if(Array.isArray(value)){
        for(let i=value.length-1;i>=0;i--)
          if(value[i]&&typeof value[i]==="object")stack.push(value[i]);
      }else if(value&&typeof value==="object")stack.push(value);
    }
  }
  return {function_nodes:functionOrdinal,matches};
}
function scan(directory){
  const names=fs.readdirSync(directory)
    .filter(name=>/^bundle-[0-9]{3,4}\.js$/.test(name)).sort();
  if(names.length>2000)throw Error("Unsupported input count");
  const result={
    format_version:1,source_scope:"local_captured_javascript",
    analysis_kind:"selector_source_candidates",source_executed:false,
    feature_ownership_verified:false,parsed_bundles:0,failed_bundles:0,
    skipped_oversize_bundles:0,function_nodes:0,matches:[],
    vocabulary:PATTERNS,
    limitations:[
      "Lexical function patterns can be satisfied by unrelated libraries; source role and caller review remain necessary.",
      "Dynamic field names, minified aliases and imported helpers require separate data-flow analysis.",
      "Ancestry traversal does not prove message rendering or actual browser execution.",
      "Feature-reference collectors must not be labeled visible chat transcripts.",
      "No captured code, values, original filenames, identifiers, endpoints or source locations are emitted."
    ]
  };
  for(const name of names){
    const entry=path.join(directory,name);
    const stat=fs.lstatSync(entry);
    if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported source entry");
    if(stat.size>8*1024*1024){result.skipped_oversize_bundles++;continue;}
    try{
      const ordinal=Number(name.match(/^bundle-([0-9]+)\.js$/)[1]);
      const parsed=inspect(fs.readFileSync(entry,"utf8"),ordinal);
      result.function_nodes+=parsed.function_nodes;
      result.matches.push(...parsed.matches);
      if(result.matches.length>4000)throw Error("Excessive matches");
      result.parsed_bundles++;
    }catch(err){
      if(err.message==="Excessive matches")throw err;
      result.failed_bundles++;
    }
  }
  result.pattern_counts=Object.fromEntries(PATTERNS.map(pattern=>[
    pattern,result.matches.filter(item=>item.pattern===pattern).length
  ]));
  return result;
}
function selfTest(){
  const js=[
    'function lineage(x){let p=x.current_node,a=[];for(;p;){let z=x.mapping[p];a.push(z.message);p=z.parent}return a.reverse().map(String)}',
    'function userLineage(x){let p=x.current_node,a=[];for(;p;){let z=x.mapping[p];if(z.message.author.role==="user")a.push(z.message.id);p=z.parent}return a.reverse()}',
    'function refs(x){return x.metadata.automation_id?[{automationId:x.id,messageId:x.id,source:"metadata"}]:[]}',
    'function Control(x){let{onBeforeAnswerNow,messages}=x;let a=messages.filter(Boolean);return a.length?"answer_now":null}',
    'const privateOnly="SYNTHETIC_PRIVATE_SENTINEL_NOT_FOR_PUBLICATION"'
  ].join(";");
  const output=inspect(js,1);
  assert.deepEqual(output.matches.map(item=>item.pattern).sort(),PATTERNS.slice().sort());
  assert.equal(output.function_nodes,4);
  assert(!JSON.stringify(output).includes("SYNTHETIC_PRIVATE_SENTINEL"));
  assert.equal(inspect("function other(){return 2}",2).matches.length,0);
}
if(require.main===module){
  if(process.argv.length===3&&process.argv[2]==="--self-test"){
    selfTest();process.stdout.write("Synthetic selector candidate probe passed\n");
  }else if(process.argv.length===3){
    try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
    catch(_){process.stderr.write("Static selector probe failed (input details suppressed)\n");process.exitCode=2;}
  }else{process.stderr.write("Usage: node scripts/trace_selector_impl.cjs <private-js-directory>\n");process.exitCode=2;}
}
module.exports={inspect,scan,selfTest};
