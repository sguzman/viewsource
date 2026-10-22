#!/usr/bin/env node
"use strict";
/* Offline source-only transport inspection.
 * Parse, do not evaluate any downloaded JavaScript. Emit only fixed
 * vocabulary and resource ordinals; never emit raw strings/paths/values.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");

const METHODS=new Set([
  "startCompletionStream","resumeCompletionStream","cancelStream",
  "getStreamOptions","createCompletionStreamHandlers"
]);
const CALLBACKS=new Set([
  "onComplete","onError","onEvent","onDecodedEvent","onResume",
  "onResumeToken","onPrematureTermination","onRecoverableError",
  "onTransportClose","onStreamData","onUpdate"
]);
const OPERATIONS=new Set([
  "handler_factory","stream_post","topic_start","cancellation_registry",
  "request_cancel","resume_configuration","retry_configuration",
  "event_decoder","event_callbacks","transport_close","websocket_recovery"
]);

function property(n){
  if(!n)return null;
  if(n.type==="Identifier")return n.name;
  if(n.type==="Literal"&&typeof n.value==="string")return n.value;
  return null;
}
function memberName(n){
  if(n?.type!=="MemberExpression")return null;
  if(n.computed)return n.property.type==="Literal"?property(n.property):null;
  return property(n.property);
}
function visit(root,visitor){
  const stack=[root];
  while(stack.length){
    const node=stack.pop();
    if(!node||typeof node!=="object")continue;
    visitor(node);
    for(const [key,value] of Object.entries(node)){
      if(["start","end","loc","raw"].includes(key))continue;
      if(Array.isArray(value)){
        for(let i=value.length-1;i>=0;i--)
          if(value[i]&&typeof value[i]==="object")stack.push(value[i]);
      }else if(value&&typeof value==="object")stack.push(value);
    }
  }
}
function inspectMethod(node){
  const operations=new Set(), callbacks=new Set(), calledMethods=new Set();
  visit(node.value.body,n=>{
    if(n.type==="CallExpression"){
      const callee=memberName(n.callee);
      if(callee==="createCompletionStreamHandlers"){
        operations.add("handler_factory");
        calledMethods.add(callee);
      }
      if(callee==="streamPost")operations.add("stream_post");
      if(callee==="startFromTopic")operations.add("topic_start");
      if(callee==="cancelStream")operations.add("request_cancel");
      if(callee==="delete" && memberName(n.callee.object)==="completionCancellations")
        operations.add("cancellation_registry");
      if(callee==="onPotentialMissedMessages"||callee==="onReconnect")
        operations.add("websocket_recovery");
      if(callee==="close")operations.add("transport_close");
    }
    if(n.type==="MemberExpression" && memberName(n)==="completionCancellations")
      operations.add("cancellation_registry");
    if(n.type==="Property"){
      const key=property(n.key);
      if(CALLBACKS.has(key))callbacks.add(key);
      if(key==="resumeState"||key==="initialStreamIsResume"||key==="resumeToken")
        operations.add("resume_configuration");
      if(key==="retryConfig"||key==="maxRetryCount")
        operations.add("retry_configuration");
      if(key==="parseEventData")operations.add("event_decoder");
    }
  });
  if(callbacks.size)operations.add("event_callbacks");
  return {operations:[...operations].sort(),callbacks:[...callbacks].sort(),
    called_methods:[...calledMethods].sort()};
}
function analyzeText(text,ordinal){
  const ast=acorn.parse(text,{ecmaVersion:"latest",sourceType:"module",
    allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
  const records=[];
  visit(ast,n=>{
    if(n.type==="MethodDefinition"&&METHODS.has(property(n.key))&&n.value?.body){
      const inspected=inspectMethod(n);
      records.push({
        source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
        method:property(n.key),
        operations:inspected.operations,
        callbacks:inspected.callbacks,
        called_methods:inspected.called_methods,
        evidence_class:"observed_static_syntax",
        live_execution_verified:false
      });
    }
  });
  return records;
}
function scan(directory){
  const names=fs.readdirSync(directory).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
  if(names.length>2000)throw Error("Too many sources");
  const report={
    format_version:1,source_scope:"local_saved_javascript",method:"ast_method_vocabulary",
    live_execution_verified:false,backend_protocol_verified:false,
    parsed_bundles:0,failed_bundles:0,skipped_oversize_bundles:0,
    method_records:[],operation_vocabulary:[...OPERATIONS].sort(),
    limitations:[
      "Method-name matches are candidate class implementations; aliases and dynamic property access are unresolved.",
      "Operations in nested callbacks are lexical containment, not proof that they executed.",
      "Method calls to the same name can resolve to different receivers; record consumers before attributing call edges.",
      "No captured code, request path, payload, source filename or customer data is emitted."
    ]
  };
  for(const name of names){
    const info=fs.lstatSync(path.join(directory,name));
    if(!info.isFile()||info.isSymbolicLink())throw Error("Unsupported input entry");
    if(info.size>8*1024*1024){report.skipped_oversize_bundles++;continue;}
    try{
      const ordinal=Number(name.match(/^bundle-([0-9]+)\.js$/)[1]);
      report.method_records.push(...analyzeText(fs.readFileSync(path.join(directory,name),"utf8"),ordinal));
      report.parsed_bundles++;
    }catch(_){report.failed_bundles++;}
  }
  report.method_records.sort((a,b)=>a.source_ref.localeCompare(b.source_ref)||a.method.localeCompare(b.method));
  return report;
}
function selfTest(){
  const source=[
    "class FakeTransport {",
    "async startCompletionStream(e){const h=this.createCompletionStreamHandlers({onComplete:e.onComplete,onError:e.onError});return Request.streamPost('synthetic',{onEvent:h.onEvent})}",
    "resumeCompletionStream(e){const h=this.createCompletionStreamHandlers({resumeState:e,initialStreamIsResume:true,onResume:e.onResume});return e.topicId?h.startFromTopic(e.topicId):Request.streamPost('synthetic',{})}",
    "cancelStream(id){this.completionCancellations.delete(id);Request.cancelStream(id)}",
    "getStreamOptions(){return {parseEventData:()=>1}}",
    "createCompletionStreamHandlers(e){return {onRecoverableError:e.onRecoverableError,onPrematureTermination:e.onPrematureTermination,retryConfig:{maxRetryCount:3}}}",
    "}",
    "const privateText='SECRET_SYNTHETIC_USER_123'"
  ].join("\n");
  const matches=analyzeText(source,1);
  assert.equal(matches.length,5);
  const named=Object.fromEntries(matches.map(x=>[x.method,x]));
  assert(named.startCompletionStream.operations.includes("handler_factory"));
  assert(named.startCompletionStream.operations.includes("stream_post"));
  assert(named.resumeCompletionStream.operations.includes("topic_start"));
  assert(named.cancelStream.operations.includes("request_cancel"));
  assert(named.cancelStream.operations.includes("cancellation_registry"));
  assert(named.getStreamOptions.operations.includes("event_decoder"));
  assert(named.createCompletionStreamHandlers.operations.includes("retry_configuration"));
  assert(!JSON.stringify(matches).includes("SECRET_SYNTHETIC_USER_123"));
  const absent=analyzeText("class Other {x(){return 1}}",2);
  assert.equal(absent.length,0);
}
if(require.main===module){
  if(process.argv.length===3&&process.argv[2]==="--self-test"){
    selfTest();process.stdout.write("Synthetic transport AST probe passed\n");
  }else if(process.argv.length===3){
    try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
    catch(_){process.stderr.write("Private transport AST probe failed\n");process.exitCode=2;}
  }else{process.stderr.write("Usage: node scripts/trace_stream_impl.cjs <private-js-directory>\n");process.exitCode=2;}
}
module.exports={analyzeText,scan,selfTest};
