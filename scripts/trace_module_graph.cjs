#!/usr/bin/env node
"use strict";
/* Source-only module dependency index. Never execute captured JavaScript.
 * Private module keys are used only in memory to join import candidates.
 * Output uses capture-local resource/module ordinals and aggregate counts.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const acorn=require("acorn");
const MAX_FILES=2000,MAX_MODULES=50000,MAX_CANDIDATES=250000;
function assertCandidateCapacity(count){
 if(!Number.isSafeInteger(count)||count<0||count>MAX_CANDIDATES)
  throw Error("Too many static candidate records");
}
function webpackChunkReceiver(node){
 if(node?.type==="AssignmentExpression"&&node.operator==="=")
  return webpackChunkReceiver(node.left);
 if(node?.type!=="MemberExpression")return null;
 const slot=literalMember(node);
 return typeof slot==="string"&&slot.startsWith("webpackChunk")&&
   node.object?.type==="Identifier"&&
   ["self","window","globalThis"].includes(node.object.name)?slot:null;
}
function registry(ast){
 const found=[];
 for(const top of ast.body){
  const declaration=top.type==="VariableDeclaration"?top:top.declaration;
  const vars=declaration?.declarations||[];
  for(const decl of vars){
   if(decl.id?.type==="Identifier"&&decl.id.name==="__webpack_modules__"&&
      decl.init?.type==="ObjectExpression")
     found.push(...decl.init.properties.map(property=>({property,domain:"unscoped"})));
  }
  // Recognize the registration syntax only. A queued chunk is not a
  // browser-confirmed module load or runtime execution.
  const expr=top.type==="ExpressionStatement"?top.expression:null;
  if(expr?.type!=="CallExpression"||literalMember(expr.callee)!=="push")
   continue;
  const chunkName=webpackChunkReceiver(expr.callee.object);
  if(!chunkName)continue;
  const batch=expr.arguments[0];
  const table=batch?.type==="ArrayExpression"?batch.elements[1]:null;
  if(table?.type==="ObjectExpression")
   found.push(...table.properties.map(property=>({property,domain:"chunk:"+chunkName})));
 }
 return found;
}
function moduleKey(node){
 if(node?.type!=="Literal")return null;
 if(typeof node.value==="string")return node.value;
 if(typeof node.value==="number"&&Number.isSafeInteger(node.value)&&node.value>=0)
  return String(node.value);
 return null;
}
function keyName(node){
 if(node?.type==="Identifier")return node.name;
 return moduleKey(node);
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
/* Preserve uncertainty from assignments to inherited bindings in conditional
 * scopes. Local declarations only shadow their enclosing scope and must not
 * invalidate an inherited identifier after the branch. */
