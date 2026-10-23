#!/usr/bin/env node
"use strict";
/* Content-free AST candidate detector for virtualized lists and viewport
 * anchors. Parse downloaded source without evaluating it or logging tokens.
 * Output includes fixed category IDs and capture-local numeric ordinals only.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");

const RULES={
  measured_estimated_layout:["estimatedHeightPx","measuredHeightsByKey","turnKey"],
  viewport_overscan_range:["overscanCount","viewportHeightPx","bottomOffsetsPx"],
  retained_outside_window:["retainedTurnKeys","turnIndexByKey"],
  viewport_resize_tracking:["ResizeObserver","onViewportChange"],
  scroll_anchor_compensation:["compensateScrollToDistanceFromBottomPx","distanceFromBottomPx","turnIndexByKey"],
  targeted_turn_restore:["scrollToDistanceFromBottomPx","turnKey","align"],
  response_spacer_placement:["consumeGrowth","prepareThreadEndContent","scrollToBottom"],
  response_spacer_controller:["consumeGrowth","prepareThreadEndContent","placementTarget"],
  explicit_input_cancellation:["AbortController","wheel","touchstart","pointerdown","keydown"],
  history_render_boundary:["onHistoryRetentionBoundaryChange","firstProtectedItemId"]
};
const ALLOWED=new Set(Object.values(RULES).flat());
function name(node){
  if(node?.type==="Identifier")return node.name;
  if(node?.type==="Literal"&&typeof node.value==="string")return node.value;
  return null;
}
function inspectTree(root){
  const found=new Set();
  const stack=[root];
  while(stack.length){
    const node=stack.pop();
    if(!node||typeof node!=="object")continue;
    if(node.type==="Identifier"&&ALLOWED.has(node.name))found.add(node.name);
    if(node.type==="Literal"&&ALLOWED.has(node.value))found.add(node.value);
    if(node.type==="Property"||node.type==="MethodDefinition"){
      const value=name(node.key);
      if(ALLOWED.has(value))found.add(value);
    }
    if(node.type==="MemberExpression"){
      const value=(!node.computed||node.property?.type==="Literal")?
        name(node.property):null;
      if(ALLOWED.has(value))found.add(value);
    }
    for(const [key,value] of Object.entries(node)){
      if(["start","end","loc","raw"].includes(key))continue;
      if(Array.isArray(value)){
        for(let i=value.length-1;i>=0;i--)
          if(value[i]&&typeof value[i]==="object")stack.push(value[i]);
      }else if(value&&typeof value==="object")stack.push(value);
    }
  }
  return Object.entries(RULES).filter(([,needs])=>
    needs.every(term=>found.has(term))).map(([key])=>key);
}
function candidates(source,ordinal){
  const ast=acorn.parse(source,{ecmaVersion:"latest",sourceType:"module",
    allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
  const decl=ast.body.flatMap(x=>x.declaration?.declarations||[])
    .find(x=>x.id?.name==="__webpack_modules__");
  const modules=decl?.init?.type==="ObjectExpression"?
    decl.init.properties.map(x=>x.value):[ast];
  const matches=[];
  modules.forEach((module,i)=>{
    const patterns=inspectTree(module);
    if(patterns.length)matches.push({
      source_ref:"R-JS-"+String(ordinal).padStart(3,"0"),
      module_ordinal:i+1,patterns,
      classification:"syntactic_candidate",
      domain_ownership_verified:false
    });
  });
  return {module_count:modules.length,matches};
}
function scan(directory){
  const files=fs.readdirSync(directory)
    .filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
  if(files.length>2000)throw Error("Unsupported input count");
  const report={
    format_version:1,source_scope:"saved_javascript_ast",
    captured_source_executed:false,verified_ui_behavior:false,
    vocabulary:Object.keys(RULES),parsed_bundles:0,failed_bundles:0,
    oversize_skipped:0,modules_examined:0,matches:[],
    limitations:[
      "Patterns are module-wide syntactic associations, not verified UI component ownership.",
      "Identical identifiers may originate in generic libraries or unrelated features.",
      "A virtualized-row implementation does not prove it was mounted on a real page.",
      "Only capture-local ordinals and fixed labels are emitted; no code, source names, URLs or values."
    ]
  };
  for(const filename of files){
    const filepath=path.join(directory,filename);
    const stats=fs.lstatSync(filepath);
    if(!stats.isFile()||stats.isSymbolicLink())throw Error("Unsupported input");
    if(stats.size>8*1024*1024){report.oversize_skipped++;continue;}
    try{
      const ordinal=Number(filename.match(/^bundle-([0-9]+)\.js$/)[1]);
      const parsed=candidates(fs.readFileSync(filepath,"utf8"),ordinal);
      report.parsed_bundles++;
      report.modules_examined+=parsed.module_count;
      report.matches.push(...parsed.matches);
      if(report.matches.length>5000)throw Error("Too many candidates");
    }catch(err){
      if(err.message==="Too many candidates")throw err;
      report.failed_bundles++;
    }
  }
  report.counts=Object.fromEntries(Object.keys(RULES).map(label=>[
    label,report.matches.filter(match=>match.patterns.includes(label)).length
  ]));
  return report;
}
function selfTest(){
  const source=[
    "export const __webpack_modules__={",
    "alpha:function(){const estimatedHeightPx=20,measuredHeightsByKey={},turnKey='T';",
    "const overscanCount=2,viewportHeightPx=800,bottomOffsetsPx=[];",
    "const retainedTurnKeys=[],turnIndexByKey=new Map();",
    "new ResizeObserver(()=>{});const onViewportChange=()=>{};",
    "let distanceFromBottomPx=0;const compensateScrollToDistanceFromBottomPx=()=>{};",
    "const scrollToDistanceFromBottomPx=()=>{},align='top';",
    "},",
    "beta:function(){const consumeGrowth=()=>{},prepareThreadEndContent=()=>{},scrollToBottom=()=>{},placementTarget=null;",
    "const abort=new AbortController();const types=['wheel','touchstart','pointerdown','keydown'];",
    "const onHistoryRetentionBoundaryChange=()=>{},firstProtectedItemId=null;}",
    "}; const SENSITIVE='SECRET_PRIVATE_SENTINEL';"
  ].join("");
  const result=candidates(source,1);
  assert.equal(result.matches.length,2);
  assert(result.matches[0].patterns.includes("viewport_overscan_range"));
  assert(result.matches[0].patterns.includes("measured_estimated_layout"));
  assert(result.matches[0].patterns.includes("scroll_anchor_compensation"));
  assert(result.matches[1].patterns.includes("explicit_input_cancellation"));
  assert(result.matches[1].patterns.includes("response_spacer_placement"));
  assert(result.matches[1].patterns.includes("response_spacer_controller"));
  assert(result.matches[1].patterns.includes("history_render_boundary"));
  assert(!JSON.stringify(result).includes("SECRET_PRIVATE_SENTINEL"));
  assert.equal(candidates("function unrelated(){return 2}",2).matches.length,0);
}
if(require.main===module){
  if(process.argv.length===3&&process.argv[2]==="--self-test"){
    selfTest();process.stdout.write("Synthetic viewport candidate scan passed\n");
  }else if(process.argv.length===3){
    try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
    catch(_){process.stderr.write("Private viewport scanner failed (details suppressed)\n");process.exitCode=2;}
  }else{process.stderr.write("Usage: node scripts/trace_viewport_impl.cjs <private-js-directory>\n");process.exitCode=2;}
}
module.exports={candidates,scan,selfTest};
