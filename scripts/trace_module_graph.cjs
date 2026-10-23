#!/usr/bin/env node
"use strict";
/* Source-only module dependency index. Never execute captured JavaScript.
 * Private module keys are used only in memory to join import candidates.
 * Output uses capture-local resource/module ordinals and aggregate counts.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");
const MAX_FILES=2000,MAX_MODULES=50000,MAX_CANDIDATES=250000;
function registry(ast){
 const found=[];
 for(const top of ast.body){
  const vars=top.declaration?.declarations||[];
  for(const decl of vars){
   if(decl.id?.type==="Identifier"&&decl.id.name==="__webpack_modules__"&&
      decl.init?.type==="ObjectExpression")found.push(...decl.init.properties);
  }
 }
 return found;
}
function keyName(node){
 if(node?.type==="Identifier")return node.name;
 if(node?.type==="Literal"&&typeof node.value==="string")return node.value;
 return null;
}
function literalMember(node){
 if(node?.type!=="MemberExpression")return null;
 if(node.computed)return node.property?.type==="Literal"?keyName(node.property):null;
 return keyName(node.property);
}
function memberOf(node,base){
 return node?.type==="MemberExpression"&&node.object?.type==="Identifier"
   &&node.object.name===base?literalMember(node):null;
}

/* Track imported object aliases within lexical function/block scopes, not by
 * spelling across the entire bundle factory. Unknown/reassigned bindings are
 * excluded; the resulting export-interface match remains a static candidate. */
function scanScopedRequiredSlots(fn,requireName,required){
 const loaderIdentity=Symbol("factory_require");
 function bind(pattern,env,value=null){
  if(!pattern)return;
  if(pattern.type==="Identifier"){env.set(pattern.name,value);return;}
  if(pattern.type==="RestElement")return bind(pattern.argument,env,null);
  if(pattern.type==="AssignmentPattern")return bind(pattern.left,env,null);
  if(pattern.type==="ArrayPattern"){
   for(const p of pattern.elements)bind(p,env,null);
  }else if(pattern.type==="ObjectPattern"){
   for(const p of pattern.properties){
    bind(p.type==="RestElement"?p.argument:p.value,env,null);
   }
  }
 }
 function importKey(init,env){
  if(!requireName||env.get(requireName)!==loaderIdentity||
     init?.type!=="CallExpression"||
     init.callee?.type!=="Identifier"||
     init.callee.name!==requireName||
     init.arguments[0]?.type!=="Literal"||
     typeof init.arguments[0].value!=="string")return null;
  return init.arguments[0].value;
 }
 function walk(node,env){
  if(!node||typeof node!=="object")return;
  if(node.type==="BlockStatement"){
   const block=new Map(env);
   for(const stmt of node.body){
    if(stmt.type==="VariableDeclaration")
     for(const decl of stmt.declarations)bind(decl.id,block,null);
    if((stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")&&stmt.id)
     bind(stmt.id,block,null);
   }
   for(const stmt of node.body)walk(stmt,block);
   return;
  }
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type)){
   const nested=new Map(env);
   if(node.id)bind(node.id,nested,null);
   for(const param of node.params||[])bind(param,nested,null);
   walk(node.body,nested);
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    walk(decl.init,env);
    if(decl.id?.type==="Identifier")
     env.set(decl.id.name,importKey(decl.init,env));
    else bind(decl.id,env,null);
   }
   return;
  }
  if(node.type==="AssignmentExpression"&&node.left?.type==="Identifier")
   env.set(node.left.name,null);
  if(node.type==="MemberExpression"&&node.object?.type==="Identifier"){
   const id=env.get(node.object.name),slot=literalMember(node);
   if(id&&slot){
    if(!required.has(id))required.set(id,new Set());
    required.get(id).add(slot);
   }
  }
  for(const [k,v] of Object.entries(node)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const child of v)if(child&&typeof child==="object")walk(child,env);
   }else if(v&&typeof v==="object")walk(v,env);
  }
 }
 const env=new Map();
 for(const param of fn.params||[])bind(param,env,null);
 if(requireName&&fn.params?.[2]?.type==="Identifier"&&
    fn.params[2].name===requireName)env.set(requireName,loaderIdentity);
 walk(fn.body,env);
}

