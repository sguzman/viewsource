"use strict";
/* Project-authored feature graph viewer. Never renders captured account content. */
window.ViewsourceChatGraph = (() => {
  const element=(tag,className="",value)=>{
    const node=document.createElement(tag);node.className=className;
    if(value!==undefined)node.textContent=String(value);
    return node;
  };
  const add=(container,...children)=>{children.forEach(child=>container.append(child));return container;};
  function render(record){
    const feature=record.visuals?.feature_graph;
    if(!feature)return element("p","result-empty","No chat interaction graph for this capture.");
    const section=element("section","chat-feature");
    const head=add(element("div","explorer-heading"),
      element("div","section-kicker","CHAT INTERACTION"),
      element("h2","","Chat state model"),
      element("p","","Select a machine and a state to inspect candidate transitions, guards and verification steps."));
    const warning=element("p","chat-warning",
      "Only UI regions were observed in the saved page. Every state transition below is a candidate, not verified ChatGPT behavior.");
    const link=element("a","text-link","Open machine-readable graph JSON ↗");
    link.href=feature.json_path;
    link.target="_blank";link.rel="noopener noreferrer";
    section.append(head,warning,link);
    const surface=element("div","chat-surface-list");
    feature.surfaces.forEach(item=>{
      const node=add(element("div","chat-surface"),
        element("strong","",item.label),
        element("small","",item.basis==="observed_static"?"Observed HTML":"Not verified"),
        element("p","",item.description));
      surface.append(node);
    });
    section.append(add(element("div","chat-subsection"),element("h3","","Observed page regions"),surface));
    const machineTabs=element("div","chat-machine-tabs");
    const stateHost=element("div","chat-states");
    const transitionHost=element("div","chat-transitions");
    const details=element("div","chat-subsection");
    details.append(element("h3","","Possible state changes"),transitionHost);
    const getEvent=id=>feature.events.find(e=>e.id===id);
    let selectedMachine=feature.machines[0]?.id||"",selectedState="";
    function renderEdges(){
      transitionHost.replaceChildren();
      const edges=feature.transitions.filter(t=>t.machine===selectedMachine&&(selectedState===""||t.from===selectedState));
      if(!edges.length){transitionHost.append(element("p","result-empty","No candidate transitions from this state."));return;}
      edges.forEach(t=>{
        const event=getEvent(t.event);
        const card=element("details","chat-transition");
        const summary=add(element("summary","chat-transition-top"),
          element("strong","",t.from+" → "+t.to),
          element("span","",event?event.label:t.event),
          element("small","",t.evidence_status==="hypothesis"?"Not verified":"Observed live"));
        const inner=element("div","chat-transition-details");
        if(t.guards.length)inner.append(element("p","","Guards: "+t.guards.join("; ")));
        if(t.effects.length)inner.append(element("p","","Possible effects: "+t.effects.join("; ")));
        inner.append(element("p","","How to verify: "+t.verify));
        card.append(summary,inner);transitionHost.append(card);
      });
    }
    function renderStates(){
      stateHost.replaceChildren();const machine=feature.machines.find(m=>m.id===selectedMachine);
      if(!machine)return;
      stateHost.append(element("p","graph-caption","Candidate states for "+machine.label+". Select a state to filter transitions."));
      const buttons=element("div","chat-state-buttons");
      machine.states.forEach(s=>{
        const button=element("button","chat-state",s.label);
        button.type="button";button.setAttribute("aria-pressed",String(selectedState===s.id));
        button.addEventListener("click",()=>{selectedState=selectedState===s.id?"":s.id;renderStates();renderEdges();});
        buttons.append(button);
      });
      stateHost.append(buttons);
      renderEdges();
    }
    function renderTabs(){
      machineTabs.replaceChildren();
      feature.machines.forEach(m=>{
        const button=element("button","chat-tab",m.label);
        button.type="button";button.setAttribute("aria-pressed",String(selectedMachine===m.id));
        button.addEventListener("click",()=>{selectedMachine=m.id;selectedState="";renderTabs();renderStates();});
        machineTabs.append(button);
      });
    }
    renderTabs();renderStates();
    section.append(add(element("div","chat-subsection"),element("h3","","Candidate state machines"),machineTabs,stateHost),details);
    const branch=element("div","chat-subsection");
    branch.append(element("h3","","Message relationships and branches"),
      element("p","",feature.branch_model.description),
      element("p","chat-warning","Branch identity and selection behavior are not established by this capture."));
    const questions=element("ul","chat-questions");
    feature.branch_model.required_observations.forEach(question=>questions.append(element("li","",question)));
    branch.append(questions);section.append(branch);
    const unresolved=element("div","chat-subsection");
    unresolved.append(element("h3","","What to test next"));
    feature.open_questions.forEach(q=>{
      const row=element("details","chat-question");
      row.append(element("summary","",q.question),element("p","",q.next_evidence));
      unresolved.append(row);
    });
    section.append(unresolved);
    return section;
  }
  return {render};
})();