function bindingNames(pattern,result){
 if(!pattern)return;
 if(pattern.type==="Identifier"){result.add(pattern.name);return;}
 if(pattern.type==="RestElement"||pattern.type==="AssignmentPattern"){
  bindingNames(pattern.argument||pattern.left,result);return;
 }
 if(pattern.type==="ArrayPattern"){
  for(const item of pattern.elements)bindingNames(item,result);
 }else if(pattern.type==="ObjectPattern"){
  for(const prop of pattern.properties)
   bindingNames(prop.type==="RestElement"?prop.argument:prop.value,result);
 }
}
function hoistedFunctionVars(node,names){
 if(!node||typeof node!=="object")return;
 if(["FunctionExpression","FunctionDeclaration","ArrowFunctionExpression"].includes(node.type))
  return;
 if(node.type==="VariableDeclaration"&&node.kind==="var")
  for(const decl of node.declarations)bindingNames(decl.id,names);
 for(const [key,value] of Object.entries(node)){
  if(["start","end","loc","raw"].includes(key))continue;
  if(Array.isArray(value)){
   for(const child of value)hoistedFunctionVars(child,names);
  }else if(value&&typeof value==="object")hoistedFunctionVars(value,names);
 }
}
function localNamesForScope(node){
 const locals=new Set();
 if(node.type==="CatchClause")bindingNames(node.param,locals);
 if(["ForStatement","ForInStatement","ForOfStatement"].includes(node.type)){
  const binding=node.type==="ForStatement"?node.init:node.left;
  if(binding?.type==="VariableDeclaration"&&binding.kind!=="var"){
   for(const decl of binding.declarations)bindingNames(decl.id,locals);
  }
 }
 const statements=node.type==="BlockStatement"?node.body:
  node.type==="SwitchStatement"?node.cases.flatMap(x=>x.consequent):[];
 for(const statement of statements){
  if(statement.type==="VariableDeclaration"&&statement.kind!=="var")
   for(const decl of statement.declarations)bindingNames(decl.id,locals);
  if((statement.type==="FunctionDeclaration"||statement.type==="ClassDeclaration")&&
     statement.id)bindingNames(statement.id,locals);
 }
 return locals;
}
function invalidateOuterBindings(outer,inner,localNames){
 for(const [name,value] of outer){
  if(!localNames.has(name)&&inner.get(name)!==value)outer.set(name,null);
 }
}
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
     init.arguments.length<1)return null;
  return moduleKey(init.arguments[0]);
 }
 function walk(node,env){
  if(!node||typeof node!=="object")return;
  if(node.type==="CatchClause"){
   const caught=new Map(env);
   bind(node.param,caught,null);
   walk(node.body,caught);
   invalidateOuterBindings(env,caught,localNamesForScope(node));
   return;
  }
  if(["ForStatement","ForInStatement","ForOfStatement"].includes(node.type)){
   const loop=new Map(env);
   if(node.type==="ForStatement"){
    walk(node.init,loop);
    walk(node.test,loop);
    walk(node.update,loop);
   }else{
    // for...of/in assigns to its left-hand target. A mutation of
    // imported.foo cannot establish foo as an original export.
    if(!["MemberExpression","ObjectPattern","ArrayPattern"].includes(node.left?.type))
     walk(node.left,loop);
    walk(node.right,loop);
   }
   if(node.type!=="ForStatement"&&node.left?.type!=="VariableDeclaration"){
    const assigned=new Set();
    bindingNames(node.left,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   if(node.type!=="ForStatement"&&
      node.left?.type==="VariableDeclaration"&&node.left.kind==="var"){
    const assigned=new Set();
    for(const item of node.left.declarations)bindingNames(item.id,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   walk(node.body,loop);
   invalidateOuterBindings(env,loop,localNamesForScope(node));
   return;
  }
  if(node.type==="SwitchStatement"){
   walk(node.discriminant,env);
   const cases=new Map(env);
   for(const branch of node.cases){
    for(const stmt of branch.consequent){
     if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var"){
      for(const declaration of stmt.declarations)
       bind(declaration.id,cases,null);
     }
    }
   }
   for(const branch of node.cases)walk(branch,cases);
   invalidateOuterBindings(env,cases,localNamesForScope(node));
   return;
  }
  if(node.type==="BlockStatement"){
   const block=new Map(env);
   for(const stmt of node.body){
    if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var")
     for(const decl of stmt.declarations)bind(decl.id,block,null);
    if((stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")&&stmt.id)
     bind(stmt.id,block,null);
   }
   for(const stmt of node.body)walk(stmt,block);
   invalidateOuterBindings(env,block,localNamesForScope(node));
   return;
  }
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type)){
   const nested=new Map(env);
   if(node.id)bind(node.id,nested,null);
   for(const param of node.params||[])bind(param,nested,null);
   const hoisted=new Set();
   hoistedFunctionVars(node.body,hoisted);
   for(const id of hoisted)if(id===requireName)nested.set(id,null);
   walk(node.body,nested);
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    walk(decl.init,env);
    if(node.kind==="var"&&!decl.init)continue;
    if(decl.id?.type==="Identifier")
     env.set(decl.id.name,importKey(decl.init,env));
    else bind(decl.id,env,null);
   }
   return;
  }
  if(node.type==="AssignmentExpression"){
   if(node.left?.type==="Identifier")env.set(node.left.name,null);
   if(node.left?.type==="MemberExpression"){
    // For a member assignment, only receiver evaluation is a read.
    walk(node.left.object,env);
    if(node.left.computed)walk(node.left.property,env);
    walk(node.right,env);
    return;
   }
   if(["ObjectPattern","ArrayPattern"].includes(node.left?.type)){
    const assigned=new Set();
    bindingNames(node.left,assigned);
    for(const id of assigned)if(env.has(id))env.set(id,null);
    walk(node.right,env);
    return;
   }
  }
  if(node.type==="UpdateExpression"&&node.argument?.type==="Identifier"){
   if(env.has(node.argument.name))env.set(node.argument.name,null);
   return;
  }
  if(node.type==="UpdateExpression"||node.type==="UnaryExpression"&&
     node.operator==="delete"){
   if(node.argument?.type==="MemberExpression"){
    walk(node.argument.object,env);
    if(node.argument.computed)walk(node.argument.property,env);
    return;
   }
  }
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

/* Export signatures are inferred only where the bundle factory export
 * parameter and loader have not been shadowed or reassigned. Computed export
 * keys are excluded unless their property keys are literal constants. */
function scanScopedExports(fn,requireName,exportName,moduleName){
 const slots=new Set(),directFunctions=[],exportToken=Symbol("factory_exports"),
  loaderToken=Symbol("factory_require"),moduleToken=Symbol("factory_module");
 if(!exportName&&!moduleName)return {slots,directFunctions};
 function neutralize(pattern,env){
  if(!pattern)return;
  if(pattern.type==="Identifier"){
   if(pattern.name===exportName||pattern.name===requireName||
      pattern.name===moduleName)
    env.set(pattern.name,null);
  }else if(pattern.type==="RestElement"||pattern.type==="AssignmentPattern"){
   neutralize(pattern.argument||pattern.left,env);
  }else if(pattern.type==="ArrayPattern"){
   for(const part of pattern.elements)neutralize(part,env);
  }else if(pattern.type==="ObjectPattern"){
   for(const prop of pattern.properties)
    neutralize(prop.type==="RestElement"?prop.argument:prop.value,env);
  }
 }
 function scan(node,env){
  if(!node||typeof node!=="object")return;
  if(node.type==="CatchClause"){
   const caught=new Map(env);
   neutralize(node.param,caught);
   scan(node.body,caught);
   invalidateOuterBindings(env,caught,localNamesForScope(node));
   return;
  }
  if(["ForStatement","ForInStatement","ForOfStatement"].includes(node.type)){
   const loop=new Map(env);
   if(node.type==="ForStatement"){
    scan(node.init,loop);
    scan(node.test,loop);
    scan(node.update,loop);
   }else{
    scan(node.left,loop);
    scan(node.right,loop);
   }
   if(node.type!=="ForStatement"&&node.left?.type!=="VariableDeclaration"){
    const assigned=new Set();
    bindingNames(node.left,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   if(node.type!=="ForStatement"&&
      node.left?.type==="VariableDeclaration"&&node.left.kind==="var"){
    const assigned=new Set();
    for(const item of node.left.declarations)bindingNames(item.id,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   scan(node.body,loop);
   invalidateOuterBindings(env,loop,localNamesForScope(node));
   return;
  }
  if(node.type==="SwitchStatement"){
   scan(node.discriminant,env);
   const cases=new Map(env);
   for(const branch of node.cases){
    for(const stmt of branch.consequent){
     if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var"){
      for(const declaration of stmt.declarations)
       neutralize(declaration.id,cases,null);
     }
    }
   }
   for(const branch of node.cases)scan(branch,cases);
   invalidateOuterBindings(env,cases,localNamesForScope(node));
   return;
  }
  if(node.type==="BlockStatement"){
   const local=new Map(env);
   for(const stmt of node.body){
    if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var")
     for(const decl of stmt.declarations)neutralize(decl.id,local);
    if((stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")&&stmt.id)
     neutralize(stmt.id,local);
   }
   for(const stmt of node.body)scan(stmt,local);
   invalidateOuterBindings(env,local,localNamesForScope(node));
   return;
  }
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type)){
   const nested=new Map(env);
   neutralize(node.id,nested);
   for(const param of node.params||[])neutralize(param,nested);
   const hoisted=new Set();
   hoistedFunctionVars(node.body,hoisted);
   for(const id of hoisted)if(id===exportName||id===moduleName||id===requireName)nested.set(id,null);
   scan(node.body,nested);
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    scan(decl.init,env);
    if(node.kind==="var"&&!decl.init)continue;
    neutralize(decl.id,env);
   }
   return;
  }
  if(node.type==="UpdateExpression"&&node.argument?.type==="Identifier")
   neutralize(node.argument,env);
  if(node.type==="AssignmentExpression"){
   if(node.left?.type==="MemberExpression"){
    let slot=null,classification=null;
    if(exportName&&env.get(exportName)===exportToken){
     slot=memberOf(node.left,exportName);
     if(slot)classification="direct_function_export_assignment_candidate";
    }
    if(!slot&&moduleName&&env.get(moduleName)===moduleToken&&
       memberOf(node.left.object,moduleName)==="exports"){
     slot=literalMember(node.left);
     if(slot)classification="module_exports_property_function_candidate";
    }
    if(slot){
     slots.add(slot);
     if(node.operator==="="&&
        ["FunctionExpression","ArrowFunctionExpression"].includes(node.right?.type))
      directFunctions.push({position:node.start,classification});
    }
   }
   if(moduleName&&env.get(moduleName)===moduleToken&&
      memberOf(node.left,moduleName)==="exports"){
    // module.exports replacement can detach the factory's original exports
    // parameter. Earlier property assignments and later writes via that
    // parameter cannot prove the final public export interface.
    slots.clear();
    directFunctions.length=0;
    if(node.operator==="="&&
       ["FunctionExpression","ArrowFunctionExpression"].includes(node.right?.type))
     directFunctions.push({
      position:node.start,
      classification:"module_object_function_assignment_candidate"
     });
    if(exportName)env.set(exportName,null);
   }
   if(["Identifier","ObjectPattern","ArrayPattern"].includes(node.left?.type))
    neutralize(node.left,env);
  }
  if(node.type==="CallExpression"&&requireName&&
     env.get(requireName)===loaderToken&&env.get(exportName)===exportToken&&
     memberOf(node.callee,requireName)==="d"&&
     node.arguments[0]?.type==="Identifier"&&
     node.arguments[0].name===exportName&&
     node.arguments[1]?.type==="ObjectExpression"){
   for(const prop of node.arguments[1].properties){
    if(prop.type!=="Property"||(prop.computed&&prop.key?.type!=="Literal"))
     continue;
    const slot=keyName(prop.key);
    if(slot)slots.add(slot);
   }
  }
  for(const [k,v] of Object.entries(node)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const child of v)if(child&&typeof child==="object")scan(child,env);
   }else if(v&&typeof v==="object")scan(v,env);
  }
 }
 const initial=new Map();
 for(const param of fn.params||[])neutralize(param,initial);
 if(fn.params?.[1]?.type==="Identifier"&&fn.params[1].name===exportName)
  initial.set(exportName,exportToken);
 if(requireName&&fn.params?.[2]?.type==="Identifier"&&fn.params[2].name===requireName)
  initial.set(requireName,loaderToken);
 if(moduleName&&fn.params?.[0]?.type==="Identifier"&&fn.params[0].name===moduleName)
  initial.set(moduleName,moduleToken);
 scan(fn.body,initial);
 return {slots,directFunctions:directFunctions.sort((a,b)=>a.position-b.position)};
}
function scanModuleSignatures(fn,requireName,exportName,moduleName){
 const {slots:exported,directFunctions}=scanScopedExports(fn,requireName,exportName,moduleName),
  required=new Map();
 scanScopedRequiredSlots(fn,requireName,required);
 return {exportedSlots:[...exported],
  directFunctionExports:directFunctions.map(x=>x.classification),
  requiredByImport:Object.fromEntries([...required].map(([id,slots])=>[id,[...slots]]))};
}

/* Very conservative startup syntax: only direct, top-level webpack calls
 * and immediately invoked function bodies. Never infer activation from a
 * function merely declared, stored as a callback or present in a module. */
function bootstrapCalls(ast,sourceOrdinal) {
 const found=new Set(),loader="__webpack_require__",valid=Symbol("bootstrap_loader");
 function startKey(arg){
  if(moduleKey(arg)!==null)return moduleKey(arg);
  if(arg?.type==="AssignmentExpression"&&arg.operator==="="&&
     arg.left?.type==="MemberExpression"&&
     arg.left.object?.type==="Identifier"&&arg.left.object.name===loader&&
     literalMember(arg.left)==="s"&&moduleKey(arg.right)!==null)
   return moduleKey(arg.right);
  return null;
 }
 function walk(node,env){
  if(!node||typeof node!=="object")return;
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression",
      "ClassDeclaration","ClassExpression"].includes(node.type))return;
  if(node.type==="CatchClause"||node.type==="BlockStatement"||
     node.type==="ForStatement"||node.type==="ForInStatement"||
     node.type==="ForOfStatement"||node.type==="SwitchStatement"){
   const scope=new Map(env),locals=localNamesForScope(node);
   if(locals.has(loader))scope.set(loader,null);
   if(node.type==="BlockStatement"){
    for(const stmt of node.body)walk(stmt,scope);
   }else if(node.type==="CatchClause"){
    walk(node.body,scope);
   }else if(node.type==="SwitchStatement"){
    walk(node.discriminant,env);
    for(const branch of node.cases)for(const stmt of branch.consequent)walk(stmt,scope);
   }else if(node.type==="ForStatement"){
    walk(node.init,scope);walk(node.test,scope);walk(node.update,scope);
    walk(node.body,scope);
   }else{
    walk(node.right,scope);
    if(node.left?.type==="VariableDeclaration"){
     if(node.left.kind==="var"){
      const names=new Set();
      for(const decl of node.left.declarations)bindingNames(decl.id,names);
      if(names.has(loader))scope.set(loader,null);
     }
    }else{
     const names=new Set();bindingNames(node.left,names);
     if(names.has(loader))scope.set(loader,null);
    }
    walk(node.body,scope);
   }
   invalidateOuterBindings(env,scope,locals);
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    walk(decl.init,env);
    const names=new Set();bindingNames(decl.id,names);
    if(names.has(loader)&&decl.init)env.set(loader,null);
   }
   return;
  }
  if(node.type==="AssignmentExpression"){
   walk(node.right,env);
   const names=new Set();bindingNames(node.left,names);
   if(names.has(loader))env.set(loader,null);
   return;
  }
  if(node.type==="UpdateExpression"&&node.argument?.type==="Identifier"&&
     node.argument.name===loader){env.set(loader,null);return;}
  if(node.type==="CallExpression"){
   if(env.get(loader)===valid&&node.callee?.type==="Identifier"&&
      node.callee.name===loader){
    const key=startKey(node.arguments[0]);
    if(key!==null)found.add(key);
   }
   if(["FunctionExpression","ArrowFunctionExpression"].includes(node.callee?.type)){
    const fn=node.callee,inside=new Map(env),locals=new Set();
    for(const param of fn.params||[])bindingNames(param,locals);
    hoistedFunctionVars(fn.body,locals);
    if(locals.has(loader))inside.set(loader,null);
    walk(fn.body,inside);
    invalidateOuterBindings(env,inside,locals);
   }
   for(const arg of node.arguments)walk(arg,env);
   return;
  }
  for(const [name,value] of Object.entries(node)){
   if(["start","end","loc","raw","callee"].includes(name))continue;
   if(Array.isArray(value)){
    for(const child of value)walk(child,env);
   }else if(value&&typeof value==="object")walk(value,env);
  }
 }
 const env=new Map([[loader,valid]]);
 for(const stmt of ast.body)walk(stmt,env);
 return [...found].map(key=>({key,sourceOrdinal}));
}

