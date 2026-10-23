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
function analyzeJS(source,sourceOrdinal){
 const ast=acorn.parse(source,{ecmaVersion:"latest",sourceType:"module",
   allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
 const entries=registry(ast),result=[];
 for(let i=0;i<entries.length;i++){
  const module=entries[i],identifier=keyName(module.key),fn=module.value;
  if(!identifier||!["FunctionExpression","ArrowFunctionExpression"].includes(fn?.type)){
   result.push({identifier,sourceOrdinal,moduleOrdinal:i+1,imports:[],eligible:false});continue;
  }
  const requireParam=fn.params?.[2];
  const requireName=requireParam?.type==="Identifier"?requireParam.name:null;
  const imports=new Set(),stack=[fn.body];
  while(stack.length){
   const n=stack.pop();
   if(!n||typeof n!=="object")continue;
   if(requireName&&n.type==="CallExpression"&&n.callee?.type==="Identifier"&&
      n.callee.name===requireName&&n.arguments.length>=1){
    const first=n.arguments[0];
    if(first.type==="Literal"&&typeof first.value==="string")
      imports.add(first.value);
   }
   for(const [k,v] of Object.entries(n)){
    if(["start","end","loc","raw"].includes(k))continue;
    if(Array.isArray(v)){
     for(const c of v)if(c&&typeof c==="object")stack.push(c);
    }else if(v&&typeof v==="object")stack.push(v);
   }
  }
  result.push({identifier,sourceOrdinal,moduleOrdinal:i+1,imports:[...imports],eligible:!!requireName});
 }
 return result;
}
function buildGraph(all,scanned,parseFailures){
 if(all.length>MAX_MODULES)throw Error("Too many modules");
 const index=new Map();
 for(const x of all){
  if(!x.identifier)continue;
  if(!index.has(x.identifier))index.set(x.identifier,[]);
  index.get(x.identifier).push(x);
 }
 const links=[];
 let candidateCalls=0,unresolved=0,ambiguous=0;
 for(const item of all){
  for(const id of item.imports){
   candidateCalls++;
   if(candidateCalls>MAX_CANDIDATES)throw Error("Too many import candidates");
   const matches=index.get(id);
   if(!matches){unresolved++;continue;}
   if(matches.length!==1){ambiguous++;continue;}
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
  modules_total:all.length,
  modules_with_import_parameter:all.filter(x=>x.eligible).length,
  import_candidates:candidateCalls,unique_resolved_links:links.length,
  unresolved_import_candidates:unresolved,ambiguous_import_candidates:ambiguous,
  cross_bundle_links:links.filter(x=>x.from_ref!==x.to_ref).length,
  same_bundle_links:links.filter(x=>x.from_ref===x.to_ref).length,
  module_census:Object.entries(Object.groupBy(all,x=>x.sourceOrdinal))
   .map(([id,items])=>({source_ref:"R-JS-"+String(id).padStart(3,"0"),count:items.length}))
   .sort((a,b)=>a.source_ref.localeCompare(b.source_ref)),
  resolved_links:links,
  limitations:[
   "Static require calls may be conditional, dead, or nested in inactive closures.",
   "A resolved bundled module reference is not proof that a module loaded or ran.",
   "Duplicate module-key candidates are deliberately ambiguous and excluded from resolved links.",
   "Only literal require arguments are considered; dynamic module keys are unresolved.",
   "No private module keys, source bytes, URLs, filenames or account data are emitted."
  ]
 };
}
function scan(directory){
 const entries=fs.readdirSync(directory).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
 if(entries.length>MAX_FILES)throw Error("Too many bundles");
 let parsed=0,failed=0;
 const modules=[];
 for(const entry of entries){
  const full=path.join(directory,entry),stat=fs.lstatSync(full);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported file");
  if(stat.size>8*1024*1024){failed++;continue;}
  const ordinal=Number(entry.match(/^bundle-([0-9]+)\.js$/)[1]);
  try{modules.push(...analyzeJS(fs.readFileSync(full,"utf8"),ordinal));parsed++;}
  catch(_){failed++;}
 }
 return buildGraph(modules,parsed,failed);
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
 const ambiguous=buildGraph([...a,...analyzeJS(s1,3)],3,0);
 assert(ambiguous.ambiguous_import_candidates>=1);
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
