"use strict";
/* Browser UI over a published, allowlisted JSON catalogue. No capture execution. */
const $ = (id) => document.getElementById(id);
const model = { catalog: null, specimen: "", version: 0, chapter: "overview", query: "" };
const namespace = "http://www.w3.org/2000/svg";
const statusLabels = { done:"Completed", queued:"Queued", in_progress:"In progress",
  blocked:"Blocked", not_observable:"Not observable" };

function elem(tag, attrs = {}, children = []) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") el.className = value;
    else if (key === "text") el.textContent = value == null ? "" : String(value);
    else if (key === "hidden") el.hidden = Boolean(value);
    else if (key === "value") el.value = String(value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else el.setAttribute(key, String(value));
  }
  for (const child of children) {
    if (child == null) continue;
    el.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return el;
}
function append(parent, ...children) {
  for (const child of children) if (child != null) parent.append(child.nodeType ? child : document.createTextNode(String(child)));
  return parent;
}
function title(text) { return elem("h2", {text}); }
function versionRecord() {
  return model.catalog.versions.find(v=>v.specimen_id===model.specimen&&v.version===model.version);
}
function specimenRecord() { return model.catalog.specimens.find(s=>s.id===model.specimen); }
const fallbackChapters = [
  {id:"overview",name:"Overview",eyebrow:"Research introduction",title:"A snapshot of an interface",
   lead:"A static research version with verified structural observations and carefully bounded unknowns.",
   metrics:[],tags:["Saved capture"],sections:[],flow:["Document","Resources","Findings"],evidence:[]},
  {id:"evidence",name:"Evidence",eyebrow:"Research findings",title:"What this capture can support",
   lead:"The inspected source makes some architecture visible without verifying live execution.",
   metrics:[],tags:[],sections:[],flow:[],evidence:[]},
  {id:"work",name:"Research queue",eyebrow:"Research progress",title:"A versioned work record",
   lead:"Research tasks remain visible alongside evidence and limitations.",
   metrics:[],tags:[],sections:[],flow:[],evidence:[]}
];
function chapters() {
  const rec = versionRecord();
  return rec.chapters.length ? rec.chapters : fallbackChapters;
}
function chapterRecord() {
  return chapters().find(c=>c.id===model.chapter) || chapters()[0];
}
function hashSelection() {
  const p = new URLSearchParams(location.hash.replace(/^#/,""));
  return { specimen: p.get("specimen"), v: Number(p.get("v")), chapter: p.get("chapter") };
}
function setRoute(chapter, version = model.version, specimen = model.specimen) {
  model.specimen = specimen;
  model.version = version;
  model.chapter = chapter;
  model.query = "";
  $("site-search").value = "";
  location.hash = new URLSearchParams({specimen, v: String(version), chapter}).toString();
  render();
  window.scrollTo({top:0,behavior:"auto"});
}
function selectModel() {
  const selection = hashSelection();
  const candidates = model.catalog.specimens;
  model.specimen = candidates.some(s=>s.id===selection.specimen) ? selection.specimen : candidates[0].id;
  const spec = specimenRecord();
  model.version = spec.versions.includes(selection.v) ? selection.v : spec.current_version;
  const valid = model.catalog.versions.find(v=>v.specimen_id===model.specimen&&v.version===model.version);
  model.chapter = (valid.chapters.length ? valid.chapters : fallbackChapters).some(c=>c.id===selection.chapter)
    ? selection.chapter : "overview";
}
function selectOptions(select, options, value) {
  select.replaceChildren(...options.map(([val,label])=>elem("option",{value:val,text:label})));
  select.value = String(value);
}
function renderControls() {
  const s = specimenRecord();
  selectOptions($("specimen-select"), model.catalog.specimens.map(x=>[x.id,x.origin.replace(/^https?:\/\//,"")]), model.specimen);
  selectOptions($("version-select"), s.versions.map(n=>[String(n),"v"+String(n).padStart(4,"0")]),String(model.version));
  $("research-status").textContent = versionRecord().status === "reviewed" ? "Static review completed" : "Deep research active";
}
function renderNavigation() {
  const nav = $("chapters");
  nav.replaceChildren();
  chapters().forEach((chapter,index)=>{
    const b=elem("button",{type:"button",className:"chapter-link",onClick:()=>setRoute(chapter.id)});
    if(chapter.id===model.chapter)b.setAttribute("aria-current","page");
    append(b,elem("span",{className:"chapter-num",text:String(index+1).padStart(2,"0")}),elem("span",{text:chapter.name}));
    nav.append(b);
  });
}
function pill(text, cls="") { return elem("span",{className:"pill "+cls,text}); }
function evidenceButton(reference) {
  return elem("button",{type:"button",className:"evidence-pill",text:reference,onClick:()=>{
    const finding=versionRecord().findings.find(f=>f.ref===reference);
    if(finding) openInspection("finding",finding);
    else openInspection("message",{name:reference,description:"This reference has not been published in the current version."});
  }});
}
function makeHero(chapter) {
  const header=elem("section",{className:"hero"});
  append(header,elem("div",{className:"eyebrow",text:chapter.eyebrow}),
    elem("h1",{text:chapter.title}),
    elem("p",{className:"lead",text:chapter.lead}));
  const tags=elem("div",{className:"hero-tags"});
  append(tags,pill("chatgpt.com / v"+String(model.version).padStart(4,"0"),"accent"),pill("Source-bounded"));
  (chapter.tags||[]).forEach(label=>tags.append(pill(label)));
  header.append(tags);
  return header;
}
function metrics(chapter) {
  const list=(chapter.metrics||[]).length ? chapter.metrics : [
    ["Published findings",versionRecord().findings.length],
    ["Ontology components",versionRecord().components.length],
    ["Research tasks",versionRecord().tasks.length]
  ];
  const panel=elem("div",{className:"metrics"});
  list.forEach(([label,value])=>panel.append(
    elem("div",{className:"metric"},[
      elem("span",{className:"metric-value",text:value}),
      elem("span",{className:"metric-label",text:label})
    ])
  ));
  return panel;
}
function sectionHeader(kicker,heading,description="") {
  const wrapper=elem("div",{className:"artifact-heading"});
  const left=elem("div");
  append(left,elem("div",{className:"section-kicker",text:kicker}),elem("h2",{text:heading}));
  wrapper.append(left);
  if(description)wrapper.append(elem("p",{text:description}));
  return wrapper;
}
function flowRail(chapter) {
  const box=elem("section");
  box.append(sectionHeader("SYSTEM MAP","How the pieces relate","An explanatory ordering from the captured evidence, not a verified execution trace."));
  const diagram=elem("div",{className:"diagram"});
  diagram.append(elem("div",{className:"diagram-caption",text:"SOURCE → INTERPRETATION → INTERFACE"}));
  const rail=elem("div",{className:"flow-rail",role:"list"});
  chapter.flow.forEach((label,i)=>{
    if(i)rail.append(elem("div",{className:"flow-arrow","aria-hidden":"true",text:"→"}));
    const card=elem("div",{className:"flow-node",role:"listitem"});
    append(card,elem("small",{text:"LAYER "+String(i+1).padStart(2,"0")}),elem("strong",{text:label}));
    rail.append(card);
  });
  diagram.append(rail,elem("div",{className:"diagram-footer"},[
    elem("span",{text:"●  Observed mechanisms and bounded interpretations"}),
    elem("span",{text:"See evidence IDs below ↘"})
  ]));
  box.append(diagram);
  return box;
}
function storySections(chapter) {
  const wrapper=elem("section");
  const heading=elem("div",{className:"section-head"},[
    elem("h2",{text:"Details"}),
    elem("span",{text:"SELECT A CONNECTION TO CONTINUE"})
  ]);
  const cards=elem("div",{className:"story-cards"});
  (chapter.sections||[]).forEach((section,i)=>{
    const card=elem("article",{className:"story-card"});
    append(card,elem("div",{className:"story-card-number",text:"FIELD NOTE / "+String(i+1).padStart(2,"0")}),
      elem("h3",{text:section.title}),elem("p",{text:section.body}));
    if(chapters().some(c=>c.id===section.link))card.append(
      elem("button",{type:"button",className:"text-link",text:"Explore "+section.link+" ↗",onClick:()=>setRoute(section.link)})
    );
    cards.append(card);
  });
  if(cards.childNodes.length)append(wrapper,heading,cards);
  return wrapper;
}
function boundary(text) {
  return elem("aside",{className:"boundary"},[
    elem("span",{className:"boundary-icon","aria-hidden":"true",text:"!"}),
    elem("div",{},[
      elem("strong",{text:"EVIDENCE BOUNDARY"}),
      elem("p",{text})
    ])
  ]);
}
function showEvidenceLinks(chapter) {
  const section=elem("section");
  section.append(sectionHeader("CITABLE OBSERVATIONS","Follow the evidence"));
  const row=elem("div",{className:"evidence-row"});
  (chapter.evidence||[]).forEach(ref=>row.append(evidenceButton(ref)));
  section.append(row);
  return section;
}
function graph() {
  const rec=versionRecord(), pool=[
    "website","dom","javascript","stylesheets","fonts","images","storage","services",
    "stream","a11y","design-system","event-lifecycle","router-stream","theme-init"
  ];
  const chosen=pool.map(id=>rec.components.find(c=>c.id===id)).filter(Boolean).slice(0,12);
  if(chosen.length<3)return null;
  const section=elem("section");
  section.append(sectionHeader("RELATIONSHIP EXPLORER","Component landscape","Select a node to inspect its published description and evidence reference."));
  const outer=elem("div",{className:"graph-panel"});
  const svg=document.createElementNS(namespace,"svg");
  svg.setAttribute("viewBox","0 0 740 365");
  svg.setAttribute("role","img");
  svg.setAttribute("aria-label","Component relationship graph; interactive nodes are also listed below.");
  const positions=new Map();
  chosen.forEach((c,i)=>positions.set(c.id,{x:13+(i%3)*247,y:12+Math.floor(i/3)*86}));
  const related=rec.relationships.filter(r=>positions.has(r.from)&&positions.has(r.to));
  related.forEach(r=>{
    const a=positions.get(r.from),b=positions.get(r.to);
    const line=document.createElementNS(namespace,"line");
    line.setAttribute("x1",a.x+105);line.setAttribute("y1",a.y+31);
    line.setAttribute("x2",b.x+105);line.setAttribute("y2",b.y+31);
    line.setAttribute("class","graph-edge");
    svg.append(line);
  });
  chosen.forEach(c=>{
    const p=positions.get(c.id);
    const box=document.createElementNS(namespace,"rect");
    for(const [k,v] of Object.entries({x:p.x,y:p.y,width:210,height:61,rx:9,class:"graph-node",tabindex:0,role:"button",
      "aria-label":"Inspect "+c.name}))box.setAttribute(k,v);
    box.addEventListener("click",()=>openInspection("component",c));
    box.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();openInspection("component",c);}});
    const label=document.createElementNS(namespace,"text");
    label.setAttribute("x",p.x+11);label.setAttribute("y",p.y+24);label.setAttribute("class","graph-label");
    label.textContent=c.name.length>26?c.name.slice(0,23)+"…":c.name;
    const kind=document.createElementNS(namespace,"text");
    kind.setAttribute("x",p.x+11);kind.setAttribute("y",p.y+43);kind.setAttribute("class","graph-label");
    kind.setAttribute("opacity",".55");kind.textContent=c.kind;
    svg.append(box,label,kind);
  });
  outer.append(svg,elem("p",{className:"graph-caption",text:"A selected subset of the public ontology. Lines represent recorded relationships, not full runtime call paths."}));
  const textList=elem("div",{className:"entity-list"});
  chosen.forEach(c=>textList.append(elem("button",{type:"button",className:"entity-mini",text:c.name,
    onClick:()=>openInspection("component",c)})));
  outer.append(textList);section.append(outer);
  return section;
}

function renderModuleExplorer() {
  const study = versionRecord().visuals?.module_imports;
  if (!study || !study.sources?.length) return null;
  const section = elem("section");
  section.append(sectionHeader("PARSED SOURCE TOPOLOGY", "Parsed module relationships",
    "Every line represents a source-level static import to an anonymous captured resource. It is not a measured runtime dependency."));
  const panel = elem("div",{className:"module-map"});
  const overview = elem("div",{className:"module-intro"},[
    elem("div",{},[elem("strong",{text:String(study.static_edges)}),elem("span",{text:"AST-linked import pairs"})]),
    elem("div",{},[elem("strong",{text:String(study.sources.length)}),elem("span",{text:"Importing bundles"})]),
    elem("div",{},[elem("strong",{text:String(study.target_bundle_count)}),elem("span",{text:"Target bundles"})])
  ]);
  panel.append(overview);
  const grid = elem("div",{className:"module-list"});
  const max = Math.max(...study.sources.map(s=>s.target_count),1);
  study.sources.forEach(item=>{
    const targets = item.target_ranges.map(([low,high])=>low===high
      ?"R-JS-"+String(low).padStart(3,"0")
      :"R-JS-"+String(low).padStart(3,"0")+"…"+String(high).padStart(3,"0")).join(", ");
    const button = elem("button",{type:"button",className:"module-source",
      onClick:()=>openInspection("message",{
        name:item.source,
        description:String(item.target_count)+" parser-matched static import declarations point to saved bundle ordinals: "+targets+
          ". These links were verified as literal import syntax but not as executed imports, load order, or module responsibility."
      })
    });
    const nameRow = elem("div",{className:"module-source-head"},[
      elem("strong",{text:item.source}),
      elem("span",{text:item.target_count+" imports"})
    ]);
    const bar = elem("div",{className:"module-bar"});
    bar.append(elem("span",{className:"module-bar-fill",
      style:"width:"+Math.max(2,100*item.target_count/max).toFixed(1)+"%"}));
    append(button,nameRow,bar,elem("small",{text:targets}));
    grid.append(button);
  });
  panel.append(grid,elem("p",{className:"graph-caption",
    text:"Anonymous script ordinals only. Eight same-ordinal links are retained as uncertain rather than interpreted as runtime recursion. Select a row to inspect its target range."}));
  section.append(panel);
  return section;
}
function renderDomTopology() {
  const study = versionRecord().visuals?.landmarks;
  if (!study) return null;
  const section = elem("section");
  section.append(sectionHeader("OBSERVED DOM REGIONS","Where the controls live",
    "Counted by closest semantic landmark in one saved rendered state; these regions are not verified framework components."));
  const wrap=elem("div",{className:"dom-topology"});
  const max=Math.max(...Object.values(study.closest_landmark_buttons));
  Object.entries(study.closest_landmark_buttons).forEach(([name,value])=>{
    const item=elem("div",{className:"dom-region"},[
      elem("div",{className:"dom-region-label"},[
        elem("strong",{text:name==="other"?"Outside landmarks":name}),
        elem("span",{text:String(value)+" buttons"})
      ]),
      elem("div",{className:"module-bar"},[
        elem("span",{className:"module-bar-fill",style:"width:"+Math.max(2,100*value/max).toFixed(1)+"%"})
      ])
    ]);
    wrap.append(item);
  });
  section.append(wrap);
  return section;
}


function renderCssSystem() {
  const details = versionRecord().visuals?.css_system;
  if (!details?.token_groups?.length) return null;
  const section=elem("section");
  section.append(sectionHeader("CSS DESIGN LANGUAGE","Explore the token families",
    "Generic semantic buckets derived from anonymized CSS property names. These are not verified component ownership groups."));
  const panel=elem("div",{className:"css-system-panel"});
  const overview=elem("div",{className:"module-intro"},[
    elem("div",{},[elem("strong",{text:String(details.distinct_tokens)}),elem("span",{text:"Distinct defined tokens"})]),
    elem("div",{},[elem("strong",{text:String(details.references)}),elem("span",{text:"Variable references"})]),
    elem("div",{},[elem("strong",{text:String(details.container_rule_occurrences)}),elem("span",{text:"Container-rule text matches"})])
  ]);
  panel.append(overview);
  const chart=elem("div",{className:"css-families"});
  const max=Math.max(1,...details.token_groups.map(x=>x.distinct));
  details.token_groups.forEach(group=>{
    const row=elem("div",{className:"css-family"},[
      elem("div",{className:"dom-region-label"},[
        elem("strong",{text:group.name}),
        elem("span",{text:group.distinct+" names · "+group.references+" uses"})
      ]),
      elem("div",{className:"module-bar"},[
        elem("span",{className:"module-bar-fill",style:"width:"+(100*group.distinct/max).toFixed(1)+"%"})
      ])
    ]);
    chart.append(row);
  });
  panel.append(chart,elem("div",{className:"css-summary"},[
    pill(details.media_rule_occurrences+" media at-rules"),
    pill(details.reduced_motion_rules+" motion-preference conditions"),
    pill(details.keyframes+" keyframe rules")
  ]));
  panel.append(elem("p",{className:"graph-caption",
    text:"Prefixes are grouped heuristically. Conditions can overlap; source presence does not prove the winning computed CSS or visible animation."}));
  section.append(panel);
  return section;
}


function renderSourceSignals(chapterId) {
  const signals=versionRecord().visuals?.source_system;
  if (!signals) return null;
  const variants={
    logic:{title:"The event and observer machinery",key:"event_signals",description:"AST-level listener, observer and animation-frame syntax; these are not observed user interactions."},
    state:{title:"Browser persistence and channels",key:"state_signals",description:"Fixed-name call and constructor syntax in captured bundles. No storage values, session identifiers or actual messages were observed."},
    flow:{title:"Streaming and transport code",key:"network_signals",description:"Syntax-tree API callsites indicate possible pathways, not verified API responses or a chronological runtime flow."}
  };
  const variant=variants[chapterId];
  if(!variant)return null;
  const items=signals[variant.key];
  const section=elem("section");
  section.append(sectionHeader("SOURCE SIGNALS",variant.title,variant.description));
  const panel=elem("div",{className:"signal-panel"});
  const max=Math.max(1,...items.map(x=>x.count));
  const list=elem("div",{className:"signal-list"});
  items.forEach(item=>{
    list.append(elem("div",{className:"signal-row"},[
      elem("div",{className:"dom-region-label"},[
        elem("strong",{text:item.label}),elem("span",{text:String(item.count)+" source matches"})
      ]),
      elem("div",{className:"module-bar"},[
        elem("span",{className:"module-bar-fill",style:"width:"+(item.count/max*100).toFixed(2)+"%"})
      ])
    ]));
  });
  panel.append(list);
  if(chapterId==="flow"){
    const scopes=signals.lexical_scopes;
    panel.append(elem("div",{className:"css-summary"},[
      pill(scopes.fetch_and_stream+" function scopes: fetch + stream"),
      pill(scopes.fetch_and_abort+" function scopes: fetch + abort")
    ]));
  }
  panel.append(elem("p",{className:"graph-caption",
    text:"Only generic platform API names are represented. Repeated calls may occur in libraries or unused code. No captured names, account data, remote endpoints or code are displayed."}));
  section.append(panel);return section;
}
function renderResourceBudget() {
  const budget=versionRecord().visuals?.source_system?.bytes;
  if(!budget)return null;
  const items=[["JavaScript",budget.scripts],["CSS",budget.css],["Fonts",budget.fonts],["Images",budget.images]];
  const section=elem("section");
  section.append(sectionHeader("CAPTURE BYTE BUDGET","Where the saved bytes are","Capture sizes, not real transfer sizes or a measured performance waterfall."));
  const panel=elem("div",{className:"signal-panel"});const max=Math.max(...items.map(x=>x[1]),1);
  const list=elem("div",{className:"signal-list"});
  items.forEach(([name,count])=>list.append(elem("div",{className:"signal-row"},[
    elem("div",{className:"dom-region-label"},[
      elem("strong",{text:name}),elem("span",{text:(count/1000000).toFixed(2)+" MB captured"})
    ]),
    elem("div",{className:"module-bar"},[
      elem("span",{className:"module-bar-fill",style:"width:"+(count/max*100).toFixed(1)+"%"})
    ])
  ])));
  panel.append(list);section.append(panel);return section;
}

function renderArticle(chapter,host) {
  if (chapter.id === "stack" || chapter.id === "page-map") {
    host.append(makeHero(chapter));
    host.append(chapter.id === "stack"
      ? ViewsourceExplorer.renderStack(versionRecord())
      : ViewsourceExplorer.renderMap(versionRecord()));
    host.append(showEvidenceLinks(chapter));
    return;
  }
  if (chapter.id === "overview" && versionRecord().visuals?.technology) {
    host.append(makeHero(chapter));
    host.append(ViewsourceExplorer.renderMap(versionRecord(), true));
    host.append(ViewsourceExplorer.renderStack(versionRecord(), true));
    host.append(storySections(chapter));
    host.append(showEvidenceLinks(chapter));
    return;
  }
  append(host,makeHero(chapter),metrics(chapter));
  if(chapter.id === "flow" && chapter.flow.length)host.append(flowRail(chapter));
  host.append(storySections(chapter));
  if (chapter.id === "javascript") { const modules=renderModuleExplorer(); if(modules) host.append(modules); }
  if (chapter.id === "css") { const visual=renderCssSystem(); if(visual) host.append(visual); }
  { const panel=renderSourceSignals(chapter.id); if(panel) host.append(panel); }
  if (chapter.id === "overview") { const budget=renderResourceBudget(); if(budget) host.append(budget); }
  if (chapter.id === "html" || chapter.id === "components") {
    const dom=renderDomTopology(); if(dom) host.append(dom);
  }
  if(chapter.id==="overview"||chapter.id==="components"||chapter.id==="javascript") {
    const graphView=graph();if(graphView)host.append(graphView);
  }
  if(chapter.unknown)host.append(boundary(chapter.unknown));
  host.append(showEvidenceLinks(chapter));
}
function metaList(rows) {
  const dl=elem("dl",{className:"inspection-meta"});
  rows.forEach(([k,v])=>dl.append(elem("div",{},[elem("dt",{text:k}),elem("dd",{text:v})])));
  return dl;
}
function openInspection(type,record) {
  const root=$("inspection");root.replaceChildren();
  const card=elem("div",{className:"inspection-card"});
  if(type==="finding"){
    append(card,pill("EVIDENCE "+(record.ref||""),"accent"),
      elem("h3",{text:"Finding "+record.id}),
      elem("p",{text:record.statement}),
      metaList([["Evidence class",record.class],["Confidence",record.confidence],["Reference",record.ref||"Unavailable"],["Specimen","v"+String(model.version).padStart(4,"0")]]));
  } else if(type==="component"){
    append(card,pill(record.kind,"accent"),
      elem("h3",{text:record.name}),
      elem("p",{text:record.description}),
      metaList([["Ontology ID",record.id],["Evidence",record.evidence_ref||"Not specified"],["Evidence class",record.evidence_class]]));
    const adjacent=versionRecord().relationships.filter(r=>r.from===record.id||r.to===record.id).slice(0,12);
    if(adjacent.length){
      append(card,elem("div",{className:"section-kicker",text:"RECORDED RELATIONSHIPS"}));
      const ul=elem("ul");
      adjacent.forEach(rel=>ul.append(elem("li",{text:(rel.from===record.id?"→ "+rel.to:rel.from+" →")+
        " · "+rel.predicate})));
      card.append(ul);
    }
  } else if(type==="task"){
    append(card,pill(statusLabels[record.status]||record.status,"warm"),
      elem("h3",{text:record.title}),
      elem("p",{text:record.notes||"No additional task notes."}),
      metaList([["Work queue",record.queue],["Status",statusLabels[record.status]||record.status],
        ["Dependencies",String(record.depends_on.length)],["Task ID",record.id]]));
    if(record.depends_on.length){
      card.append(elem("div",{className:"section-kicker",text:"TASK DEPENDENCIES"}));
      const ul=elem("ul");
      const byId=new Map(versionRecord().tasks.map(t=>[t.id,t]));
      record.depends_on.forEach(id=>{
        const item=byId.get(id);
        ul.append(elem("li",{text:(item?item.title:id)+" — "+(item?statusLabels[item.status]:"unknown")}));
      });
      card.append(ul);
    }
  } else {
    append(card,elem("h3",{text:record.name||"Research note"}),elem("p",{text:record.description||""}));
  }
  root.append(card);
  if(matchMedia("(max-width: 720px)").matches) $("inspector").scrollIntoView({behavior:"smooth",block:"start"});
}
function renderEmptyInspector() {
  $("inspection").replaceChildren(elem("div",{className:"inspector-empty"},[
    elem("div",{className:"inspector-empty-symbol","aria-hidden":"true",text:"↗"}),
    elem("p",{text:"This panel connects the narrative to the published research record. Open an evidence ID, an ontology node, or a research task to see its provenance and constraints."})
  ]));
}
function filterText(query,content) { return content.toLowerCase().includes(query.toLowerCase()); }
function renderFindings(host,onlyQuery="") {
  const rec=versionRecord();
  const intro=elem("section",{className:"hero"},[
    elem("div",{className:"eyebrow",text:"RESEARCH LEDGER"}),
    elem("h1",{text:onlyQuery?"Research matches":"Evidence, not assertion."}),
    elem("p",{className:"lead",text:"All published findings are linked to a source scope and confidence classification. The original capture remains private."})
  ]);
  host.append(intro);
  const content=rec.findings.filter(f=>!onlyQuery||filterText(onlyQuery,f.id+" "+f.ref+" "+f.statement+" "+f.class));
  host.append(elem("div",{className:"section-head"},[
    elem("h2",{text:"Published findings"}),
    elem("span",{text:content.length+" of "+rec.findings.length})
  ]));
  const wrap=elem("div",{className:"collection"});
  content.forEach(f=>{
    const item=elem("article",{className:"finding"});
    append(item,elem("div",{className:"finding-top"},[
      elem("span",{className:"finding-id",text:f.id+" / "+(f.ref||"")}),
      pill(f.class==="observed_static"?"Observed static":f.class,"accent")
    ]),elem("p",{text:f.statement}),
    elem("button",{type:"button",text:"Inspect finding ↗",onClick:()=>openInspection("finding",f)}));
    wrap.append(item);
  });
  if(!content.length)wrap.append(elem("p",{className:"result-empty",text:"No findings match this search."}));
  host.append(wrap);
}
function derivedStatus(task,byId) {
  if(task.status!=="queued")return task.status;
  const blocked=task.depends_on.some(dep=>!["done","not_observable"].includes(byId.get(dep)?.status));
  return blocked?"blocked":"queued";
}
function renderWork(host,query="") {
  const rec=versionRecord(), all=rec.tasks, byId=new Map(all.map(t=>[t.id,t]));
  const deep=all.filter(t=>t.id.includes("-followup-deep-"));
  const done=all.filter(t=>t.status==="done").length;
  const pending=all.filter(t=>t.status==="queued"||t.status==="in_progress"||t.status==="blocked").length;
  append(host,elem("section",{className:"hero"},[
    elem("div",{className:"eyebrow",text:"PERSISTENT RESEARCH PROGRAM"}),
    elem("h1",{text:"Research tasks"}),
    elem("p",{className:"lead",text:"The first analysis pass is not the last. Every deep task has a dependency chain and must be closed through evidence, not an automatic inventory count."})
  ]));
  const metricBox=elem("div",{className:"metrics"});
  [["Deep tasks",deep.length],["Active tasks",pending],["Previously completed",done]].forEach(([label,value])=>metricBox.append(
    elem("div",{className:"metric"},[elem("span",{className:"metric-value",text:value}),elem("span",{className:"metric-label",text:label})])
  ));
  host.append(metricBox);
  const filtered=all.filter(t=>!query||filterText(query,t.title+" "+t.queue+" "+t.id+" "+t.notes));
  const groups=new Map();
  filtered.forEach(t=>{if(!groups.has(t.queue))groups.set(t.queue,[]);groups.get(t.queue).push(t);});
  host.append(sectionHeader("TASK DEPENDENCIES","Investigations by workstream","Expand a queue; click a task to inspect its required evidence and dependencies."));
  if(!groups.size)host.append(elem("div",{className:"result-empty",text:"No research tasks matched."}));
  [...groups].sort(([a],[b])=>a.localeCompare(b)).forEach(([name,list])=>{
    const details=elem("details",{className:"queue-group"});
    const summary=elem("summary",{className:"queue-head"});
    append(summary,elem("span",{text:name.charAt(0).toUpperCase()+name.slice(1)}),
      elem("small",{text:list.length+" tasks · "+list.filter(t=>t.status==="queued").length+" queued"}));
    details.append(summary);
    const wrap=elem("div",{className:"queue-content"});
    list.sort((a,b)=>(a.status==="queued"?0:1)-(b.status==="queued"?0:1));
    list.forEach(t=>{
      const status=derivedStatus(t,byId);
      const row=elem("article",{className:"task"});
      append(row,elem("div",{className:"task-top"},[
        elem("span",{className:"task-id",text:t.id.includes("-deep-")?"DEEP RESEARCH":"INITIAL PASS"}),
        elem("span",{className:"task-status "+status,text:status==="queued"?"Ready":statusLabels[status]||status})
      ]),elem("h3",{text:t.title}),elem("p",{text:t.notes||"Source-grounded research task."}),
      elem("button",{type:"button",text:"Inspect dependencies ↗",onClick:()=>openInspection("task",t)}));
      wrap.append(row);
    });
    details.append(wrap);
    if(query || list.some(t=>t.status==="queued"))details.open=true;
    host.append(details);
  });
}
function renderSearch(host) {
  const q=model.query.trim();
  const rec=versionRecord();
  host.append(elem("section",{className:"hero"},[
    elem("div",{className:"eyebrow",text:"ATLAS SEARCH"}),
    elem("h1",{text:"Results for “"+q+"”"}),
    elem("p",{className:"lead",text:"Search is restricted to original, published analysis: chapters, findings, components, and the task ledger."})
  ]));
  const matchChapters=chapters().filter(c=>filterText(q,c.title+" "+c.lead+" "+c.name));
  if(matchChapters.length){
    host.append(sectionHeader("STORY","Chapters"));
    const wrap=elem("div",{className:"entity-list"});
    matchChapters.forEach(c=>wrap.append(elem("button",{className:"entity-mini",type:"button",text:c.name+" →",onClick:()=>setRoute(c.id)})));
    host.append(wrap);
  }
  const componentMatches=rec.components.filter(c=>filterText(q,c.name+" "+c.kind+" "+c.description)).slice(0,30);
  if(componentMatches.length){
    host.append(sectionHeader("ONTOLOGY", "Component matches"));
    const wrap=elem("div",{className:"entity-list"});
    componentMatches.forEach(c=>wrap.append(elem("button",{className:"entity-mini",type:"button",text:c.name,onClick:()=>openInspection("component",c)})));
    host.append(wrap);
  }
  const findingMatches=rec.findings.filter(f=>filterText(q,f.id+" "+f.ref+" "+f.statement));
  if(findingMatches.length){
    host.append(sectionHeader("EVIDENCE",findingMatches.length+" matching findings"));
    const row=elem("div",{className:"evidence-row"});
    findingMatches.slice(0,20).forEach(f=>row.append(evidenceButton(f.ref)));
    host.append(row);
  }
  const taskMatches=rec.tasks.filter(t=>filterText(q,t.title+" "+t.queue+" "+t.notes));
  if(taskMatches.length){
    host.append(sectionHeader("WORK QUEUES",taskMatches.length+" related investigations"));
    const row=elem("div",{className:"entity-list"});
    taskMatches.slice(0,30).forEach(t=>row.append(elem("button",{className:"entity-mini",type:"button",text:t.title,onClick:()=>openInspection("task",t)})));
    host.append(row);
  }
  if(!matchChapters.length&&!componentMatches.length&&!findingMatches.length&&!taskMatches.length)
    host.append(elem("p",{className:"result-empty",text:"No published research matched your search."}));
}
function render() {
  if(!model.catalog)return;
  renderControls();renderNavigation();
  const c=chapterRecord();
  $("breadcrumbs").textContent="VIEWSOURCE / "+model.specimen.toUpperCase()+" / V"+String(model.version).padStart(4,"0")+" / "+c.name.toUpperCase();
  const host=$("story");host.replaceChildren();
  if(model.query.trim())renderSearch(host);
  else if(c.id==="evidence")renderFindings(host);
  else if(c.id==="work")renderWork(host);
  else renderArticle(c,host);
}
async function initialize() {
  const stored=document.documentElement.dataset.theme||"system";
  $("theme-select").value=["system","light","dark"].includes(stored)?stored:"system";
  $("theme-select").addEventListener("change",e=>{
    const chosen=e.target.value;
    if(!["system","light","dark"].includes(chosen))return;
    document.documentElement.dataset.theme=chosen;
    try{localStorage.setItem("viewsource:theme",chosen);}catch(_){}
  });
  $("specimen-select").addEventListener("change",e=>{
    const next=model.catalog.specimens.find(s=>s.id===e.target.value);
    if(next)setRoute("overview",next.current_version,next.id);
  });
  $("version-select").addEventListener("change",e=>setRoute("overview",Number(e.target.value),model.specimen));
  $("site-search").addEventListener("input",e=>{
    model.query=e.target.value;
    $("clear-search").hidden=!model.query;
    render();
  });
  $("clear-search").addEventListener("click",()=>{
    model.query="";$("site-search").value="";$("clear-search").hidden=true;render();$("site-search").focus();
  });
  try {
    const response=await fetch("./data/catalog.json",{cache:"no-cache"});
    if(!response.ok)throw new Error("Research catalogue unavailable ("+response.status+")");
    model.catalog=await response.json();
    if(!model.catalog.specimens?.length)throw new Error("The research catalogue is empty");
    selectModel();renderEmptyInspector();render();
    window.addEventListener("hashchange",()=>{
      if(!model.catalog)return;
      const previous=model.chapter+"|"+model.version+"|"+model.specimen;
      selectModel();if(previous!==model.chapter+"|"+model.version+"|"+model.specimen){
        model.query="";$("site-search").value="";$("clear-search").hidden=true;
        renderEmptyInspector();render();
      }
    });
  } catch(error) {
    $("story").replaceChildren(elem("div",{className:"result-empty",text:
      "Unable to load the research catalogue. "+error.message+
      ". Open the published website via HTTP(S), not as a local file."}));
    $("research-status").textContent="Research data unavailable";
  }
}
initialize();