const DYNAMIC_LABELS=[
 "dynamic_import_literal_candidate",
 "dynamic_import_computed_candidate",
 "bundler_chunk_loader_candidate",
 "computed_module_require_candidate"
];
function dynamicSyntax(fn,requireName,scopeCalls){
 const patterns=new Set(),stack=[fn.body];
 if(scopeCalls.computedRequire)patterns.add(DYNAMIC_LABELS[3]);
 if(scopeCalls.chunkLoader)patterns.add(DYNAMIC_LABELS[2]);
 while(stack.length){
  const n=stack.pop();
  if(!n||typeof n!=="object")continue;
  if(n.type==="ImportExpression"){
   const arg=n.source;
   patterns.add(arg?.type==="Literal"&&typeof arg.value==="string"?
      DYNAMIC_LABELS[0]:DYNAMIC_LABELS[1]);
  }
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
 const imports=new Set(),directImports=new Set(),nestedImports=new Set(),
  boundImports=new Set(),loaderIdentity=Symbol("factory_require");
 let computedRequire=false,chunkLoader=false,literalCallCount=0;
 let nestedLiteralCallCount=0,nestedFunctionDepth=0;
 if(!requireName||fn.params?.[2]?.type!=="Identifier"||
    fn.params[2].name!==requireName)
     return {imports,directImports,nestedImports,boundImports,
       computedRequire,chunkLoader,literalCallCount,nestedLiteralCallCount};
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
  if(node.type==="CatchClause"){
   const caught=new Map(env);
   shadows(node.param,caught);
   walk(node.body,caught);
   invalidateOuterBindings(env,caught,localNamesForScope(node));
   return;
  }
  if(["ForStatement","ForInStatement","ForOfStatement"].includes(node.type)){
   const loop=new Map(env);
   if(node.type==="ForStatement"){
    walk(node.init,loop);
    walk(node.test,loop);
    walk(node.update,loop);
   }else{
    walk(node.left,loop);
    walk(node.right,loop);
   }
   if(node.type!=="ForStatement"&&node.left?.type!=="VariableDeclaration"){
    const assigned=new Set();
    bindingNames(node.left,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   if(node.type!=="ForStatement"&&
      node.left?.type==="VariableDeclaration"&&node.left.kind==="var"){
    const assigned=new Set();
    for(const item of node.left.declarations)bindingNames(item.id,assigned);
    for(const id of assigned)if(loop.has(id))loop.set(id,null);
   }
   walk(node.body,loop);
   invalidateOuterBindings(env,loop,localNamesForScope(node));
   return;
  }
  if(node.type==="SwitchStatement"){
   walk(node.discriminant,env);
   const cases=new Map(env);
   for(const branch of node.cases){
    for(const stmt of branch.consequent){
     if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var"){
      for(const declaration of stmt.declarations)
       shadows(declaration.id,cases,null);
     }
    }
   }
   for(const branch of node.cases)walk(branch,cases);
   invalidateOuterBindings(env,cases,localNamesForScope(node));
   return;
  }
  if(node.type==="BlockStatement"){
   const scoped=new Map(env);
   for(const stmt of node.body){
    if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var")
     for(const decl of stmt.declarations)shadows(decl.id,scoped);
    if((stmt.type==="FunctionDeclaration"||stmt.type==="ClassDeclaration")&&stmt.id)
     shadows(stmt.id,scoped);
   }
   for(const stmt of node.body)walk(stmt,scoped);
   invalidateOuterBindings(env,scoped,localNamesForScope(node));
   return;
  }
  if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type)){
   const nested=new Map(env);
   if(node.id)shadows(node.id,nested);
   for(const param of node.params||[])shadows(param,nested);
   nestedFunctionDepth++;
   const hoisted=new Set();
   hoistedFunctionVars(node.body,hoisted);
   for(const id of hoisted)if(id===requireName)nested.set(id,null);
   walk(node.body,nested);
   nestedFunctionDepth--;
   return;
  }
  if(node.type==="VariableDeclaration"){
   for(const decl of node.declarations){
    walk(decl.init,env);
    if(node.kind==="var"&&!decl.init)continue;
    shadows(decl.id,env);
   }
   return;
  }
  if(node.type==="UpdateExpression"&&node.argument?.type==="Identifier"&&
     node.argument.name===requireName)env.set(requireName,null);
  if(node.type==="AssignmentExpression"){
   const assigned=new Set();
   bindingNames(node.left,assigned);
   if(assigned.has(requireName))env.set(requireName,null);
  }
  if(node.type==="CallExpression"&&env.get(requireName)===loaderIdentity){
   if(node.callee?.type==="Identifier"&&node.callee.name===requireName&&
      node.arguments.length>=1){
    const key=moduleKey(node.arguments[0]);
    if(key!==null){
     literalCallCount++;
     if(nestedFunctionDepth>0){
      nestedLiteralCallCount++;
      nestedImports.add(key);
     }else directImports.add(key);
     imports.add(key);
    }else computedRequire=true;
   }
   if(memberOf(node.callee,requireName)==="e")chunkLoader=true;
   if(memberOf(node.callee,requireName)==="bind"&&
      node.arguments[0]?.type==="Identifier"&&
      node.arguments[0].name===requireName&&
      moduleKey(node.arguments[1])!==null)
    boundImports.add(moduleKey(node.arguments[1]));
  }
  for(const [k,v] of Object.entries(node)){
   if(["start","end","loc","raw"].includes(k))continue;
   if(Array.isArray(v)){
    for(const child of v)if(child&&typeof child==="object")walk(child,env);
   }else if(v&&typeof v==="object")walk(v,env);
  }
 }
 walk(fn.body,new Map([[requireName,loaderIdentity]]));
 return {imports,directImports,nestedImports,boundImports,computedRequire,
   chunkLoader,literalCallCount,nestedLiteralCallCount};
}

/* A Webpack chunk may include a third-position runtime callback. Only
 * literal, direct call or return statements to the callback parameter
 * are startup syntax candidates. Nested/conditional callbacks are skipped.
 * This callback was not executed by the analyzer or observed in a browser. */
