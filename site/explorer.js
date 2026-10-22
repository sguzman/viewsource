"use strict";
// Original diagrams based on public, whitelisted research data.
window.ViewsourceExplorer = (() => {
  function el(tag, cls="", text) {
    const node=document.createElement(tag);
    node.className=cls;
    if(text!==undefined)node.textContent=String(text);
    return node;
  }
  const add=(node,...children)=>{children.forEach(c=>c&&node.append(c));return node;};
  const head=(label,title,description)=>add(el("div","explorer-heading"),el("div","section-kicker",label),el("h2","",title),el("p","",description));
  function stack(record,compact=false) {
    const data=record.visuals?.technology;
    if(!data?.technologies?.length)return el("p","result-empty","No library inventory for this capture.");
    const section=el("section","technology-explorer");
    section.append(head("SOFTWARE FOUND","Libraries and frameworks","Open a card to see its markers. Versions and live execution were not verified."));
    const gallery=el("div","technology-grid");
    const items=compact?data.technologies.filter(x=>x.confidence==="strong"):data.technologies;
    const choices=compact?["strong"]:["all","strong","likely","indicator"];
    const buttons=el("div","technology-filters");const cards=[];
    choices.forEach(filter=>{
      const button=el("button","technology-filter",filter==="all"?"All":filter[0].toUpperCase()+filter.slice(1));
      button.type="button";button.setAttribute("aria-pressed",String(filter===choices[0]));
      button.addEventListener("click",()=>{
        [...buttons.children].forEach(b=>b.setAttribute("aria-pressed",String(b===button)));
        cards.forEach(([card,item])=>card.hidden=filter!=="all"&&item.confidence!==filter);
      });
      buttons.append(button);
    });
    items.forEach(item=>{
      const card=el("details","technology-card");
      const summary=el("summary","technology-summary");
      const name=add(el("span","technology-name"),el("strong","",item.name),el("small","",item.category));
      add(summary,name,el("span","technology-confidence",item.confidence==="strong"?"Strong evidence":item.confidence==="likely"?"Likely":"Indicator"));
      card.append(summary);
      const body=el("div","technology-details");
      body.append(el("p","",item.evidence),el("p","",item.role?"Potential use: "+item.role:""));
      const list=el("ul","technology-signatures");
      (item.observations||[]).forEach(s=>list.append(el("li","",s.marker+": "+s.matches+" matches in "+s.files+" captured files")));
      body.append(list,el("p","technology-limit",item.note),el("p","technology-version","Version: not established"));
      card.append(body);gallery.append(card);cards.push([card,item]);
    });
    section.append(buttons,gallery);
    if(!compact){
      const unknown=el("div","technology-unresolved");
      unknown.append(el("h3","","Not established"));
      const list=el("ul");
      (data.unresolved||[]).forEach(x=>list.append(el("li","",x.technology+": "+x.reason)));
      unknown.append(list);section.append(unknown);
    } else {
      const button=el("button","text-link","Open all libraries →");button.type="button";button.addEventListener("click",()=>setRoute("stack"));section.append(button);
    }
    return section;
  }
  function pageMap(record,compact=false){
    const data=record.visuals?.page_map;
    if(!data?.nodes?.length)return el("p","result-empty","No page map for this capture.");
    const section=el("section","page-explorer");
    section.append(head("SAVED HTML","Page layout","Click a region to inspect it. This is a structural diagram, not a screenshot."));
    const nodes=new Map(data.nodes.map(n=>[n.id,n]));
    const region=(id,cls)=>{
      const item=nodes.get(id), button=el("button","wire-node "+cls);
      button.type="button";button.setAttribute("aria-label","Inspect "+item.title);
      const count=Object.entries(item.counts).map(([name,value])=>value+" "+name.replace(/_/g," ")).join(" · ");
      add(button,el("strong","",item.title),el("small","",item.kind),el("span","wire-count",count));
      button.addEventListener("click",()=>openInspection("message",{name:item.title,description:item.description+" "+count+". Evidence: "+item.evidence+". Regions are nested, so descendant counts overlap. No page content is reproduced."}));
      return button;
    };
    const diagram=el("div","wireframe");
    const aside=add(el("div","wire-sidebar"),region("sidebar","wire-sidebar-head"),region("top-nav","wire-top-nav"),region("list-nav","wire-list-nav"));
    const main=el("div","wire-main");
    const content=add(el("div","wire-content-placeholder"),el("strong","","Page content"),el("span","","Private conversation contents excluded"));
    add(main,region("main","wire-main-head"),region("page-header","wire-header"),content,region("composer","wire-composer"));
    const overlay=add(el("div","wire-overlay"),region("dialog","wire-dialog"));
    diagram.append(aside,main,overlay);section.append(diagram);
    if(!compact){
      const controls=el("div","whitelist-controls");
      controls.append(el("h3","","Control categories observed in labels"));
      const row=el("div","control-categories");
      (data.observed_control_categories||[]).forEach(x=>row.append(el("span","control-category",x.label+": "+x.aria_matches)));
      controls.append(row,el("p","graph-caption",data.note));section.append(controls);
    }else{
      const open=el("button","text-link","Inspect the full page map →");open.type="button";open.addEventListener("click",()=>setRoute("page-map"));section.append(open);
    }
    section.append(el("p","graph-caption","Based on one captured DOM, not an exact pixel layout or recovered React component hierarchy."));
    return section;
  }
  return {renderStack:stack,renderMap:pageMap};
})();
