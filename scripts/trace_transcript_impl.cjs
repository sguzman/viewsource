#!/usr/bin/env node
"use strict";
/* Candidate-only, offline AST research into saved conversation render pipelines.
 * NEVER evaluate captured assets. Never publish names, strings, URLs or code.
 * A lexical candidate is not source-verified feature ownership.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");

const FUNCTION_KINDS=new Set(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"]);
const CLASSES=[
 "render_turn_derivation","pending_turn_preparation","first_user_item_filter",
 "typed_turn_renderer","message_dom_identity_wrapper","alternate_selected_render"
];
function name(node){
 if(!node)return null;
 if(node.type==="Identifier")return node.name;
 if(node.type==="Literal"&&typeof node.value==="string")return node.value;
 return null;
}
function member(node){
 if(node?.type!=="MemberExpression")return null;
 if(node.computed)return node.property?.type==="Literal"?name(node.property):null;
 return name(node.property);
}
function profile(fn){
 const keys=new Set(),reads=new Set(),literals=new Set(),calls=new Set();
 const stack=[fn.body];
 while(stack.length){
  const n=stack.pop();
  if(!n||typeof n!=="object")continue;
  if(n.type==="Property"){
   const key=name(n.key);if(key)keys.add(key);
  }
  if(n.type==="MemberExpression"){
   const key=member(n);if(key)reads.add(key);
  }
  if(n.type==="Literal"&&typeof n.value==="string"){
   if(["user-message","assistant-message"].includes(n.value))literals.add(n.value);
  }
  if(n.type==="CallExpression"){
   const key=member(n.callee);if(key)calls.add(key);
  }
  for(const [key,value] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(key))continue;
   if(Array.isArray(value)){
    for(const child of value)if(child&&typeof child==="object")stack.push(child);
   }else if(value&&typeof value==="object")stack.push(value);
  }
 }
 const has=(set,...values)=>values.every(x=>set.has(x));
 const matches=[];
 if(has(keys,"renderedTurns","messages","turns"))matches.push("render_turn_derivation");
 if(has(keys,"renderedConversation","renderedTurns","showPendingLoadingMessage"))
  matches.push("pending_turn_preparation");
 if(keys.has("hideInitialUserMessage")&&reads.has("items")&&calls.has("filter"))
  matches.push("first_user_item_filter");
 if(has(keys,"turn","turnId")&&reads.has("items")&&
     has(literals,"user-message","assistant-message"))matches.push("typed_turn_renderer");
 if(has(keys,"data-message-id","data-message-author-role","data-source-message-ids"))
  matches.push("message_dom_identity_wrapper");
 if(keys.has("renderedTurns")&&keys.has("hideInitialUserMessage")&&
     reads.has("promptMessageId"))matches.push("alternate_selected_render");
 return matches;
}
function inspect(text,ordinal){
 const ast=acorn.parse(text,{ecmaVersion:"latest",sourceType:"module",
  allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
 let fnOrdinal=0;
 const matches=[],stack=[ast];
 while(stack.length){
  const n=stack.pop();if(!n||typeof n!=="object")continue;
  if(FUNCTION_KINDS.has(n.type)){
   fnOrdinal++;
   for(const pattern of profile(n)){
    matches.push({source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
      function_ordinal:fnOrdinal,pattern,
      classification:"candidate_static_syntax",render_behavior_verified:false});
   }
  }
  for(const [key,value] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(key))continue;
   if(Array.isArray(value)){
    for(let i=value.length-1;i>=0;i--)
     if(value[i]&&typeof value[i]==="object")stack.push(value[i]);
   }else if(value&&typeof value==="object")stack.push(value);
  }
 }
 return {function_nodes:fnOrdinal,matches};
}
function scan(dir){
 const names=fs.readdirSync(dir).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
 if(names.length>2000)throw Error("Too many source files");
 const result={format_version:1,source_scope:"private_saved_javascript",
  parsed_bundles:0,failed_bundles:0,skipped_oversize_bundles:0,
  source_executed:false,render_behavior_verified:false,function_nodes:0,
  matches:[],pattern_vocabulary:CLASSES,
  limitations:[
   "Function-pattern matches are candidate research leads, not verified transcript implementations.",
   "Lexical scanning includes nested callback fields; this does not establish execution or exact ownership.",
   "All dynamic imports and rendered UI outcomes require separate review.",
   "No source text, URLs, message identities, original filenames or user data are printed."
  ]};
 for(const file of names){
  const full=path.join(dir,file),stat=fs.lstatSync(full);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported input");
  if(stat.size>8*1024*1024){result.skipped_oversize_bundles++;continue;}
  try{
   const ord=Number(file.match(/^bundle-([0-9]+)\.js$/)[1]);
   const parsed=inspect(fs.readFileSync(full,"utf8"),ord);
   result.parsed_bundles++;result.function_nodes+=parsed.function_nodes;
   result.matches.push(...parsed.matches);
   if(result.matches.length>4000)throw Error("Too many candidates");
  }catch(err){
   if(err.message==="Too many candidates")throw err;
   result.failed_bundles++;
  }
 }
 result.pattern_counts=Object.fromEntries(CLASSES.map(c=>
  [c,result.matches.filter(x=>x.pattern===c).length]));
 return result;
}
function selfTest(){
 const synthetic=[
 "function derive(){return {messages:[],turns:new Map(),renderedTurns:[]}}",
 "function prepare(){return {renderedConversation:{},renderedTurns:[],showPendingLoadingMessage:false}}",
 "function filter(e){let x=e.hideInitialUserMessage;return e.turn.items.filter(y=>y.type==='user-message')}",
 "function display(e){let{turn,turnId}=e;return turn.items.map(x=>x.type==='user-message'||x.type==='assistant-message')}",
 "function wrapper(x){return {'data-message-id':x.id,'data-message-author-role':'assistant','data-source-message-ids':x.sources}}",
 "function page(e){return {hideInitialUserMessage:e.hideInitialUserMessage,renderedTurns:e.turns.map(x=>x.promptMessageId)}}",
 "const privateText='SYNTHETIC_PRIVATE_MESSAGE_DO_NOT_PUBLISH'"
 ].join(";");
 const d=inspect(synthetic,1);
 assert.equal(d.function_nodes,9); // includes the inline callback arrows
 for(const term of CLASSES)
  assert(d.matches.some(x=>x.pattern===term),term);
 assert(!JSON.stringify(d).includes("SYNTHETIC_PRIVATE_MESSAGE"));
 assert.equal(inspect("function unrelated(){return 42}",2).matches.length,0);
}
if(require.main===module){
 if(process.argv.length===3&&process.argv[2]==="--self-test"){
  selfTest();process.stdout.write("Synthetic transcript AST classifier passed\n");
 }else if(process.argv.length===3){
  try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
  catch(_){process.stderr.write("Transcript AST scan rejected (details suppressed)\n");process.exitCode=2;}
 }else{process.stderr.write("Usage: node scripts/trace_transcript_impl.cjs <private-js-dir>\n");process.exitCode=2;}
}
module.exports={inspect,scan,selfTest};
