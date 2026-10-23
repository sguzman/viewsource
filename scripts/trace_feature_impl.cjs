#!/usr/bin/env node
"use strict";
/* Static feature leads only. Captured scripts are parsed, never executed.
 * Report fixed category labels and capture-local numeric ordinals, never source. */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");
const fnTypes=new Set(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"]);
const vocab=[
 "search_query_result_candidate","search_request_dispatch_candidate",
 "auth_signin_candidate","auth_refresh_candidate","auth_signout_candidate",
 "media_progress_candidate","media_controls_candidate",
 "editor_transaction_candidate","editor_undo_selection_candidate"
];
const categories={
 search_query_result_candidate:[["searchQuery","searchTerm","queryText"],["searchResults","resultItems","searchHits"]],
 search_request_dispatch_candidate:[["searchQuery","searchTerm","queryText"],["searchRequest","searchResponse"]],
 auth_signin_candidate:[["loginForm","signIn"],["authenticate","authentication","authSession"]],
 auth_refresh_candidate:[["refreshToken"],["accessToken","authSession"]],
 auth_signout_candidate:[["signOut","logOut"],["sessionToken","authSession"]],
 media_progress_candidate:[["currentTime"],["playbackState","mediaSession"]],
 media_controls_candidate:[["playbackRate"],["pausePlayback","playbackState"]],
 editor_transaction_candidate:[["editorState"],["applyTransaction","insertText"]],
 editor_undo_selection_candidate:[["undoStack"],["selectionChange","editorState"]]
};
const allow=new Set(Object.values(categories).flat(2));
function field(node){
 if(!node)return null;
 if(node.type==="MemberExpression"){
  const p=node.property;
  if(!node.computed&&p?.type==="Identifier")return p.name;
  if(node.computed&&p?.type==="Literal"&&typeof p.value==="string")return p.value;
 }else if(node.type==="Property"||node.type==="MethodDefinition"){
  const p=node.key;
  if(!node.computed&&p?.type==="Identifier")return p.name;
  if(p?.type==="Literal"&&typeof p.value==="string")return p.value;
 }
 return null;
}
function check(fn){
 const names=new Set(),stack=[fn.body];
 while(stack.length){
  const n=stack.pop();
  if(!n||typeof n!=="object")continue;
  if(n!==fn.body&&fnTypes.has(n.type))continue;
  if(["MemberExpression","Property","MethodDefinition"].includes(n.type)){
   const k=field(n);
   if(allow.has(k))names.add(k);
  }
  for(const [k,v] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v))for(const x of v)if(x&&typeof x==="object")stack.push(x);
   else if(v&&typeof v==="object")stack.push(v);
  }
 }
 return vocab.filter(pattern=>categories[pattern].every(group=>group.some(k=>names.has(k))));
}
function analyze(source,ordinal){
 const ast=acorn.parse(source,{ecmaVersion:"latest",sourceType:"module",
  allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
 let total=0;
 const matches=[];
 function walk(n,parent){
  if(!n||typeof n!=="object")return;
  if(fnTypes.has(n.type)){
   const current=++total;
   for(const pattern of check(n))matches.push({
    source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
    function_ordinal:current,parent_ordinal:parent,
    pattern,classification:"syntactic_candidate",
    feature_ownership_verified:false,runtime_behavior_verified:false
   });
   parent=current;
  }
  for(const [k,v] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v))for(const x of v)walk(x,parent);
   else if(v&&typeof v==="object")walk(v,parent);
  }
 }
 walk(ast,null);
 return {function_nodes:total,matches};
}
function scan(dir){
 const entries=fs.readdirSync(dir).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
 if(entries.length>2000)throw Error("Too many bundles");
 const out={format_version:1,scope:"private_saved_javascript",
  classification:"source_syntax_feature_leads",
  captured_code_executed:false,feature_ownership_verified:false,
  runtime_behavior_verified:false,pattern_vocabulary:vocab,
  parsed_bundles:0,failed_bundles:0,skipped_oversize:0,function_nodes:0,matches:[],
  limitations:[
   "Candidate labels do not verify that a feature exists, loads, or runs.",
   "Member/property co-occurrence in a function does not establish true dataflow or module ownership.",
   "Only manually reviewed source and call chains may support a canonical finding.",
   "No source identifiers, paths, URLs, user text, credentials or snippets are emitted."
  ]};
 for(const entry of entries){
  const location=path.join(dir,entry),stat=fs.lstatSync(location);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsafe input");
  if(stat.size>8*1024*1024){out.skipped_oversize++;continue;}
  try{
   const ordinal=Number(entry.match(/^bundle-([0-9]+)\.js$/)[1]);
   const info=analyze(fs.readFileSync(location,"utf8"),ordinal);
   out.parsed_bundles++;
   out.function_nodes+=info.function_nodes;
   out.matches.push(...info.matches);
   if(out.matches.length>4000)throw Error("Too many matches");
  }catch(e){
   if(e.message==="Too many matches")throw e;
   out.failed_bundles++;
  }
 }
 out.matches.sort((a,b)=>a.source_ref.localeCompare(b.source_ref)||
  a.function_ordinal-b.function_ordinal||a.pattern.localeCompare(b.pattern));
 out.pattern_counts=Object.fromEntries(vocab.map(x=>[x,out.matches.filter(m=>m.pattern===x).length]));
 return out;
}
function selfTest(){
 const input=[
  "function search(x){return x.searchRequest({searchQuery:x.queryText,searchResults:x.searchHits})}",
  "function refresh(x){return {refreshToken:x.refreshToken,accessToken:x.accessToken}}",
  "function media(x){return x.currentTime+x.playbackState+x.playbackRate+x.pausePlayback}",
  "function edit(x){return x.editorState+x.applyTransaction+x.undoStack+x.selectionChange}",
  "function split(x){function inside(){return x.searchTerm+x.searchResults};return x.queryText}",
  "const privateSentinel='SYNTHETIC_SECRET_NOT_FOR_OUTPUT'"
 ].join(";");
 const sample=analyze(input,1);
 const found=new Set(sample.matches.map(x=>x.pattern));
 for(const expected of ["search_query_result_candidate","search_request_dispatch_candidate",
  "auth_refresh_candidate","media_progress_candidate","media_controls_candidate",
  "editor_transaction_candidate","editor_undo_selection_candidate"])assert(found.has(expected));
 assert(sample.matches.every(x=>!x.feature_ownership_verified&&!x.runtime_behavior_verified));
 assert(!JSON.stringify(sample).includes("SYNTHETIC_SECRET_NOT_FOR_OUTPUT"));
 assert.equal(sample.matches.filter(x=>x.pattern==="search_query_result_candidate").length,2);
}
if(require.main===module){
 if(process.argv.length===3&&process.argv[2]==="--self-test"){
  selfTest();console.log("Synthetic feature AST probe passed");
 }else if(process.argv.length===3){
  try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
  catch(_){process.stderr.write("Feature AST scan rejected (details suppressed)\n");process.exitCode=2;}
 }else{process.stderr.write("Usage: node scripts/trace_feature_impl.cjs <private-ordinal-js-directory>\n");process.exitCode=2;}
}
module.exports={analyze,scan,selfTest};