function runtimeLoaderReassigned(node,name,shadowed=false){
 if(!node||typeof node!=="object")return false;
 if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression"].includes(node.type))
  return false;
 if(node.type==="CallExpression"&&
    ["FunctionExpression","ArrowFunctionExpression"].includes(node.callee?.type)){
  const fn=node.callee,names=new Set();
  for(const param of fn.params||[])bindingNames(param,names);
  hoistedFunctionVars(fn.body,names);
  if(runtimeLoaderReassigned(fn.body,name,shadowed||names.has(name)))
   return true;
 }
 const innerShadow=()=>{
  if(node.type==="CatchClause"){
   const names=new Set();bindingNames(node.param,names);
   return shadowed||names.has(name);
  }
  if(["ForStatement","ForOfStatement","ForInStatement"].includes(node.type)){
   const decl=node.type==="ForStatement"?node.init:node.left;
   if(decl?.type==="VariableDeclaration"&&decl.kind!=="var"){
    const names=new Set();
    for(const item of decl.declarations)bindingNames(item.id,names);
    return shadowed||names.has(name);
   }
  }
  if(node.type==="BlockStatement"||node.type==="SwitchStatement"){
   const statements=node.type==="BlockStatement"?node.body:
     node.cases.flatMap(x=>x.consequent);
   const names=new Set();
   for(const stmt of statements){
    if(stmt.type==="VariableDeclaration"&&stmt.kind!=="var")
     for(const decl of stmt.declarations)bindingNames(decl.id,names);
    if((stmt.type==="ClassDeclaration"||stmt.type==="FunctionDeclaration")&&stmt.id)
     bindingNames(stmt.id,names);
   }
   return shadowed||names.has(name);
  }
  return shadowed;
 };
 const childShadow=innerShadow();
 if(!shadowed){
  if(node.type==="AssignmentExpression"){
   const assigned=new Set();
   bindingNames(node.left,assigned);
   if(assigned.has(name))return true;
  }
  if(node.type==="UpdateExpression"&&node.argument?.type==="Identifier"&&
     node.argument.name===name)return true;
  if(node.type==="ForInStatement"||node.type==="ForOfStatement"){
   const assigned=new Set();
   if(node.left?.type==="VariableDeclaration"){
    if(node.left.kind==="var")
     for(const decl of node.left.declarations)bindingNames(decl.id,assigned);
   }else bindingNames(node.left,assigned);
   if(assigned.has(name))return true;
  }
  if(node.type==="VariableDeclaration"&&node.kind==="var"&&
     node.declarations.some(decl=>decl.id?.type==="Identifier"&&
       decl.id.name===name&&decl.init))return true;
 }
 for(const [key,child] of Object.entries(node)){
  if(["start","end","loc","raw"].includes(key))continue;
  if(Array.isArray(child)){
   if(child.some(item=>runtimeLoaderReassigned(item,name,childShadow)))return true;
  }else if(child&&typeof child==="object"&&
     runtimeLoaderReassigned(child,name,childShadow))return true;
 }
 return false;
}
function chunkRuntimeEntrypoints(ast,sourceOrdinal){
 const candidates=[];
 for(const top of ast.body){
  const expr=top.type==="ExpressionStatement"?top.expression:null;
  if(expr?.type!=="CallExpression"||literalMember(expr.callee)!=="push")
   continue;
  const namespace=webpackChunkReceiver(expr.callee.object);
  if(!namespace)continue;
  const chunk=expr.arguments[0];
  const runtime=chunk?.type==="ArrayExpression"?chunk.elements[2]:null;
  if(!["FunctionExpression","ArrowFunctionExpression"].includes(runtime?.type))
   continue;
  const first=runtime.params?.[0];
  if(first?.type!=="Identifier")continue;
  const body=runtime.body?.type==="BlockStatement"?runtime.body.body:[{
   type:"ReturnStatement",argument:runtime.body
  }];
  let factoryLoaderValid=true;
  for(const statement of body){
   if(runtimeLoaderReassigned(statement,first.name))factoryLoaderValid=false;
   if(!factoryLoaderValid)continue;
   const call=statement?.type==="ExpressionStatement"?statement.expression:
    statement?.type==="ReturnStatement"?statement.argument:null;
   if(call?.type!=="CallExpression"||call.callee?.type!=="Identifier"||
      call.callee.name!==first.name)continue;
   const key=moduleKey(call.arguments[0]);
   if(key!==null)candidates.push({
    key,sourceOrdinal,domain:"chunk:"+namespace,
    bootstrap_kind:"chunk_runtime_literal_call_candidate"
   });
  }
 }
 return candidates;
}

