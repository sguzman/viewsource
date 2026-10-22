"use strict";
/* Project-authored feature graph viewer. Never renders captured account content. */
window.ViewsourceChatGraph = (() => {
  const element=(tag,className="",value)=>{
    const node=document.createElement(tag);node.className=className;
    if(value!==undefined)node.textContent=String(value);
    return node;
  };
  const add=(container,...children)=>{children.forEach(child=>container.append(child));return container;};
  function renderSyntheticExample(){
    const block=element("div","chat-subsection");
    block.append(element("h3","","Explore a synthetic message graph"));
    block.append(element("p","graph-caption",
      "Invented messages and relationships, not a reconstruction of ChatGPT's storage model. Switch the visible response or display a separate candidate fork."));
    const controls=element("div","chat-example-controls");
    const replyOne=element("button","chat-example-choice","Select response A");
    const replyTwo=element("button","chat-example-choice","Select response B");
    const fork=element("button","chat-example-choice","Show separate conversation fork");
    [replyOne,replyTwo,fork].forEach(button=>{button.type="button";controls.append(button);});
    const figure=element("div","chat-example-figure");
    const status=element("p","chat-example-status");
    const structural=element("div","chat-example-metrics");
    let selected="a",forkVisible=false;
    const makeNode=(label,detail,active=false)=>{
      const node=element("div","chat-example-node");
      node.setAttribute("data-selected",String(active));
      node.append(element("strong","",label),element("small","",detail));
      return node;
    };
    function draw(){
      replyOne.setAttribute("aria-pressed",String(selected==="a"));
      replyTwo.setAttribute("aria-pressed",String(selected==="b"));
      fork.setAttribute("aria-pressed",String(forkVisible));
      figure.replaceChildren();
      const first=element("div","chat-example-conversation");
      first.append(element("div","chat-example-caption","Conversation A · synthetic"));
      const top=element("div","chat-example-row");
      top.append(makeNode("User message","Node U1",true));
      const second=element("div","chat-example-row chat-example-alternatives");
      second.append(makeNode("Assistant response A","Node A1",selected==="a"));
      second.append(makeNode("Assistant response B","Node A2",selected==="b"));
      first.append(top,element("div","chat-example-connector","↓"),second);
      figure.append(first);
      if(forkVisible){
        const secondChat=element("div","chat-example-conversation");
        secondChat.append(element("div","chat-example-caption","Conversation B · synthetic fork"),
          element("p","graph-caption","Candidate link from U1; no claim that the original messages are copied."),
          makeNode("Separate conversation root","Node B1",true));
        figure.append(secondChat);
      }
      structural.replaceChildren();
      const metrics=[
        ["Conversations",forkVisible?2:1],
        ["Message nodes",forkVisible?4:3],
        ["Alternative replies",1],
        ["Candidate cross-chat links",forkVisible?1:0]
      ];
      metrics.forEach(([label,value])=>{
        const card=element("div","chat-example-metric");
        card.append(element("strong","",value),element("small","",label));
        structural.append(card);
      });
      status.textContent="Selected path in A: U1 → "+(selected==="a"?"A1":"A2")+
        (forkVisible?" · Candidate cross-conversation fork shown":"");
    }
    replyOne.addEventListener("click",()=>{selected="a";draw();});
    replyTwo.addEventListener("click",()=>{selected="b";draw();});
    fork.addEventListener("click",()=>{forkVisible=!forkVisible;draw();});
    draw();
    block.append(controls,figure,structural,status);
    return block;
  }
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
    const capabilities=record.visuals?.chat_capabilities;
    if(capabilities?.entries?.length){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Chat functionality: evidence by operation"));
      block.append(element("p","graph-caption",
        "Static evidence, public documentation and candidate event models are separate. No operation below has a verified internal runtime contract."));
      const list=element("div","chat-capability-list");
      capabilities.entries.forEach(item=>{
        const card=element("details","chat-capability");
        const summary=element("summary","");
        summary.append(element("strong","",item.label),
          element("small","","Not verified internally"));
        card.append(summary);
        const observed=item.static_refs.length?"Saved-file evidence: "+item.static_refs.join(", "):"Saved-file action evidence: not established";
        card.append(element("p","",observed));
        card.append(element("p","",item.documented_action?
          "Official UI documentation: available ("+item.documented_action.replaceAll("_"," ")+").":
          "Official UI documentation: not linked in this study."));
        if(item.candidate_events.length)card.append(element("p","",
          "Candidate events: "+item.candidate_events.join(", ")));
        if(item.candidate_relations.length)card.append(element("p","",
          "Candidate relationships: "+item.candidate_relations.join(", ")));
        card.append(element("p","chat-capability-next","Next test: "+item.next_experiment));
        list.append(card);
      });
      block.append(list);section.append(block);
    }
    const implTrace=record.visuals?.chat_static_impl_trace;
    if(implTrace){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Traced client implementation"));
      block.append(element("p","graph-caption",
        "Actual client-side code shapes from the captured JavaScript, labeled by anonymous source/function ordinals. Static evidence only; no verified server storage or network behavior."));
      block.append(element("p","chat-implementation-totals",
        implTrace.match_count+" AST pattern matches across "+implTrace.matched_functions+" captured functions; "+implTrace.reviewed_operations.length+" operations examined."));
      const items=element("div","chat-implementation-list");
      for(const operation of implTrace.reviewed_operations){
        const card=element("details","chat-implementation-card");
        const summary=element("summary","");
        summary.append(element("strong","",operation.classification),
          element("small","",operation.source_ref+" / function "+operation.function_ordinal));
        card.append(summary,element("p","",operation.description),
          element("p","graph-caption",operation.limits));
        items.append(card);
      }
      block.append(items);
      const questions=element("details","chat-implementation-questions");
      questions.append(element("summary","","Next source-level investigations"));
      const lines=element("ul","");
      implTrace.open_static_questions.forEach(item=>lines.append(element("li","",item)));
      questions.append(lines);
      block.append(questions);
      section.append(block);
    }
    const astStudy=record.visuals?.chat_ast_followup;
    if(astStudy){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Implementation evidence from captured JavaScript"));
      block.append(element("p","graph-caption",
        "Parsed, locally captured function/property operations. These are concrete syntax observations, not verified chat handler ownership or backend behavior."));
      const metrics=element("div","chat-ast-metrics");
      [["Parsed bundles",astStudy.parsed_bundles],
       ["Candidate functions",astStudy.candidate_functions],
       ["Bundles with candidates",astStudy.candidate_bundles]].forEach(([label,count])=>{
         const cell=element("div","chat-ast-stat");
         cell.append(element("strong","",String(count)),element("small","",label));
         metrics.append(cell);
       });
      block.append(metrics);
      const details=element("details","chat-ast-details");
      details.append(element("summary","","Member operations and remaining research"));
      const pairs=element("ul","");
      astStudy.cooccurrences.forEach(item=>pairs.append(element("li","",item.label+": "+item.count+" function scopes")));
      details.append(element("p","graph-caption",
        "Member-property pairs are not confirmed data schemas or call edges."),pairs);
      const unresolved=element("ul","");
      astStudy.unresolved.forEach(item=>unresolved.append(element("li","",item)));
      details.append(element("p","graph-caption","Unresolved:"),unresolved);
      block.append(details);
      section.append(block);
    }
    const exported=record.visuals?.chat_export_format;
    if(exported?.fields?.length){
      const block=element("div","chat-subsection");
      block.append(element("h3","","How exported conversation trees are organized"));
      block.append(element("p","graph-caption",
        "Public export documentation and community parser research. This is not a recovered live ChatGPT API or database schema."));
      const fields=element("div","chat-export-fields");
      exported.fields.forEach(item=>{
        const field=element("div","chat-export-field");
        field.append(element("strong","",item.field),element("p","",item.meaning));
        fields.append(field);
      });
      block.append(fields);
      const relations=element("div","chat-export-operations");
      exported.operations.forEach(item=>{
        relations.append(element("p","",item.operation.replaceAll("_"," ")+": "+item.description));
      });
      block.append(relations);
      const references=element("details","chat-export-references");
      references.append(element("summary","","Sources and limitations"));
      exported.sources.forEach(item=>{
        const link=element("a","text-link",item.authority+": "+item.title+" ↗");
        link.href=item.url;link.target="_blank";link.rel="noopener noreferrer";
        references.append(link);
      });
      block.append(references);
      block.append(element("p","chat-document-limit",
        "The export tree can be inspected locally with the content-free analyzer. No real export was used in this research."));
      section.append(block);
    }
    const documented=record.visuals?.public_chat_actions;
    if(documented?.actions?.length){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Documented ChatGPT actions"));
      block.append(element("p","graph-caption",
        "Public Help Center descriptions. These confirm user-facing controls, not internal handler code, API contracts or graph storage."));
      const entries=element("div","chat-documented-list");
      documented.actions.forEach(action=>{
        const card=element("details","chat-documented-action");
        const heading=element("summary","");
        heading.append(element("strong","",action.name),
          element("small","","Documented UI"));
        card.append(heading,element("p","",action.summary));
        const source=element("a","text-link","Source: "+action.source_title+" ↗");
        source.href=action.source_url;
        source.target="_blank";
        source.rel="noopener noreferrer";
        card.append(source);
        card.append(element("p","chat-document-limit","Not established: "+action.unknown));
        entries.append(card);
      });
      block.append(entries);
      section.append(block);
    }
    const signals=record.visuals?.chat_source_signals;
    if(signals){
      const block=element("div","chat-subsection");
      block.append(element("h3","","What the saved JavaScript contains"));
      const note=element("p","graph-caption","Bundle and syntax-tree counts. They are not a recovered chat protocol or verified data format.");
      block.append(note);
      const cards=element("div","chat-signals");
      signals.summary.forEach(x=>{
        const card=element("div","chat-source-card");
        card.append(element("strong","",x.count),element("small","",x.label+" · saved bundles"));
        cards.append(card);
      });
      block.append(cards);
      const relations=element("details","chat-source-relations");
      relations.append(element("summary","","Code structures containing related fields"));
      const lines=element("ul","chat-questions");
      signals.object_relationships.forEach(x=>lines.append(element("li","",x.label+": "+x.count+" object literals")));
      signals.function_relationships.forEach(x=>lines.append(element("li","",x.label+": "+x.count+" function scopes")));
      relations.append(lines);block.append(relations);
      section.append(block);

      const dom=signals.dom_controls;
      if(dom){
        const block=element("div","chat-subsection");
        block.append(element("h3","","Controls found in the saved page"));
        block.append(element("p","graph-caption",
          "The composer has one editable textbox. Main-region edit and regeneration labels were found, but their click results were not recorded."));
        const listing=element("div","chat-signals");
        dom.features.forEach(item=>{
          const card=element("div","chat-source-card");
          card.append(element("strong","",item.count),
            element("small","",item.category.replaceAll("_"," ")+" · "+item.nearest_region));
          listing.append(card);
        });
        block.append(listing,element("p","graph-caption",dom.caveat));
        section.append(block);
      }
    }
    const research=record.visuals?.feature_research;
    if(research){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Chat research backlog"));
      const counts={done:0,queued:0,requires_new_evidence:0};
      research.tasks.forEach(t=>{counts[t.status]=(counts[t.status]||0)+1;});
      block.append(element("p","graph-caption",
        counts.done+" tasks completed · "+counts.queued+" offline tasks open · "+
        counts.requires_new_evidence+" tasks requiring new runtime evidence."));
      const groups=element("div","chat-research-list");
      const protocols=new Map((research.protocols||[]).map(p=>[p.task_id,p]));
      research.tasks.forEach(t=>{
        const row=element("details","chat-research-task");
        const header=element("summary","chat-research-head");
        header.append(element("strong","",t.title),
          element("small","",t.status==="requires_new_evidence"?"Needs new evidence":t.status==="done"?"Completed":"Queued"));
        row.append(header,element("p","",t.acceptance));
        const protocol=protocols.get(t.id);
        if(protocol){
          row.append(element("p","graph-caption","Proposed study, not performed: "+protocol.question));
          const distinctions=element("ul","");
          protocol.discriminators.forEach(x=>distinctions.append(element("li","",x)));
          row.append(element("p","graph-caption","Outcomes to distinguish:"),distinctions);
          row.append(element("p","graph-caption","Observation categories: "+protocol.observables.join(", ")));
          row.append(element("p","graph-caption","Stop boundary: "+protocol.stop_condition));
        }
        if(t.depends_on.length)row.append(element("p","graph-caption","Prerequisites: "+t.depends_on.length));
        groups.append(row);
      });
      block.append(groups);section.append(block);
    }

    const surface=element("div","chat-surface-list");
    feature.surfaces.forEach(item=>{
      const node=add(element("div","chat-surface"),
        element("strong","",item.label),
        element("small","",item.basis==="observed_static"?"Observed HTML":"Not verified"),
        element("p","",item.description));
      surface.append(node);
    });
    section.append(add(element("div","chat-subsection"),element("h3","","Observed page regions"),surface));
    if(feature.domain_relations?.length){
      const domain=element("div","chat-subsection");
      domain.append(element("h3","","Candidate message data relationships"));
      domain.append(element("p","graph-caption",
        "Typed entity links for coding and testing. All edges are hypotheses; source clues do not verify their runtime meaning."));
      const list=element("div","chat-domain-links");
      feature.domain_relations.forEach(relation=>{
        const detail=element("details","chat-domain-edge");
        const title=element("summary","",relation.from+" → "+relation.predicate.replaceAll("_"," ")+" → "+relation.to);
        detail.append(title,element("p","",
          "Possible multiplicity: "+relation.multiplicity.replaceAll("_"," ")+". Status: "+relation.evidence_status+"."));
        detail.append(element("p","graph-caption","How to verify: "+relation.verify));
        list.append(detail);
      });
      domain.append(list);section.append(domain);
      section.append(renderSyntheticExample());
    }
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
