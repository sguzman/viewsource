#!/usr/bin/env node
"use strict";
/* Offline, content-free CSS and JS vocabulary census for saved web captures.
 * Counts lexical syntax, not parsed computed CSS or verified component styles.
 * Does not execute captured assets or publish filenames, source, selectors,
 * style values, route names or runtime measurements.
 */
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const MAX_FILES=2000,MAX_SIZE=8*1024*1024;
const CSS={
  media_at_rules:/@media\b/g,
  container_at_rules:/@container\b/g,
  prefers_reduced_motion_mentions:/prefers-reduced-motion/g,
  focus_visible_pseudo_classes:/:focus-visible\b/g,
  test_id_attribute_selectors:/\[data-testid\b/g,
  data_state_attribute_selectors:/\[data-state\b/g,
  role_attribute_selectors:/\[role(?:\]|[~*^$|]?=)/g,
  thread_content_vocabulary_mentions:/thread-content/g
};
const IDENT={
  data_message_id:/\[data-message-id\b/g,
  data_message_author_role:/\[data-message-author-role\b/g,
  data_source_message_ids:/\[data-source-message-ids\b/g,
  data_turn_key:/\[data-turn-key\b/g
};
const count=(s,r)=>Array.from(s.matchAll(r)).length;
function fresh(){
 return {format_version:1,source_scope:"offline_saved_stylesheets",
   evidence_status:"lexical_source_candidates",
   stylesheets_scanned:0,javascript_bundles_scanned:0,
   stylesheet_bytes:0,css_lexical_occurrences:Object.fromEntries(Object.keys(CSS).map(k=>[k,0])),
   exact_css_attribute_selectors:Object.fromEntries(Object.keys(IDENT).map(k=>[k,0])),
   cross_resource_vocabulary:{thread_content:{javascript_bundle_count:0,javascript_occurrences:0,css_occurrences:0}},
   limits:[
     "Lexical matches do not establish that a CSS rule applies to a particular DOM element.",
     "Missing literal attribute selectors do not mean the component lacks styling.",
     "CSS values, source selectors and original resource names are never output.",
     "Runtime theme, media/container branch selection and computed styles are not verified."
   ]};
}
function consumeCSS(report,text,byteSize){
 report.stylesheets_scanned++;report.stylesheet_bytes+=byteSize;
 for(const [k,rx] of Object.entries(CSS))report.css_lexical_occurrences[k]+=count(text,rx);
 for(const [k,rx] of Object.entries(IDENT))report.exact_css_attribute_selectors[k]+=count(text,rx);
 report.cross_resource_vocabulary.thread_content.css_occurrences+=count(text,/thread-content/g);
}
function consumeJS(report,text){
 report.javascript_bundles_scanned++;
 const total=count(text,/thread-content/g);
 if(total)report.cross_resource_vocabulary.thread_content.javascript_bundle_count++;
 report.cross_resource_vocabulary.thread_content.javascript_occurrences+=total;
}
function scan(directory){
 const report=fresh();
 const files=fs.readdirSync(directory).filter(x=>/^(?:style|bundle)-[0-9]{3,4}\.(?:css|js)$/.test(x)).sort();
 if(files.length>MAX_FILES)throw Error("Too many capture assets");
 for(const file of files){
   const stat=fs.lstatSync(path.join(directory,file));
   if(!stat.isFile()||stat.isSymbolicLink()||stat.size>MAX_SIZE)throw Error("Unsupported capture file");
   const text=fs.readFileSync(path.join(directory,file),"utf8");
   if(/^style-/.test(file))consumeCSS(report,text,stat.size);
   else consumeJS(report,text);
 }
 return report;
}
function selfTest(){
 const result=fresh();
 const css='@media (prefers-reduced-motion: reduce){[data-state=open]:focus-visible{opacity:1}}'+
 '@container (min-width:100px){[data-testid=x] [role=button]{color:red}}'+
 '.chat{max-width:var(--thread-content-max-width)}';
 consumeCSS(result,css,Buffer.byteLength(css));
 consumeJS(result,'const x="thread-content";const y="PRIVATE_SYNTHETIC_SENTINEL";');
 assert.equal(result.css_lexical_occurrences.media_at_rules,1);
 assert.equal(result.css_lexical_occurrences.container_at_rules,1);
 assert.equal(result.css_lexical_occurrences.prefers_reduced_motion_mentions,1);
 assert.equal(result.css_lexical_occurrences.focus_visible_pseudo_classes,1);
 assert.equal(result.css_lexical_occurrences.test_id_attribute_selectors,1);
 assert.equal(result.css_lexical_occurrences.data_state_attribute_selectors,1);
 assert.equal(result.css_lexical_occurrences.role_attribute_selectors,1);
 assert.equal(result.cross_resource_vocabulary.thread_content.javascript_bundle_count,1);
 assert.equal(result.cross_resource_vocabulary.thread_content.css_occurrences,1);
 assert(Object.values(result.exact_css_attribute_selectors).every(x=>x===0));
 assert(!JSON.stringify(result).includes("PRIVATE_SYNTHETIC_SENTINEL"));
}
if(require.main===module){
 if(process.argv.length===3&&process.argv[2]==="--self-test"){
   selfTest();process.stdout.write("Synthetic saved-stylesheet census passed\n");
 }else if(process.argv.length===3){
   try{process.stdout.write(JSON.stringify(scan(process.argv[2]),null,2)+"\n");}
   catch(_){process.stderr.write("Stylesheet candidate census failed (details suppressed)\n");process.exitCode=2;}
 }else{process.stderr.write("Usage: node scripts/trace_style_hooks.cjs <private-asset-dir>\n");process.exitCode=2;}
}
module.exports={fresh,consumeCSS,consumeJS,scan,selfTest};