function scanModuleSignatures(fn,requireName,exportName){
 const exported=new Set(),required=new Map();
 const stack=[fn.body];
 while(stack.length){
  const n=stack.pop();
  if(!n||typeof n!=="object")continue;
  if(exportName&&n.type==="AssignmentExpression"){
   const slot=memberOf(n.left,exportName);
   if(slot)exported.add(slot);
  }
  if(requireName&&n.type==="CallExpression"
      &&n.callee?.type==="MemberExpression"
      &&memberOf(n.callee,requireName)==="d"
      &&n.arguments[0]?.type==="Identifier"
      &&n.arguments[0].name===exportName
      &&n.arguments[1]?.type==="ObjectExpression"){
   for(const prop of n.arguments[1].properties){
    const slot=keyName(prop.key);if(slot)exported.add(slot);
   }
  }
  for(const [k,v] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const c of v)if(c&&typeof c==="object")stack.push(c);
   }else if(v&&typeof v==="object")stack.push(v);
  }
 }
 scanScopedRequiredSlots(fn,requireName,required);
 return {exportedSlots:[...exported],
   requiredByImport:Object.fromEntries([...required].map(([id,slots])=>[id,[...slots]]))};
}

/* Very conservative startup syntax: only direct, top-level webpack calls
 * and immediately invoked function bodies. Never infer activation from a
 * function merely declared, stored as a callback or present in a module. */
function bootstrapCalls(ast,sourceOrdinal) {
 const found=new Set();
 function startKey(arg){
  if(arg?.type==="Literal"&&typeof arg.value==="string")return arg.value;
  if(arg?.type==="AssignmentExpression"&&arg.operator==="="&&
     arg.left?.type==="MemberExpression"&&
     arg.left.object?.type==="Identifier"&&arg.left.object.name==="__webpack_require__"&&
     literalMember(arg.left)==="s"&&
     arg.right?.type==="Literal"&&typeof arg.right.value==="string")
   return arg.right.value;
  return null;
 }
 function visit(node){
  if(!node||typeof node!=="object")return;
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type))
   return;
  if(node.type==="CallExpression"){
   if(node.callee?.type==="Identifier"&&node.callee.name==="__webpack_require__"){
    const key=startKey(node.arguments[0]);
    if(key)found.add(key);
   }
   if(["FunctionExpression","ArrowFunctionExpression"].includes(node.callee?.type))
    visit(node.callee.body);
  }
  for(const [name,value] of Object.entries(node)){
   if(["start","end","loc","raw","callee"].includes(name))continue;
   if(Array.isArray(value)){
    for(const child of value)visit(child);
   }else if(value&&typeof value==="object")visit(value);
  }
 }
 for(const stmt of ast.body){
  if(stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")continue;
  visit(stmt);
 }
 return [...found].map(key=>({key,sourceOrdinal}));
}


const DYNAMIC_LABELS=[
 "dynamic_import_literal_candidate",
 "dynamic_import_computed_candidate",
 "bundler_chunk_loader_candidate"
];
function dynamicSyntax(fn,requireName){
 const patterns=new Set(),stack=[fn.body];
 while(stack.length){
  const n=stack.pop();
  if(!n||typeof n!=="object")continue;
  if(n.type==="ImportExpression"){
   const arg=n.source;
   patterns.add(arg?.type==="Literal"&&typeof arg.value==="string"?
      DYNAMIC_LABELS[0]:DYNAMIC_LABELS[1]);
  }
  if(requireName&&n.type==="CallExpression"&&
     memberOf(n.callee,requireName)==="e")patterns.add(DYNAMIC_LABELS[2]);
  for(const [k,v] of Object.entries(n)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const item of v)if(item&&typeof item==="object")stack.push(item);
   }else if(v&&typeof v==="object")stack.push(v);
  }
 }
 return [...patterns];
}


/* Name-only matching can invent imports when a nested callback shadows the
 * module factory's require parameter. Scope is tracked conservatively and
 * candidate edges are emitted only for references to the original parameter. */