function analyzeJS(source,sourceOrdinal){
 const ast=acorn.parse(source,{ecmaVersion:"latest",sourceType:"module",
   allowReturnOutsideFunction:true,allowImportExportEverywhere:true});
 const entries=registry(ast),result=[];
 Object.defineProperty(result,"bootstrapCandidates",
   {value:[...bootstrapCalls(ast,sourceOrdinal).map(x=>({
      ...x,domain:"unscoped",bootstrap_kind:"top_level_literal_call_candidate"
    })),...chunkRuntimeEntrypoints(ast,sourceOrdinal)],enumerable:false});
 for(let i=0;i<entries.length;i++){
  const {property,domain}=entries[i],
   unresolvedComputedKey=property.computed&&moduleKey(property.key)===null,
   identifier=unresolvedComputedKey?null:keyName(property.key),
   fn=property.value;
  if(!["FunctionExpression","ArrowFunctionExpression"].includes(fn?.type)){
   result.push({identifier,domain,sourceOrdinal,moduleOrdinal:i+1,
    imports:[],literalCallExpressions:0,eligible:false,
    registry_factory_candidate:false,
    unresolved_computed_registry_key:!!unresolvedComputedKey});continue;
  }
  const requireParam=fn.params?.[2];
  const requireName=requireParam?.type==="Identifier"?requireParam.name:null;
  const exportName=fn.params?.[1]?.type==="Identifier"?fn.params[1].name:null;
  const moduleName=fn.params?.[0]?.type==="Identifier"?fn.params[0].name:null;
  const signatures=scanModuleSignatures(fn,requireName,exportName,moduleName);
  const scopeCalls=scanScopedModuleCalls(fn,requireName);
  const {imports,boundImports}=scopeCalls;
  result.push({identifier,domain,sourceOrdinal,moduleOrdinal:i+1,
    literalCallExpressions:scopeCalls.literalCallCount,
    nestedLiteralCallExpressions:scopeCalls.nestedLiteralCallCount,
    imports:[...imports],
    directImports:[...scopeCalls.directImports],
    nestedImports:[...scopeCalls.nestedImports],
    boundImports:[...boundImports],
    eligible:!!requireName,registry_factory_candidate:true,
    unresolved_computed_registry_key:!!unresolvedComputedKey,
    exportedSlots:signatures.exportedSlots,
    directFunctionExports:signatures.directFunctionExports,
    requiredByImport:signatures.requiredByImport,
    dynamic_syntax:dynamicSyntax(fn,requireName,scopeCalls)});
 }
 return result;
}
function buildGraph(all,scanned,parseFailures,bootstrap=[]){
 if(all.length>MAX_MODULES)throw Error("Too many modules");
 const index=new Map(),globalKeyCounts=new Map();
 for(const x of all){
  if(!x.identifier||x.registry_factory_candidate===false)continue;
  globalKeyCounts.set(x.identifier,(globalKeyCounts.get(x.identifier)||0)+1);
  const domain=x.domain||"unscoped";
  if(!index.has(domain))index.set(domain,new Map());
  if(!index.get(domain).has(x.identifier))index.get(domain).set(x.identifier,[]);
  index.get(domain).get(x.identifier).push(x);
 }
 const resolve=(domain,key)=>index.get(domain||"unscoped")?.get(key)||[];
 const links=[],shapeCandidates=[],boundCandidates=[],foreignRegistryCollisions=[],
  unresolvedSites=[];
 const directFunctionSites=[];
 const literalCallSiteCounts=[];
 for(const item of all){
  if((item.literalCallExpressions||0)>0){
   literalCallSiteCounts.push({
    source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
    module_ordinal:item.moduleOrdinal,
    literal_call_expressions:item.literalCallExpressions,
    nested_function_literal_call_expressions:item.nestedLiteralCallExpressions||0,
    distinct_literal_targets:item.imports.length,
    classification:"static_literal_loader_calls",
    runtime_invocation_verified:false
   });
  }
 }
 for(const item of all){
  for(const [i,classification] of (item.directFunctionExports||[]).entries()){
   assertCandidateCapacity(directFunctionSites.length+1);
   directFunctionSites.push({
    source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
    module_ordinal:item.moduleOrdinal,
    export_function_ordinal:i+1,
    classification,
    runtime_invocation_verified:false
   });
  }
 }
 for(const item of all){
  for(const key of item.boundImports||[]){
   const matches=resolve(item.domain,key);
   assertCandidateCapacity(boundCandidates.length+1);
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
 const dynamicBoundaries=[];
 for(const item of all){
  for(const pattern of item.dynamic_syntax||[]){
   assertCandidateCapacity(dynamicBoundaries.length+1);
   dynamicBoundaries.push({
    source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
    module_ordinal:item.moduleOrdinal,pattern,
    classification:"unresolved_dynamic_boundary",
    target_module_verified:false
   });
  }
 }
 dynamicBoundaries.sort((a,b)=>a.source_ref.localeCompare(b.source_ref)||
  a.module_ordinal-b.module_ordinal||a.pattern.localeCompare(b.pattern));
 const bootstrapCandidates=[];
 for(const candidate of bootstrap){
  assertCandidateCapacity(bootstrapCandidates.length+1);
  const matches=resolve(candidate.domain||"unscoped",candidate.key);
  bootstrapCandidates.push({
   callsite_ref:"R-JS-"+String(candidate.sourceOrdinal).padStart(3,"0"),
   bootstrap_kind:candidate.bootstrap_kind||"top_level_literal_call_candidate",
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
   const matches=resolve(item.domain,id);
   if(!matches.length){
    unresolved++;
    unresolvedSites.push({
     source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
     module_ordinal:item.moduleOrdinal,
     factory_body_syntax_present:(item.directImports||[]).includes(id),
     nested_function_syntax_present:(item.nestedImports||[]).includes(id),
     classification:"missing_saved_target",
     definition_candidates:0,import_resolved:false
    });
    const foreignCount=globalKeyCounts.get(id)||0;
    if(foreignCount){
     foreignRegistryCollisions.push({
      source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
      module_ordinal:item.moduleOrdinal,
      foreign_registry_definition_count:foreignCount,
      classification:"foreign_registry_key_collision",
      import_resolved:false
     });
    }
    continue;
   }
   if(matches.length!==1){
    ambiguous++;
    unresolvedSites.push({
     source_ref:"R-JS-"+String(item.sourceOrdinal).padStart(3,"0"),
     module_ordinal:item.moduleOrdinal,
     factory_body_syntax_present:(item.directImports||[]).includes(id),
     nested_function_syntax_present:(item.nestedImports||[]).includes(id),
     classification:"ambiguous_same_registry_target",
     definition_candidates:matches.length,import_resolved:false
    });
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
    factory_body_syntax_present:(item.directImports||[]).includes(id),
    nested_function_syntax_present:(item.nestedImports||[]).includes(id),
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
  registry_runtime_scope_count:index.size,
  chunk_runtime_isolation_applied:true,
  foreign_registry_key_collision_count:foreignRegistryCollisions.length,
  foreign_registry_key_collisions:foreignRegistryCollisions,
  unresolved_import_sites:unresolvedSites,
  unresolved_import_site_count:unresolvedSites.length,
  direct_function_export_site_count:directFunctionSites.length,
  direct_function_export_sites:directFunctionSites,
  bootstrap_call_candidates:bootstrapCandidates.length,
  bootstrap_candidates:bootstrapCandidates,
  bootstrap_runtime_verified:false,
  dynamic_boundary_candidates:dynamicBoundaries,
  dynamic_boundary_count:dynamicBoundaries.length,
  dynamic_boundary_vocabulary:DYNAMIC_LABELS,
  bound_import_candidates:boundCandidates,
  bound_import_candidate_count:boundCandidates.length,
  modules_total:all.length,
  registry_nonfactory_entry_count:
   all.filter(item=>item.registry_factory_candidate===false).length,
  registry_unresolved_computed_key_count:
   all.filter(item=>item.unresolved_computed_registry_key).length,
  modules_with_import_parameter:all.filter(x=>x.eligible).length,
  import_candidates:candidateCalls,unique_resolved_links:links.length,
  nested_only_resolved_link_count:links.filter(x=>
    x.nested_function_syntax_present&&!x.factory_body_syntax_present).length,
  literal_module_loader_call_expression_count:
    literalCallSiteCounts.reduce((n,item)=>n+item.literal_call_expressions,0),
  literal_module_loader_call_site_counts:literalCallSiteCounts,
  nested_function_literal_module_loader_call_expression_count:
    literalCallSiteCounts.reduce((n,item)=>
      n+item.nested_function_literal_call_expressions,0),
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
   "A chunk runtime callback containing a direct literal require call may be discovered, but chunk registration never proves callback execution.",
   "Literal loader-call expression counts include repeated syntax, while import_candidates counts distinct keys per module.",
   "Nested-function literal loader-call syntax is counted separately; the same source may still execute immediately through an invocation.",
   "An import key occurring only inside a nested function is tagged separately from a key used in the factory body; neither presence is runtime execution evidence.",
   "Static require calls may be conditional, dead, or nested in inactive closures.",
   "A resolved bundled module reference is not proof that a module loaded or ran.",
   "Duplicate module-key candidates are deliberately ambiguous and excluded from resolved links.",
   "Export-shape matches are candidate disambiguations only; minified alias shadowing or dead code can create misleading required slots.",
   "Export-shape candidates do not change unique/ambiguous import counts and require independent source inspection before promotion.",
   "Dynamic imports, computed require arguments and bundler chunk-loader calls are unresolved syntax boundaries, never resolved import edges.",
   "Function-bound module-loader callbacks are future-import candidates, not direct calls or verified loads.",
   "Named webpackChunk registrations are linked only within the same in-memory chunk namespace; namespaces are never published.",
   "Standalone __webpack_modules__ declarations have unknown runtime identity and share an unscoped provisional group.",
   "Foreign registry key collisions are unresolved diagnostics only and do not establish any imported target.",
   "Unresolved import site ordinals are source-review leads; neither missing nor ambiguous candidate calls are verified at runtime.",
   "Registry entries with computed nonliteral keys remain anonymous factories and are not resolved by identifier spelling.",
   "Registry object entries without callable function factories are counted but excluded as resolvable targets.",
   "Only literal require arguments are considered; dynamic module keys are unresolved.",
   "Direct functions on export objects or module.exports assignments are source syntax candidates; getter and alias ownership remain unresolved.",
   "No private module keys, source bytes, URLs, filenames or account data are emitted."
  ]
 };
}
function scan(directory){
 const entries=fs.readdirSync(directory).filter(x=>/^bundle-[0-9]{3,4}\.js$/.test(x)).sort();
 if(entries.length>MAX_FILES)throw Error("Too many bundles");
 let parsed=0,failed=0;
 const failedOrdinals=[],noModuleOrdinals=[],modules=[],bootstrap=[];
 for(const entry of entries){
  const full=path.join(directory,entry),stat=fs.lstatSync(full);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error("Unsupported file");
  const ordinal=Number(entry.match(/^bundle-([0-9]+)\.js$/)[1]);
  if(stat.size>8*1024*1024){failed++;failedOrdinals.push(ordinal);continue;}
  try{
   const report=analyzeJS(fs.readFileSync(full,"utf8"),ordinal);
   if(report.length===0)noModuleOrdinals.push(ordinal);
   modules.push(...report);
   bootstrap.push(...report.bootstrapCandidates);
   parsed++;
  }
  catch(_){failed++;failedOrdinals.push(ordinal);}
 }
 const report=buildGraph(modules,parsed,failed,bootstrap);
 report.failed_parser_source_refs=failedOrdinals.map(id=>
   "R-JS-"+String(id).padStart(3,"0"));
 report.parsed_without_indexed_module_count=noModuleOrdinals.length;
 report.parsed_without_indexed_module_refs=noModuleOrdinals.map(id=>
   "R-JS-"+String(id).padStart(3,"0"));
 return report;
}
function selfTest(){
 assert.doesNotThrow(()=>assertCandidateCapacity(MAX_CANDIDATES));
 assert.throws(()=>assertCandidateCapacity(MAX_CANDIDATES+1));
 assert.throws(()=>assertCandidateCapacity(-1));
 const s1="export const __webpack_modules__={A:(function(e,t,n){const b=n('B');t.a=()=>b.a}),B:(function(e,t,n){t.a=()=>1})};";
 const s2="export const __webpack_modules__={C:(function(e,t,n){const a=n('A');const missing=n('External');t.a=a})};";
 const a=[...analyzeJS(s1,1),...analyzeJS(s2,2)];
 const o=buildGraph(a,2,0);
 assert.equal(o.modules_total,3);
 assert.equal(o.import_candidates,3);
 assert.equal(o.unique_resolved_links,2);
 assert.equal(o.unresolved_import_candidates,1);
 assert.equal(o.unresolved_import_site_count,1);
 assert.equal(o.unresolved_import_sites[0].classification,"missing_saved_target");
 assert.equal(o.unresolved_import_sites[0].module_ordinal,1);
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
 assert.deepEqual(new Set(dynamicReport.dynamic_boundary_candidates.map(x=>x.pattern)),new Set(DYNAMIC_LABELS.slice(0,3)));
 assert(!JSON.stringify(dynamicReport).includes("private-module"));
 assert(!JSON.stringify(dynamicReport).includes("private-chunk"));
 const computed=analyzeJS("export const __webpack_modules__={"+
   "A:(function(e,t,n){const lazy=n(t.privateDynamicKey);"+
   "function unrelated(n){n(t.otherKey);n.e('shadowed')}})};",10);
 const computedOutput=buildGraph(computed,1,0);
 assert.equal(computedOutput.import_candidates,0);
 assert.equal(computedOutput.dynamic_boundary_count,1);
 assert.equal(computedOutput.dynamic_boundary_candidates[0].pattern,
    "computed_module_require_candidate");
 assert(!JSON.stringify(computedOutput).includes("privateDynamicKey"));
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
 const scopedExport="export const __webpack_modules__={"+
  "Caller:(function(e,t,n){const x=n('Q');x.h()}),"+
  "Q:(function(e,t,n){function fake(t){t.h=1;}t.x=1})};";
 const otherExport="export const __webpack_modules__={Q:(function(e,t,n){t.y=1})};";
 const scopedOutput=buildGraph([...analyzeJS(scopedExport,1),
   ...analyzeJS(otherExport,2)],2,0);
 assert.equal(scopedOutput.ambiguous_import_candidates,1);
 assert.equal(scopedOutput.export_shape_candidate_count,0);
 const trueExport="export const __webpack_modules__={"+
  "Caller:(function(e,t,n){const x=n('Q');x.h()}),"+
  "Q:(function(e,t,n){t.h=()=>1})};";
 const trueOutput=buildGraph([...analyzeJS(trueExport,1),
   ...analyzeJS(otherExport,2)],2,0);
 assert.equal(trueOutput.export_shape_candidate_count,1);
 const computedExport="export const __webpack_modules__={"+
  "Caller:(function(e,t,n){const x=n('Q');x.h()}),"+
  "Q:(function(e,t,n){n.d(t,{[someRuntimeValue]:()=>1})})};";
 assert.equal(buildGraph([...analyzeJS(computedExport,1),
   ...analyzeJS(otherExport,2)],2,0).export_shape_candidate_count,0);
 const numericSource=analyzeJS("export const __webpack_modules__={"+
  "871997334455:(function(e,t,n){const x=n(871997334456);const later=n.bind(n,871997334456)}),"+
  "871997334456:(function(e,t,n){t.a=1})};"+
  "__webpack_require__(871997334455);",12);
 const numericGraph=buildGraph(numericSource,1,0,numericSource.bootstrapCandidates);
 assert.equal(numericGraph.unique_resolved_links,1);
 assert.equal(numericGraph.bootstrap_candidates[0].classification,"unique_registry_key_candidate");
 assert.equal(numericGraph.bound_import_candidate_count,1);
 assert.equal(numericGraph.dynamic_boundary_count,0);
 assert(!JSON.stringify(numericGraph).includes("871997334455"));
 assert(!JSON.stringify(numericGraph).includes("871997334456"));
 const plainVar=analyzeJS("var __webpack_modules__={"+
  "A:function(e,t,n){t.a=n('B')},B:function(e,t,n){t.a=1}};",13);
 assert.equal(plainVar.length,2);
 assert.equal(buildGraph(plainVar,1,0).unique_resolved_links,1);
 const chunkScript="(self['webpackChunkPrivateScope']=self['webpackChunkPrivateScope']||[]).push("+
  "[[73],{9001:function(e,t,n){const x=n(9002)},9002:function(e,t,n){t.a=1}}]);";
 const chunkModules=analyzeJS(chunkScript,14);
 const chunkReport=buildGraph(chunkModules,1,0);
 assert.equal(chunkReport.modules_total,2);
 assert.equal(chunkReport.unique_resolved_links,1);
 assert(!JSON.stringify(chunkReport).includes("webpackChunkPrivateScope"));
 const unrecognized=analyzeJS("self.notWebpackChunk.push([[73],"+
  "{9001:function(e,t,n){t.a=1}}]);",14);
 assert.equal(unrecognized.length,0);
 const isolatedA="(self.webpackChunkPrivateAlpha=self.webpackChunkPrivateAlpha||[]).push("+
   "[[1],{100:function(e,t,n){const x=n(200)},200:function(e,t,n){t.a=1}}]);";
 const isolatedB="(window.webpackChunkPrivateBeta=window.webpackChunkPrivateBeta||[]).push("+
   "[[2],{200:function(e,t,n){t.b=1},300:function(e,t,n){const x=n(100)}}]);";
 const isolatedC="(globalThis.webpackChunkPrivateAlpha=globalThis.webpackChunkPrivateAlpha||[]).push("+
   "[[3],{400:function(e,t,n){const x=n(200)}}]);";
 const isolated=buildGraph([...analyzeJS(isolatedA,14),
  ...analyzeJS(isolatedB,15),...analyzeJS(isolatedC,16)],3,0);
 assert.equal(isolated.modules_total,5);
 assert.equal(isolated.registry_runtime_scope_count,2);
 assert.equal(isolated.import_candidates,3);
 assert.equal(isolated.unique_resolved_links,2);
 assert.equal(isolated.unresolved_import_candidates,1);
 assert.equal(isolated.ambiguous_import_candidates,0);
 assert.equal(isolated.cross_bundle_links,1);
 assert.equal(isolated.foreign_registry_key_collision_count,1);
 assert.equal(isolated.foreign_registry_key_collisions[0].classification,
   "foreign_registry_key_collision");
 assert.equal(isolated.foreign_registry_key_collisions[0].import_resolved,false);
 assert(!JSON.stringify(isolated).includes("webpackChunkPrivateAlpha"));
 assert(!JSON.stringify(isolated).includes("webpackChunkPrivateBeta"));
 const catchSource=analyzeJS("export const __webpack_modules__={"+
  "Reader:(function(e,t,n){try{throw 1}catch(n){n('Ghost')}"+
  "const imported=n('Collision');"+
  "try{throw 1}catch(imported){imported.h()} }),"+
  "Collision:(function(e,t,n){try{throw 1}catch(t){t.h=1}})};",21);
 const catchDuplicate=analyzeJS("export const __webpack_modules__={"+
  "Collision:(function(e,t,n){t.x=1})};",22);
 const catchGraph=buildGraph([...catchSource,...catchDuplicate],2,0);
 assert.equal(catchGraph.import_candidates,1);
 assert.equal(catchGraph.ambiguous_import_candidates,1);
 assert.equal(catchGraph.export_shape_candidate_count,0);
 assert(!JSON.stringify(catchGraph).includes("Ghost"));
 const chunkRuntimeSource="(self.webpackChunkPrivateRuntime=self.webpackChunkPrivateRuntime||[]).push("+
  "[[41],{901:function(e,t,n){const b=n(902)},902:function(e,t,n){t.a=1}},function(n){n(901)}]);";
 const chunkRuntimeAnalyzed=analyzeJS(chunkRuntimeSource,23);
 const runtimeGraph=buildGraph(chunkRuntimeAnalyzed,1,0,
   chunkRuntimeAnalyzed.bootstrapCandidates);
 assert.equal(runtimeGraph.bootstrap_call_candidates,1);
 assert.equal(runtimeGraph.bootstrap_candidates[0].bootstrap_kind,
   "chunk_runtime_literal_call_candidate");
 assert.equal(runtimeGraph.bootstrap_candidates[0].classification,
   "unique_registry_key_candidate");
 assert.equal(runtimeGraph.bootstrap_candidates[0].target_module,1);
 assert.equal(runtimeGraph.bootstrap_candidates[0].bootstrap_execution_verified,false);
 assert.equal(runtimeGraph.unique_resolved_links,1);
 assert(!JSON.stringify(runtimeGraph).includes("webpackChunkPrivateRuntime"));
 const deferredRuntime=analyzeJS("(self.webpackChunkDeferred=self.webpackChunkDeferred||[]).push("+
  "[[51],{901:function(e,t,n){t.a=1}},function(n){const unused=()=>n(901)}]);",24);
 assert.equal(deferredRuntime.bootstrapCandidates.length,0);
 const loopScopes=analyzeJS("export const __webpack_modules__={"+
  "Consumer:(function(e,t,n){const a=n('Q');"+
  "for(let a of [{z:()=>1}]){a.z()}a.x();"+
  "for(let n of [()=>1]){n('Unrelated')}"+
  "switch(1){case 1:{const n=()=>1;n('Unrelated')}break}"+
  "switch(1){case 1:const a={z:()=>1};a.z();break}"+
  "}),Q:(function(e,t,n){t.x=1})};",36);
 const loopGraph=buildGraph(loopScopes,1,0);
 assert.equal(loopGraph.import_candidates,1);
 assert.equal(loopGraph.unique_resolved_links,1);
 assert(!JSON.stringify(loopGraph).includes("Unrelated"));
 const owners=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){t.PrivateExportFunctionZ941=function(){return 1};t.stop=()=>2;"+
  "function local(t){t.fake=()=>3}n.d(t,{getter:()=>local})}),"+
  "B:(function(e,t,n){t.data=17})};",37);
 const ownerGraph=buildGraph(owners,1,0);
 assert.equal(ownerGraph.direct_function_export_site_count,2);
 assert.equal(ownerGraph.direct_function_export_sites[0].module_ordinal,1);
 assert.equal(ownerGraph.direct_function_export_sites[1].export_function_ordinal,2);
 assert(ownerGraph.direct_function_export_sites.every(site=>!site.runtime_invocation_verified));
 assert(!JSON.stringify(ownerGraph).includes("fake"));
 assert(!JSON.stringify(ownerGraph).includes("PrivateExportFunctionZ941"));
 const reboundRuntime=analyzeJS("(self.webpackChunkRebound=self.webpackChunkRebound||[]).push("+
  "[[61],{901:function(e,t,n){t.a=1}},function(n){"+
  "if(Math.random())n=()=>1;n(901)}]);",25);
 assert.equal(reboundRuntime.bootstrapCandidates.length,0);
 const directBeforeRebind=analyzeJS("(self.webpackChunkDirectFirst=self.webpackChunkDirectFirst||[]).push("+
  "[[62],{901:function(e,t,n){t.a=1}},function(n){"+
  "n(901);n=()=>1;n(901)}]);",26);
 assert.equal(directBeforeRebind.bootstrapCandidates.length,1);
 const commonjsOwners=analyzeJS("export const __webpack_modules__={"+
  "A:(function(module,exports,require){module.exports=function(){return 1};"+
  "function PrivateShadowFnZ937(module){module.exports=()=>99}}),"+
  "B:(function(module,exports,require){exports.fn=()=>2})};",38);
 const commonjsGraph=buildGraph(commonjsOwners,1,0);
 assert.equal(commonjsGraph.direct_function_export_site_count,2);
 assert.deepEqual(commonjsGraph.direct_function_export_sites.map(x=>x.classification),
  ["module_object_function_assignment_candidate",
   "direct_function_export_assignment_candidate"]);
 assert(!JSON.stringify(commonjsGraph).includes("PrivateShadowFnZ937"));
 const repeated=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){n('B');n('B');const a=n('C')}),"+
  "B:(function(e,t,n){t.a=1}),C:(function(e,t,n){t.c=1})};",39);
 const repeatedGraph=buildGraph(repeated,1,0);
 assert.equal(repeatedGraph.import_candidates,2);
 assert.equal(repeatedGraph.literal_module_loader_call_expression_count,3);
 assert.equal(repeatedGraph.literal_module_loader_call_site_counts[0].distinct_literal_targets,2);
 assert(!JSON.stringify(repeatedGraph).includes("'B'"));
 const possibleMutation=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){if(t.choice){n=()=>1}n('B');"+
  "const candidate=n('C');if(t.choice){candidate={p:1}}candidate.x();"+
  "if(t.choice){t={}}t.m=()=>1}),"+
  "B:(function(e,t,n){t.b=1}),C:(function(e,t,n){t.c=1})};",40);
 const mutationResult=buildGraph(possibleMutation,1,0);
 assert.equal(mutationResult.import_candidates,0);
 assert.equal(mutationResult.direct_function_export_site_count,0);
 const localShadow=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){if(t.choice){const n=()=>1;n('X')}"+
  "const candidate=n('B');if(t.choice){const candidate={p:1};candidate.p}"+
  "candidate.x();if(t.choice){const t={};t.m=()=>1}t.good=()=>1}),"+
  "B:(function(e,t,n){t.b=1})};",41);
 const localShadowGraph=buildGraph(localShadow,1,0);
 assert.equal(localShadowGraph.import_candidates,1);
 assert.equal(localShadowGraph.unique_resolved_links,1);
 assert.equal(localShadowGraph.direct_function_export_site_count,1);
 assert(!JSON.stringify(localShadowGraph).includes("'X'"));
 const nonfactory=analyzeJS("export const __webpack_modules__={"+
  "Caller:(function(e,t,n){const a=n('Bare');const b=n('TwoParam')}),"+
  "Bare:42,TwoParam:(function(e,t){t.a=1})};",42);
 const nonfactoryGraph=buildGraph(nonfactory,1,0);
 assert.equal(nonfactoryGraph.registry_nonfactory_entry_count,1);
 assert.equal(nonfactoryGraph.modules_total,3);
 assert.equal(nonfactoryGraph.import_candidates,2);
 assert.equal(nonfactoryGraph.unique_resolved_links,1);
 assert.equal(nonfactoryGraph.unresolved_import_candidates,1);
 assert.equal(nonfactoryGraph.resolved_links[0].to_module,3);
 const writesOnly=analyzeJS("export const __webpack_modules__={"+
  "Reader:(function(e,t,n){const x=n('Q');x.foo=1;x.foo++;"+
  "delete x.foo;for(x.foo of [1]){};({p:x.foo}={p:2})}),"+
  "Q:(function(e,t,n){t.foo=1})};",43);
 const otherQ=analyzeJS("export const __webpack_modules__={"+
  "Q:(function(e,t,n){t.bar=1})};",44);
 const writeOnlyGraph=buildGraph([...writesOnly,...otherQ],2,0);
 assert.equal(writeOnlyGraph.ambiguous_import_candidates,1);
 assert.equal(writeOnlyGraph.export_shape_candidate_count,0);
 const readOnly=analyzeJS("export const __webpack_modules__={"+
  "Reader:(function(e,t,n){const x=n('Q');x.foo()}),"+
  "Q:(function(e,t,n){t.foo=()=>1})};",45);
 const readGraph=buildGraph([...readOnly,...otherQ],2,0);
 assert.equal(readGraph.export_shape_candidate_count,1);
 const computedTable=analyzeJS("export const __webpack_modules__={"+
  "Consumer:(function(e,t,n){n('HiddenDynamicKey');n(987654321)}),"+
  "[HiddenDynamicKey]:(function(e,t,n){n(987654321)}),"+
  "[987654321]:(function(e,t){t.a=1})};",46);
 const computedResult=buildGraph(computedTable,1,0);
 assert.equal(computedResult.registry_unresolved_computed_key_count,1);
 assert.equal(computedResult.registry_nonfactory_entry_count,0);
 assert.equal(computedResult.modules_total,3);
 assert.equal(computedResult.unique_resolved_links,2);
 assert.equal(computedResult.unresolved_import_candidates,1);
 assert(!JSON.stringify(computedResult).includes("HiddenDynamicKey"));
 const nestedCount=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){n('B');function later(){n('B');n('B')}"+
  "function hidden(n){n('PrivateNested')}const arrow=()=>n('B')}),"+
  "B:(function(e,t,n){t.a=1})};",47);
 const nestedReport=buildGraph(nestedCount,1,0);
 assert.equal(nestedReport.literal_module_loader_call_expression_count,4);
 assert.equal(nestedReport.nested_function_literal_module_loader_call_expression_count,3);
 assert.equal(nestedReport.import_candidates,1);
 assert(!JSON.stringify(nestedReport).includes("PrivateNested"));
 const branchModes=analyzeJS("export const __webpack_modules__={"+
  "Loop:(function(e,t,n){for(let i=0;i<1;i++){n=()=>1}n('Goal')}),"+
  "Switch:(function(e,t,n){switch(t.flag){case 1:n=()=>1;break}n('Goal')}),"+
  "Catch:(function(e,t,n){try{throw 1}catch(e){n=()=>1}n('Goal')}),"+
  "Shadow:(function(e,t,n){for(let n of [()=>1]){n('PrivateShadowed')}"+
  "try{throw 1}catch(n){n('PrivateCaught')}n('Goal')}),"+
  "Goal:(function(e,t){t.a=1})};",48);
 const branchResult=buildGraph(branchModes,1,0);
 assert.equal(branchResult.import_candidates,1);
 assert.equal(branchResult.unique_resolved_links,1);
 assert.equal(branchResult.resolved_links[0].from_module,4);
 assert.equal(branchResult.resolved_links[0].to_module,5);
 assert(!JSON.stringify(branchResult).includes("PrivateCaught"));
 const locallyShadowedRuntime=analyzeJS(""+
  "(self.webpackChunkLocalShadow=self.webpackChunkLocalShadow||[]).push("+
  "[[81],{901:function(e,t,n){t.a=1}},function(n){"+
  "if(true){const n=()=>1;n(999)}n(901)}]);",49);
 assert.equal(locallyShadowedRuntime.bootstrapCandidates.length,1);
 const varRuntime=analyzeJS(""+
  "(self.webpackChunkVarRebind=self.webpackChunkVarRebind||[]).push("+
  "[[82],{901:function(e,t,n){t.a=1}},function(n){"+
  "if(true){var n=()=>1}n(901)}]);",50);
 assert.equal(varRuntime.bootstrapCandidates.length,0);
 const varScoped=analyzeJS("export const __webpack_modules__={"+
  "Assigned:(function(e,t,n){if(t.flag){var n=()=>1}n('Target')}),"+
  "Redeclared:(function(e,t,n){if(t.flag){var n}n('Target')}),"+
  "Iterated:(function(e,t,n){for(var n of [()=>1]){}n('Target')}),"+
  "Target:(function(e,t){t.a=1})};",59);
 const varReport=buildGraph(varScoped,1,0);
 assert.equal(varReport.import_candidates,1);
 assert.equal(varReport.unique_resolved_links,1);
 assert.equal(varReport.resolved_links[0].from_module,2);
 const nestedHoist=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){function other(){n('B');if(false){var n}}}),"+
  "B:(function(e,t){t.a=1})};",60);
 assert.equal(buildGraph(nestedHoist,1,0).import_candidates,0);
 const iteratedRuntime=analyzeJS(""+
  "(self.webpackChunkVarIteration=self.webpackChunkVarIteration||[]).push("+
  "[[91],{901:function(e,t,n){t.a=1}},function(n){"+
  "for(var n of [()=>1]){}n(901)}]);",61);
 assert.equal(iteratedRuntime.bootstrapCandidates.length,0);
 const destructuredRuntime=analyzeJS(""+
  "(self.webpackChunkDestructure=self.webpackChunkDestructure||[]).push("+
  "[[92],{901:function(e,t,n){t.a=1}},function(n){"+
  "({loader:n}={loader:()=>1});n(901)}]);",62);
 assert.equal(destructuredRuntime.bootstrapCandidates.length,0);
 const lexicalRuntime=analyzeJS(""+
  "(self.webpackChunkLexicalIteration=self.webpackChunkLexicalIteration||[]).push("+
  "[[93],{901:function(e,t,n){t.a=1}},function(n){"+
  "for(let n of [()=>1]){}n(901)}]);",63);
 assert.equal(lexicalRuntime.bootstrapCandidates.length,1);
 const invokedMutator=analyzeJS(""+
  "(self.webpackChunkInvokedMutator=self.webpackChunkInvokedMutator||[]).push("+
  "[[101],{901:function(e,t,n){t.a=1}},function(n){"+
  "(()=>{n=()=>1})();n(901)}]);",64);
 assert.equal(invokedMutator.bootstrapCandidates.length,0);
 const invokedShadow=analyzeJS(""+
  "(self.webpackChunkInvokedShadow=self.webpackChunkInvokedShadow||[]).push("+
  "[[102],{901:function(e,t,n){t.a=1}},function(n){"+
  "((n)=>{n=()=>1})(()=>1);n(901)}]);",65);
 assert.equal(invokedShadow.bootstrapCandidates.length,1);
 const unusedMutator=analyzeJS(""+
  "(self.webpackChunkDeferredMutator=self.webpackChunkDeferredMutator||[]).push("+
  "[[103],{901:function(e,t,n){t.a=1}},function(n){"+
  "const deferred=()=>{n=()=>1};n(901)}]);",66);
 assert.equal(unusedMutator.bootstrapCandidates.length,1);
 const replacedExport=analyzeJS("export const __webpack_modules__={"+
  "Caller:(function(e,t,n){const x=n('Z');x.obsolete()}),"+
  "Z:(function(e,t,n){t.obsolete=()=>1;e.exports=function(){return 1};"+
  "t.later=()=>2})};",67);
 const duplicateReplacement=analyzeJS("export const __webpack_modules__={"+
  "Z:(function(e,t,n){t.alternate=()=>3})};",68);
 const replacedGraph=buildGraph([...replacedExport,...duplicateReplacement],2,0);
 assert.equal(replacedGraph.ambiguous_import_candidates,1);
 assert.equal(replacedGraph.export_shape_candidate_count,0);
 assert.equal(replacedGraph.direct_function_export_site_count,2);
 assert.equal(replacedGraph.direct_function_export_sites[0].classification,
  "module_object_function_assignment_candidate");
 assert(!JSON.stringify(replacedGraph).includes("obsolete"));
 const beforeOnly=analyzeJS("export const __webpack_modules__={"+
  "A:(function(e,t,n){t.before=()=>1;e.exports={replaced:1};t.after=()=>2})};",69);
 assert.equal(buildGraph(beforeOnly,1,0).direct_function_export_site_count,0);
 const shadowedBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};{const __webpack_require__=()=>0;"+
  "__webpack_require__('A')};",70);
 assert.equal(shadowedBoot.bootstrapCandidates.length,0);
 const reassignedBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};if(flag){__webpack_require__=()=>0}"+
  "__webpack_require__('A');",71);
 assert.equal(reassignedBoot.bootstrapCandidates.length,0);
 const iifeShadowedBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};((__webpack_require__)=>"+
  "__webpack_require__('A'))(()=>0);",72);
 assert.equal(iifeShadowedBoot.bootstrapCandidates.length,0);
 const validIifeBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};(()=>__webpack_require__('A'))();",73);
 assert.equal(validIifeBoot.bootstrapCandidates.length,1);
 const mutatedIifeBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};(()=>{__webpack_require__=()=>0})();"+
  "__webpack_require__('A');",74);
 assert.equal(mutatedIifeBoot.bootstrapCandidates.length,0);
 const deferredBoot=analyzeJS("export const __webpack_modules__={"+
  "A:function(){}};const later=()=>__webpack_require__('A');",75);
 assert.equal(deferredBoot.bootstrapCandidates.length,0);
 const moduleProperties=analyzeJS("export const __webpack_modules__={"+
  "Caller:(function(m,t,n){const q=n('Q');q.fn()}),"+
  "Q:(function(m,t,n){m.exports.fn=function(){return 1};"+
  "function shadow(m){m.exports.PrivateShadowOwnerZ990=()=>1}})};",76);
 const alternativeModule=analyzeJS("export const __webpack_modules__={"+
  "Q:(function(m,t,n){t.other=()=>2})};",77);
 const modulePropertyGraph=buildGraph([...moduleProperties,...alternativeModule],2,0);
 assert.equal(modulePropertyGraph.ambiguous_import_candidates,1);
 assert.equal(modulePropertyGraph.export_shape_candidate_count,1);
 assert.equal(modulePropertyGraph.direct_function_export_site_count,2);
 assert.equal(modulePropertyGraph.direct_function_export_sites[0].classification,
  "module_exports_property_function_candidate");
 assert(!JSON.stringify(modulePropertyGraph).includes("PrivateShadowOwnerZ990"));
 const replacedProperty=analyzeJS("export const __webpack_modules__={"+
  "Q:(function(m,t,n){t.old=()=>1;m.exports={};m.exports.newer=()=>2})};",78);
 const replacedPropertyGraph=buildGraph(replacedProperty,1,0);
 assert.equal(replacedPropertyGraph.direct_function_export_site_count,1);
 assert.equal(replacedPropertyGraph.direct_function_export_sites[0].classification,
  "module_exports_property_function_candidate");
 const contextExample=analyzeJS("export const __webpack_modules__={"+
  "Entry:(function(e,t,n){n('Body');"+
  "const fn=()=>{n('Later');n('Body')}}),"+
  "Body:(function(e,t,n){t.a=1}),Later:(function(e,t,n){t.b=1})};",79);
 const contextGraph=buildGraph(contextExample,1,0);
 assert.equal(contextGraph.unique_resolved_links,2);
 assert.equal(contextGraph.nested_only_resolved_link_count,1);
 const byDestination=new Map(contextGraph.resolved_links.map(x=>[x.to_module,x]));
 assert.equal(byDestination.get(2).factory_body_syntax_present,true);
 assert.equal(byDestination.get(2).nested_function_syntax_present,true);
 assert.equal(byDestination.get(3).factory_body_syntax_present,false);
 assert.equal(byDestination.get(3).nested_function_syntax_present,true);
 const assignmentTargets=analyzeJS("export const __webpack_modules__={"+
  "Loader:(function(e,t,n){({next:n}={next:()=>1});n('Unused')}),"+
  "Iteration:(function(e,t,n){for(n of [()=>1]){}n('Unused')}),"+
  "Exported:(function(e,t,n){({next:t}={next:{}});t.handler=()=>1}),"+
  "Alias:(function(e,t,n){let a=n('Target');"+
  "for(a of [{foo:1}]){}a.foo()}),"+
  "Target:(function(e,t,n){t.foo=()=>1})};",80);
 const assignmentGraph=buildGraph(assignmentTargets,1,0);
 assert.equal(assignmentGraph.import_candidates,1);
 assert.equal(assignmentGraph.unique_resolved_links,1);
 assert.equal(assignmentGraph.direct_function_export_site_count,1);
 assert(!JSON.stringify(assignmentGraph).includes("Unused"));
 const updatedBindings=analyzeJS("export const __webpack_modules__={"+
  "Loader:(function(e,t,n){n++;n('Fake')}),"+
  "Export:(function(e,t,n){t++;t.fake=()=>1}),"+
  "Alias:(function(e,t,n){let a=n('Target');a++;a.ok()}),"+
  "Target:(function(e,t,n){t.ok=()=>1})};",81);
 const updateResult=buildGraph(updatedBindings,1,0);
 assert.equal(updateResult.import_candidates,1);
 assert.equal(updateResult.unique_resolved_links,1);
 assert.equal(updateResult.direct_function_export_site_count,1);
 assert(!JSON.stringify(updateResult).includes("'Fake'"));
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