function scanScopedModuleCalls(fn,requireName){
 const imports=new Set(),boundImports=new Set(),loaderIdentity=Symbol("factory_require");
 if(!requireName||fn.params?.[2]?.type!=="Identifier"||
    fn.params[2].name!==requireName)return {imports,boundImports};
 function shadows(pattern,env){
  if(!pattern)return;
  if(pattern.type==="Identifier"){
   if(pattern.name===requireName)env.set(requireName,null);
   return;
  }
  if(pattern.type==="RestElement"||pattern.type==="AssignmentPattern")
   return shadows(pattern.argument||pattern.left,env);
  if(pattern.type==="ArrayPattern"){
   for(const part of pattern.elements)shadows(part,env);
  }else if(pattern.type==="ObjectPattern"){
   for(const prop of pattern.properties)
    shadows(prop.type==="RestElement"?prop.argument:prop.value,env);
  }
 }
 function walk(node,env){
  if(!node||typeof node!=="object")return;
  if(node.type==="BlockStatement"){
   const scoped=new Map(env);
   for(const stmt of node.body){
    if(stmt.type==="VariableDeclaration")
     for(const decl of stmt.declarations)shadows(decl.id,scoped);
    if((stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")&&stmt.id)
     shadows(stmt.id,scoped);
   }
   for(const stmt of node.body)walk(stmt,scoped);
   return;
  }
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type)){
   const nested=new Map(env);
   if(node.id)shadows(node.id,nested);
   for(const param of node.params||[])shadows(param,nested);
   walk(node.body,nested);
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    walk(decl.init,env);
    shadows(decl.id,env);
   }
   return;
  }
  if(node.type==="AssignmentExpression"&&node.left?.type==="Identifier"&&
     node.left.name===requireName)env.set(requireName,null);
  if(node.type==="CallExpression"&&env.get(requireName)===loaderIdentity){
   if(node.callee?.type==="Identifier"&&node.callee.name===requireName&&
      node.arguments[0]?.type==="Literal"&&
      typeof node.arguments[0].value==="string")
    imports.add(node.arguments[0].value);
   if(memberOf(node.callee,requireName)==="bind"&&
      node.arguments[0]?.type==="Identifier"&&
      node.arguments[0].name===requireName&&
      node.arguments[1]?.type==="Literal"&&
      typeof node.arguments[1].value==="string")
    boundImports.add(node.arguments[1].value);
  }
  for(const [k,v] of Object.entries(node)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const child of v)if(child&&typeof child==="object")walk(child,env);
   }else if(v&&typeof v==="object")walk(v,env);
  }
 }
 walk(fn.body,new Map([[requireName,loaderIdentity]]));
 return {imports,boundImports};
}

function analyzeJS(source,sourceOrdinal){
 const ast=acorn.parse(source,{ecmaVersion:"latest",sourceType:"module",
   allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
 const entries=registry(ast),result=[];
 Object.defineProperty(result,"bootstrapCandidates",
   {value:bootstrapCalls(ast,sourceOrdinal),enumerable:false});
 for(let i=0;i<entries.length;i++){
  const module=entries[i],identifier=keyName(module.key),fn=module.value;
  if(!identifier||!["FunctionExpression","ArrowFunctionExpression"].includes(fn?.type)){
   result.push({identifier,sourceOrdinal,moduleOrdinal:i+1,imports:[],eligible:false});continue;
  }
  const requireParam=fn.params?.[2];
  const requireName=requireParam?.type==="Identifier"?requireParam.name:null;
  const exportName=fn.params?.[1]?.type==="Identifier"?fn.params[1].name:null;
  const signatures=scanModuleSignatures(fn,requireName,exportName);
  const {imports,boundImports}=scanScopedModuleCalls(fn,requireName);
  result.push({identifier,sourceOrdinal,moduleOrdinal:i+1,imports:[...imports],
    boundImports:[...boundImports],
    eligible:!!requireName,exportedSlots:signatures.exportedSlots,
    requiredByImport:signatures.requiredByImport,
    dynamic_syntax:dynamicSyntax(fn,requireName)});
 }
 return result;
}
function buildGraph(all,scanned,parseFailures,bootstrap=[]){
 if(all.length>MAX_MODULES)throw Error("Too many modules");
 const index=new Map();
 for(const x of all){
  if(!x.identifier)continue;
  if(!index.has(x.identifier))index.set(x.identifier,[]);
  index.get(x.identifier).push(x);
 }
 const links=[],shapeCandidates=[],boundCandidates=[];
 for(const item of all){
  for(const key of item.boundImports||[]){
   const matches=index.get(key)||[];
   boundCandidates.push({
    source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
    module_ordinal:item.moduleOrdinal,
    classification:matches.length===1?"bound_import_target_candidate":
      matches.length>1?"ambiguous_bound_import":"missing_bound_import_target",
    ...(matches.length===1?{
     candidate_target_ref:"R-JS-"+String(matches[0].sourceOrdinal).padStart(3,"0"),
     candidate_target_module:matches[0].moduleOrdinal
    }:{}),
    definition_candidates:matches.length,
    binding_executed_verified:false,target_module_loaded_verified:false
   });
  }
 }
 const dynamicBoundaries=all.flatMap(item=>
  (item.dynamic_syntax||[]).map(pattern=>({
   source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
   module_ordinal:item.moduleOrdinal,pattern,
   classification:"unresolved_dynamic_boundary",
   target_module_verified:false
  })));
 dynamicBoundaries.sort((a,b)=>a.source_ref.localeCompare(b.source_ref)||
  a.module_ordinal-b.module_ordinal||a.pattern.localeCompare(b.pattern));
 const bootstrapCandidates=[];
 for(const candidate of bootstrap){
  const matches=index.get(candidate.key)||[];
  bootstrapCandidates.push({
   callsite_ref:"R-JS-"+String(candidate.sourceOrdinal).padStart(3,"0"),
   classification:matches.length===1?"unique_registry_key_candidate":
     matches.length>1?"ambiguous_registry_key":"missing_saved_module",
   ...(matches.length===1?{
    target_ref:"R-JS-"+String(matches[0].sourceOrdinal).padStart(3,"0"),
    target_module:matches[0].moduleOrdinal
   }:{}),
   registry_definition_candidates:matches.length,
   bootstrap_execution_verified:false
  });
 }
 let candidateCalls=0,unresolved=0,ambiguous=0;
 for(const item of all){
  for(const id of item.imports){
   candidateCalls++;
   if(candidateCalls>MAX_CANDIDATES)throw Error("Too many import candidates");
   const matches=index.get(id);
   if(!matches){unresolved++;continue;}
   if(matches.length!==1){
    ambiguous++;
    const needed=item.requiredByImport?.[id]||[];
    if(needed.length>0){
     const candidates=matches.filter(target=>
       needed.every(slot=>(target.exportedSlots||[]).includes(slot)));
     if(candidates.length===1){
      const target=candidates[0];
      shapeCandidates.push({
       from_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
       from_module:item.moduleOrdinal,
       to_ref:"R-JS-"+String(target.sourceOrdinal).padStart(3,"0"),
       to_module:target.moduleOrdinal,
       required_export_count:needed.length,
       registry_definition_candidates:matches.length,
       matching_export_interfaces:1,
       classification:"candidate_unique_export_interface",
       runtime_import_verified:false
      });
     }
    }
    continue;
   }
   const target=matches[0];
   links.push({
    from_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
    from_module:item.moduleOrdinal,
    to_ref:"R-JS-"+String(target.sourceOrdinal).padStart(3,"0"),
    to_module:target.moduleOrdinal,
    classification:"static_import_candidate",
    runtime_import_verified:false
   });
  }
 }
 links.sort((a,b)=>a.from_ref.localeCompare(b.from_ref)||a.from_module-b.from_module||
   a.to_ref.localeCompare(b.to_ref)||a.to_module-b.to_module);
 return {
  format_version:1,scope:"private_saved_javascript_modules",
  source_executed:false,module_runtime_loaded_verified:false,
  parsed_bundles:scanned,failed_bundles:parseFailures,
  bootstrap_call_candidates:bootstrapCandidates.length,
  bootstrap_candidates:bootstrapCandidates,
  bootstrap_runtime_verified:false,
  dynamic_boundary_candidates:dynamicBoundaries,
  dynamic_boundary_count:dynamicBoundaries.length,
  dynamic_boundary_vocabulary:DYNAMIC_LABELS,
  bound_import_candidates:boundCandidates,
  bound_import_candidate_count:boundCandidates.length,
  modules_total:all.length,
  modules_with_import_parameter:all.filter(x=>x.eligible).length,
  import_candidates:candidateCalls,unique_resolved_links:links.length,
  unresolved_import_candidates:unresolved,ambiguous_import_candidates:ambiguous,
  cross_bundle_links:links.filter(x=>x.from_ref!==x.to_ref).length,
  same_bundle_links:links.filter(x=>x.from_ref===x.to_ref).length,
  module_census:[...all.reduce((map,x)=>{
    map.set(x.sourceOrdinal,(map.get(x.sourceOrdinal)||0)+1);
    return map;
   },new Map())]
   .map(([id,count])=>({source_ref:"R-JS-"+String(id).padStart(3,"0"),count}))
   .sort((a,b)=>a.source_ref.localeCompare(b.source_ref)),
  resolved_links:links,
  export_shape_candidates:shapeCandidates,
  export_shape_candidate_count:shapeCandidates.length,
  limitations:[
   "Bootstrap candidates require direct top-level or immediately-invoked __webpack_require__ literal calls; other startup patterns are not covered.",
   "Candidate bootstrap calls do not show that a browser invoked or loaded a module.",
   "Static require calls may be conditional, dead, or nested in inactive closures.",
   "A resolved bundled module reference is not proof that a module loaded or ran.",
   "Duplicate module-key candidates are deliberately ambiguous and excluded from resolved links.",
   "Export-shape matches are candidate disambiguations only; minified alias shadowing or dead code can create misleading required slots.",
   "Export-shape candidates do not change unique/ambiguous import counts and require independent source inspection before promotion.",
   "Dynamic import expressions and bundler chunk-loader calls are recorded as unresolved boundary syntax, never followed as import edges.",
   "Function-bound module-loader callbacks are future-import candidates, not direct calls or verified loads.",
   "Only literal require arguments are considered; dynamic module keys are unresolved.",
   "No private module keys, source bytes, URLs, filenames or account data are emitted."
  ]
 };
}
function scan(directory){
 const entries=fs.readdirSync(directory).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
 if(entries.length>MAX_FILES)throw Error("Too many bundles");
 let parsed=0,failed=0;
 const modules=[],bootstrap=[];
 for(const entry of entries){
  const full=path.join(directory,entry),stat=fs.lstatSync(full);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported file");
  if(stat.size>8*1024*1024){failed++;continue;}
  const ordinal=Number(entry.match(/^bundle-([0-9]+)\.js$/)[1]);
  try{
   const report=analyzeJS(fs.readFileSync(full,"utf8"),ordinal);
   modules.push(...report);
   bootstrap.push(...report.bootstrapCandidates);
   parsed++;
  }
  catch(_){failed++;}
 }
 return buildGraph(modules,parsed,failed,bootstrap);
}
function selfTest(){
 const s1="export const __webpack_modules__={A:(function(e,t,n){const b=n('B');t.a=()=>b.a}),B:(function(e,t,n){t.a=()=>1})};";
 const s2="export const __webpack_modules__={C:(function(e,t,n){const a=n('A');const missing=n('External');t.a=a})};";
 const a=[...analyzeJS(s1,1),...analyzeJS(s2,2)];
 const o=buildGraph(a,2,0);
 assert.equal(o.modules_total,3);
 assert.equal(o.import_candidates,3);
 assert.equal(o.unique_resolved_links,2);
 assert.equal(o.unresolved_import_candidates,1);
 assert.equal(o.cross_bundle_links,1);
 assert.equal(o.same_bundle_links,1);
 assert.equal(o.resolved_links[0].from_ref,"R-JS-001");
 assert.equal(o.resolved_links[0].to_module,2);
 assert(!JSON.stringify(o).includes("External"));
 assert(!JSON.stringify(o).includes("const b"));
 const dynamicArchive=analyzeJS("export const __webpack_modules__={D:(function(e,t,n){"+
  "import('private-module');import(t.route);n.e('private-chunk')})};",6);
 const dynamicReport=buildGraph(dynamicArchive,1,0);
 assert.equal(dynamicReport.dynamic_boundary_count,3);
 assert.deepEqual(new Set(dynamicReport.dynamic_boundary_candidates.map(x=>x.pattern)),new Set(DYNAMIC_LABELS));
 assert(!JSON.stringify(dynamicReport).includes("private-module"));
 assert(!JSON.stringify(dynamicReport).includes("private-chunk"));
 const boot='export const __webpack_modules__={Startup:(function(e,t,n){t.a=1})};__webpack_require__("Startup");';
 const source=analyzeJS(boot,4);
 const startup=buildGraph(source,1,0,source.bootstrapCandidates);
 assert.equal(startup.bootstrap_call_candidates,1);
 assert.equal(startup.bootstrap_candidates[0].classification,"unique_registry_key_candidate");
 assert.equal(startup.bootstrap_candidates[0].target_module,1);
 assert.equal(startup.bootstrap_candidates[0].bootstrap_execution_verified,false);
 const delayed=analyzeJS('export const __webpack_modules__={A:function(){}};function dormant(){__webpack_require__("A")}',5);
 assert.equal(delayed.bootstrapCandidates.length,0);
 const withHoles=analyzeJS('export const __webpack_modules__={A:function(){}};'+
  'const a=[null,,()=>__webpack_require__("A")];',5);
 assert.equal(withHoles.bootstrapCandidates.length,0);
 const invokedWithHoles=analyzeJS('export const __webpack_modules__={A:function(){}};'+
  'const a=[null,,(()=>__webpack_require__("A"))()];',5);
 assert.equal(invokedWithHoles.bootstrapCandidates.length,1);
 const invoked=analyzeJS('export const __webpack_modules__={A:function(){}};(()=>__webpack_require__("A"))()',5);
 assert.equal(invoked.bootstrapCandidates.length,1);
 assert(!JSON.stringify(startup).includes("Startup"));
 const ambiguous=buildGraph([...a,...analyzeJS(s1,3)],3,0);
 assert(ambiguous.ambiguous_import_candidates>=1);
 const shapeSource1="export const __webpack_modules__={X:(function(e,t,n){const recovery=n('K');recovery.h();recovery.p()}),K:(function(e,t,n){n.d(t,{h:()=>1,p:()=>2})})};";
 const shapeSource2="export const __webpack_modules__={K:(function(e,t){t.a=1})};";
 const resolved=buildGraph([...analyzeJS(shapeSource1,1),...analyzeJS(shapeSource2,2)],2,0);
 assert.equal(resolved.ambiguous_import_candidates,1);
 assert.equal(resolved.export_shape_candidate_count,1);
 assert.equal(resolved.export_shape_candidates[0].to_ref,"R-JS-001");
 assert.equal(resolved.export_shape_candidates[0].required_export_count,2);
 assert(!JSON.stringify(resolved).includes("'K'"));
 assert(!JSON.stringify(resolved).includes("recovery.h"));
 const boundSource=analyzeJS("export const __webpack_modules__={A:(function(e,t,n){"+
   "const later=n.bind(n,'B')}),B:(function(e,t,n){t.a=1})};",7);
 const boundReport=buildGraph(boundSource,1,0);
 assert.equal(boundReport.bound_import_candidate_count,1);
 assert.equal(boundReport.unique_resolved_links,0);
 assert.equal(boundReport.bound_import_candidates[0].classification,"bound_import_target_candidate");
 assert.equal(boundReport.bound_import_candidates[0].candidate_target_module,2);
 assert.equal(boundReport.bound_import_candidates[0].target_module_loaded_verified,false);
 const shadowOnly=analyzeJS("export const __webpack_modules__={"+
  "Shadow:(function(e,t,n){function local(n){const a=n('Private');a.x()}"+
  "function bound(n){return n.bind(n,'Private')} }),"+
  "Private:(function(e,t,n){t.x=1})};",8);
 const shadowReport=buildGraph(shadowOnly,1,0);
 assert.equal(shadowReport.import_candidates,0);
 assert.equal(shadowReport.bound_import_candidate_count,0);
 const captureNested=analyzeJS("export const __webpack_modules__={"+
  "Factory:(function(e,t,n){const lazy=()=>n('Link')}),"+
  "Link:(function(e,t,n){t.x=1})};",8);
 assert.equal(buildGraph(captureNested,1,0).unique_resolved_links,1);
 const scopedConsumer="export const __webpack_modules__={"
   +"Outer:(function(e,t,n){function owner(){const local=n('K')}"
   +"function unrelated(){const local={h:()=>1};return local.h()}}),"
   +"K:(function(e,t,n){n.d(t,{h:()=>1})})};";
 const duplicateK="export const __webpack_modules__={K:(function(e,t){t.x=1})};";
 const scoped=buildGraph([...analyzeJS(scopedConsumer,1),...analyzeJS(duplicateK,2)],2,0);
 assert.equal(scoped.ambiguous_import_candidates,1);
 assert.equal(scoped.export_shape_candidate_count,0);

}
if(require.main===module){
 if(process.argv.length===3&&process.argv[2]==="--self-test"){
  selfTest();process.stdout.write("Synthetic module-graph probe passed\n");
 }else if(process.argv.length===3){
  try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
  catch(_){process.stderr.write("Static module graph scan failed (details suppressed)\n");process.exitCode=2;}
 }else{process.stderr.write("Usage: node scripts/trace_module_graph.cjs <private-js-dir>\n");process.exitCode=2;}
}
module.exports={analyzeJS,buildGraph,scan,selfTest};
