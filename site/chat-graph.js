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
    const lifecycle=record.visuals?.chat_end_to_end_trace;
    if(lifecycle){
      const block=element("div","chat-subsection");
      block.append(element("h3","","End-to-end captured client lifecycle"));
      block.append(element("p","graph-caption",
        "Source-composed flow. Direct calls, callbacks and state dependencies are distinguished; no live session or server outcome is verified."));
      const stages=element("ol","chat-lifecycle-stages");
      lifecycle.stages.forEach(stage=>{
        const item=element("li","chat-lifecycle-stage");
        item.append(element("strong","",stage.id.replaceAll("_"," ")),
          element("p","",stage.behavior),
          element("small","",stage.source_refs.join(", ")+" · "+
            stage.evidence_refs.join(", ")));
        stages.append(item);
      });
      block.append(stages);
      const edges=element("details","chat-lifecycle-edges");
      edges.append(element("summary","","Evidence-graded source connections"));
      const edgeList=element("ol","");
      lifecycle.connections.forEach(link=>edgeList.append(element("li","",
        link.from.replaceAll("_"," ")+" → "+link.to.replaceAll("_"," ")+
        " ["+link.kind.replaceAll("_"," ")+"]: "+link.limits)));
      edges.append(edgeList);block.append(edges);
      const variants=element("details","chat-lifecycle-alternatives");
      variants.append(element("summary","","Alternative client paths"));
      const alts=element("ul","");
      lifecycle.alternatives.forEach(x=>alts.append(element("li","",
        x.name.replaceAll("_"," ")+": "+x.behavior)));
      variants.append(alts);block.append(variants);
      section.append(block);
    }
    const cssHooks=record.visuals?.chat_css_hooks;
    if(cssHooks){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Captured styling and DOM hook evidence"));
      block.append(element("p","graph-caption",
        cssHooks.stylesheets+" saved stylesheets; lexical CSS syntax counts, not computed browser styles."));
      const metrics=element("div","chat-css-metrics");
      cssHooks.metrics.forEach(x=>{
        const card=element("div","chat-css-stat");
        card.append(element("strong","",String(x.count)),
          element("small","",x.label));
        metrics.append(card);
      });
      block.append(metrics);
      const gaps=element("details","chat-css-limits");
      gaps.append(element("summary","","DOM attribution selectors and unresolved ownership"));
      const findings=element("ul","");
      cssHooks.conclusions.forEach(x=>findings.append(element("li","",x)));
      const absent=cssHooks.unmatched_attribution.filter(x=>x.count===0);
      findings.append(element("li","",
        absent.length+" exact message/turn attribution selector families absent as literal CSS selectors. This does not imply messages are unstyled."));
      gaps.append(findings);
      const remain=element("ul","");
      cssHooks.unverified.forEach(x=>remain.append(element("li","",x)));
      gaps.append(element("p","graph-caption","Unresolved style ownership:"),remain);
      block.append(gaps);section.append(block);
    }
    const clientCache=record.visuals?.chat_persistence_cache;
    if(clientCache){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Browser-local conversation caches — captured client"));
      block.append(element("p","graph-caption",
        "Versioned list/pinned metadata, query-cache updates and snapshot-worker lifecycle. No executed storage write, server durability or cross-tab synchronization verified."));
      const stages=element("div","chat-cache-stages");
      clientCache.stages.forEach(stage=>{
        const panel=element("details","chat-cache-stage");
        panel.append(element("summary","",stage.id.replaceAll("_"," ")),
          element("p","",stage.description));
        stages.append(panel);
      });
      block.append(stages);
      const limits=element("details","chat-cache-limits");
      limits.append(element("summary","","Cache boundaries and unresolved behavior"),
        element("p","graph-caption",clientCache.cross_tab_boundary));
      const items=element("ul","");
      clientCache.unverified.forEach(line=>items.append(element("li","",line)));
      limits.append(items);block.append(limits);section.append(block);
    }
    const branchStudy=record.visuals?.chat_branch_switch;
    if(branchStudy){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Response version switching — client source"));
      block.append(element("p","graph-caption",
        "Previous/next controls, optimistic selected-node updates and failure rollback. A real server response was not observed."));
      const steps=element("div","chat-branch-stages");
      branchStudy.stages.forEach((stage,index)=>{
        const row=element("details","chat-branch-stage");
        row.append(element("summary","",(index+1)+". "+stage.id.replaceAll("_"," ")),
          element("p","",stage.description),
          element("p","graph-caption","Captured source: "+stage.source_ref));
        steps.append(row);
      });
      block.append(steps);
      const link=element("details","chat-branch-render-link");
      link.append(element("summary","","How selection feeds transcript preparation"),
        element("p","",branchStudy.render_recomputation_link.description),
        element("p","graph-caption",branchStudy.render_recomputation_link.boundary));
      block.append(link);
      const derivation=element("details","chat-branch-derivation");
      derivation.append(element("summary","","How selectable response versions are derived"));
      const derivationList=element("ol","");
      branchStudy.variant_derivation.forEach(item=>derivationList.append(
        element("li","",item.id.replaceAll("_"," ")+": "+item.behavior)));
      derivation.append(derivationList,element("p","graph-caption",
        branchStudy.variant_derivation_limits));
      block.append(derivation);
      const caveats=element("details","chat-branch-caveats");
      caveats.append(element("summary","","Selection and persistence limits"));
      const list=element("ul","");
      branchStudy.caveats.forEach(item=>list.append(element("li","",item)));
      caveats.append(list);
      block.append(caveats);
      section.append(block);
    }
    const transcript=record.visuals?.chat_transcript_render_trace;
    if(transcript){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Transcript turn and message rendering — saved source"));
      block.append(element("p","graph-caption",
        "Source-backed turn derivation and typed item presentation. The website's actual runtime render was not observed."));
      const stages=element("div","chat-transcript-stages");
      transcript.stages.forEach((step,i)=>{
        const panel=element("details","chat-transcript-stage");
        panel.append(element("summary","",(i+1)+". "+step.id.replaceAll("_"," ")),
          element("p","",step.description),
          element("p","graph-caption","Captured source: "+step.source_ref));
        stages.append(panel);
      });
      block.append(stages);
      const edges=element("details","chat-transcript-edges");
      edges.append(element("summary","","Reviewed transcript source relationships"));
      const list=element("ol","");
      transcript.relationships.forEach(link=>list.append(element("li","",
        link.from.replaceAll("_"," ")+" → "+link.to.replaceAll("_"," ")+
        " ("+link.kind.replaceAll("_"," ")+")")));
      edges.append(list);
      block.append(edges);
      const moduleCall=element("details","chat-transcript-import");
      moduleCall.append(element("summary","","Verified turn renderer import"),
        element("p","",transcript.cross_module_call.behavior),
        element("p","graph-caption",
          transcript.cross_module_call.source_ref+" → "+transcript.cross_module_call.target_ref+
          ". "+transcript.cross_module_call.boundary));
      block.append(moduleCall);
      const dependencies=element("details","chat-transcript-dependencies");
      dependencies.append(element("summary","","Selected-node and mapping recomputation"));
      const depList=element("ul","");
      transcript.page_recomputation.observations.forEach(item=>{
        depList.append(element("li","",item));
      });
      dependencies.append(depList,element("p","graph-caption",
        "Memoization inputs: "+transcript.page_recomputation.dependency_roles.join(", ")),
        element("p","graph-caption",transcript.page_recomputation.boundary));
      block.append(dependencies);
      const rules=element("details","chat-transcript-rules");
      rules.append(element("summary","","Reviewed presentation and filtering rules"));
      const ruleList=element("div","chat-transcript-rule-list");
      transcript.presentation_rules.forEach(rule=>{
        const item=element("div","chat-transcript-rule");
        item.append(element("strong","",rule.id.replaceAll("_"," ")),
          element("p","",rule.description),
          element("small","",rule.source_ref+" · "+rule.classification.replaceAll("_"," ")));
        ruleList.append(item);
      });
      rules.append(ruleList,element("p","graph-caption",transcript.rule_limitations.join(" ")));
      block.append(rules);
      const actions=element("details","chat-transcript-actions");
      actions.append(element("summary","","Edit, regenerate and fork callback gates"));
      const actionList=element("ul","");
      transcript.action_bindings.forEach(row=>actionList.append(
        element("li","",row.action.replaceAll("_"," ")+": "+row.gates+" "+row.limits)));
      actions.append(actionList);
      block.append(actions);
      const limits=element("details","chat-transcript-limits");
      limits.append(element("summary","","Still unresolved"));
      const questions=element("ul","");
      transcript.unverified.forEach(note=>questions.append(element("li","",note)));
      limits.append(questions);
      block.append(limits);
      section.append(block);
    }
    const moduleGraph=record.visuals?.chat_module_dependency;
    if(moduleGraph){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Anonymous saved-module dependency graph"));
      block.append(element("p","graph-caption",
        "Module registries and static import candidates across the original JavaScript dump. Module loading and execution were not observed."));
      const stats=element("div","chat-module-stats");
      [["Parsed bundles",moduleGraph.census.parsed_bundles],
       ["Modules",moduleGraph.census.module_registry_entries],
       ["Resolved import candidates",moduleGraph.census.uniquely_resolved_import_candidates],
       ["Ambiguous",moduleGraph.census.ambiguous_import_candidates]].forEach(([name,value])=>{
          const cell=element("div","chat-module-stat");
          cell.append(element("strong","",String(value)),element("small","",name));
          stats.append(cell);
       });
      block.append(stats);
      const links=element("details","chat-module-links");
      links.append(element("summary","","Four reviewed capture-local module links"));
      const list=element("ul","");
      moduleGraph.edges.forEach(edge=>list.append(element("li","",
        edge.from_ref+" #"+edge.from_module+" → "+edge.to_ref+" #"+edge.to_module+
        " · "+edge.role)));
      links.append(list);
      block.append(links);
      const limits=element("details","chat-module-limits");
      limits.append(element("summary","","Import graph limitations"));
      const details=element("ul","");
      moduleGraph.limitations.forEach(note=>details.append(element("li","",note)));
      limits.append(details);
      block.append(limits);
      section.append(block);
    }
    const accessibility=record.visuals?.chat_accessibility_trace;
    if(accessibility){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Accessible conversation navigation — client source"));
      block.append(element("p","graph-caption",
        "Screen-reader-only landmark, abortable focus navigation, pagination status and polite completion announcement; no assistive-technology behavior tested."));
      const items=element("div","chat-a11y-grid");
      accessibility.mechanisms.forEach((m,i)=>{
        const row=element("details","chat-a11y-mechanism");
        row.append(element("summary","",(i+1)+". "+m.id.replaceAll("_"," ")),
          element("p","",m.description),
          element("p","graph-caption",m.source_ref+" · "+m.kind.replaceAll("_"," ")));
        items.append(row);
      });
      block.append(items);
      const anchors=element("p","graph-caption",
        "Reviewed module anchors: "+accessibility.module_anchors.map(x=>
          x.source_ref+" #"+x.module_ordinal+" ("+x.role.replaceAll("_"," ")+")").join("; "));
      block.append(anchors);
      const limits=element("details","chat-a11y-limits");
      limits.append(element("summary","","Accessibility verification limits"));
      const list=element("ul","");
      accessibility.limits.forEach(note=>list.append(element("li","",note)));
      limits.append(list);
      block.append(limits);
      section.append(block);
    }
    const editStudy=record.visuals?.chat_edit_submission_trace;
    if(editStudy){
      const block=element("div","chat-subsection");
      block.append(element("h3","","User-message editing — guarded source lifecycle"));
      block.append(element("p","graph-caption",
        "Source-reviewed target validation, active-response stop, replacement completion submission and cleanup. No live edit or server mutation was observed."));
      const steps=element("div","chat-edit-grid");
      editStudy.stages.forEach((stage,i)=>{
        const item=element("details","chat-edit-stage");
        item.append(element("summary","",(i+1)+". "+stage.id.replaceAll("_"," ")),
          element("p","",stage.behavior),
          element("p","graph-caption",stage.source_ref+" · "+stage.kind.replaceAll("_"," ")));
        steps.append(item);
      });
      block.append(steps);
      block.append(element("p","graph-caption",
        "Reviewed module anchors: "+editStudy.module_anchors.map(x=>
          x.source_ref+" #"+x.module_ordinal+" ("+x.role.replaceAll("_"," ")+")").join("; ")));
      const open=element("details","chat-edit-boundaries");
      open.append(element("summary","","Still unverified"));
      const list=element("ul","");
      editStudy.unverified.forEach(x=>list.append(element("li","",x)));
      open.append(list);
      block.append(open);
      section.append(block);
    }
    const selectionCopy=record.visuals?.chat_selection_copy_trace;
    if(selectionCopy){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Selected text and last code block — source actions"));
      block.append(element("p","graph-caption",
        "Archived client source validates selected Markdown ranges and supports a guarded last-code-block command. No live clipboard operation was observed."));
      function addPath(label,klass,steps){
        const details=element("details",klass);
        details.append(element("summary","",label));
        const list=element("ol","");
        steps.forEach(step=>list.append(element("li","",step.id.replaceAll("_"," ")+
          ": "+step.operation)));
        details.append(list);
        block.append(details);
      }
      addPath("Selected text validation and dispatch","chat-selection-stages",selectionCopy.selected_text);
      addPath("Last code block resolution and copy","chat-code-copy-stages",selectionCopy.last_code_block);
      const caveats=element("details","chat-selection-boundaries");
      caveats.append(element("summary","","Remaining verification boundaries"));
      const lines=element("ul","");
      selectionCopy.limitations.forEach(x=>lines.append(element("li","",x)));
      caveats.append(lines);
      block.append(caveats);
      section.append(block);
    }
    const viewport=record.visuals?.chat_virtual_viewport;
    if(viewport){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Virtualized transcript viewport and scroll anchoring"));
      block.append(element("p","graph-caption",
        "Recovered virtual turn range, measured layout, retained off-screen rows, and bottom-response spacer from captured client source. Browser scrolling not observed."));
      const sources=element("p","graph-caption",
        "Source resources: "+viewport.source_resources.join(", "));
      block.append(sources);
      block.append(element("p","graph-caption",
        viewport.ast_recheck.candidate_count+
        " syntax-level viewport signals across "+
        viewport.ast_recheck.module_count+
        " reviewed module anchors. These are candidate matches, not runtime proof."));
      const anchors=element("details","chat-viewport-anchors");
      anchors.append(element("summary","","Reviewed capture-local module anchors"));
      const anchorsList=element("ul","");
      viewport.module_anchors.forEach(module=>{
        anchorsList.append(element("li","",module.ref+
          " · module "+module.module_ordinal+" · "+module.role));
      });
      anchors.append(anchorsList,element("p","graph-caption",
        "Module ordinals are stable only within this saved capture and are not runtime IDs."));
      block.append(anchors);
      const rules=element("div","chat-viewport-rule-grid");
      viewport.windowing_rules.forEach(rule=>{
        const card=element("details","chat-viewport-rule");
        card.append(element("summary","",rule.id),
          element("p","",rule.behavior),
          element("p","graph-caption",rule.source_ref+" · "+rule.limits));
        rules.append(card);
      });
      block.append(rules);
      const edges=element("details","chat-viewport-links");
      edges.append(element("summary","","Verified viewport source relationships"));
      const paths=element("ol","");
      viewport.source_chain.forEach(edge=>{
        paths.append(element("li","",edge.from+" → "+edge.to+" ("+edge.kind+")"));
      });
      edges.append(paths,element("p","graph-caption",
        "Source imports and DOM preparation paths do not establish runtime scroll outcomes."));
      block.append(edges);
      const branchLink=element("details","chat-viewport-branch-link");
      branchLink.append(element("summary","","Response variant → turn window reconciliation"));
      const stages=element("ol","");
      viewport.branch_window.stages.forEach(item=>{
        stages.append(element("li","",item.role+": "+item.behavior+" ("+item.source_ref+")"));
      });
      branchLink.append(stages,element("p","graph-caption",
        "Source-level composition only: an actual branch switch or scroll movement has not been observed."));
      block.append(branchLink);
      const spacerLink=element("details","chat-viewport-spacer-link");
      spacerLink.append(element("summary","","Composer → response spacer lifecycle"));
      const spacerStages=element("ol","");
      viewport.composer_spacer.stages.forEach(item=>{
        spacerStages.append(element("li","",item.role+": "+item.behavior+" ("+item.source_ref+")"));
      });
      spacerLink.append(spacerStages,element("p","graph-caption",
        viewport.composer_spacer.boundaries.join(" ")));
      block.append(spacerLink);
      section.append(block);
    }
    const selectorStudy=record.visuals?.chat_selector_consumers;
    if(selectorStudy){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Selected-message selectors and client consumers"));
      block.append(element("p","graph-caption",
        "Two message ancestry selectors, one user-identity ancestry selector, and two feature-reference collections. Source-level subscribers, not verified live rendering."));
      const selectors=element("div","chat-selector-grid");
      selectorStudy.selectors.forEach(item=>{
        const panel=element("details","chat-selector-item");
        panel.append(element("summary","",item.id.replaceAll("_"," ")),
          element("p","",item.behavior),
          element("p","graph-caption",item.purpose));
        selectors.append(panel);
      });
      block.append(selectors);
      const links=element("details","chat-selector-consumers");
      links.append(element("summary","","Reviewed selector consumers"));
      const list=element("ul","");
      selectorStudy.consumers.forEach(item=>list.append(
        element("li","",item.selector_id.replaceAll("_"," ")+
          " → "+item.role+" ("+item.source_ref+"): "+item.behavior)));
      links.append(list,element("p","graph-caption",
        "UI subscriptions are source-confirmed; their runtime conditions and rendered results were not observed."));
      block.append(links);
      const actions=element("details","chat-selector-actions");
      actions.append(element("summary","","Captured React click dispatch"));
      actions.append(element("p","graph-caption",
        "Surfaces: "+selectorStudy.ui_action.surfaces.join(", ")+
        "; selector: "+selectorStudy.ui_action.selector));
      const routes=element("ul","");
      selectorStudy.ui_action.paths.forEach(route=>routes.append(
        element("li","",route.name.replaceAll("_"," ")+": "+route.behavior)));
      actions.append(routes,element("p","graph-caption",
        selectorStudy.ui_action.verification_boundary));
      block.append(actions);
      section.append(block);
    }
    const graphWrite=record.visuals?.chat_graph_mutation;
    if(graphWrite){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Message graph mutation: captured implementation"));
      block.append(element("p","graph-caption",
        "Source-backed parent/child linking and selected-node updates in "+
        graphWrite.source_ref+". The server model and live outcomes are unverified."));
      const operations=element("div","chat-mutation-grid");
      graphWrite.operations.forEach(item=>{
        const row=element("details","chat-mutation-operation");
        row.append(element("summary","",item.kind),
          element("p","",item.observation));
        operations.append(row);
      });
      block.append(operations);
      const graph=element("details","chat-mutation-callpath");
      graph.append(element("summary","","Recovered client call sequence"));
      const list=element("ol","");
      graphWrite.call_sequence.forEach(edge=>list.append(
        element("li","",edge.from+" → "+edge.to+" ("+edge.kind+")")));
      graph.append(list);
      block.append(graph);
      const projection=element("details","chat-mutation-projection");
      projection.append(element("summary","","Selected-message and ancestry projections"),
        element("p","",graphWrite.state_projection.behavior),
        element("p","graph-caption",
          "State roles: "+graphWrite.state_projection.field_roles.join(", ")),
        element("p","graph-caption",graphWrite.state_projection.limits));
      block.append(projection);
      section.append(block);
    }
    const transport=record.visuals?.chat_transport_trace;
    if(transport){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Completion transport: source-backed lifecycle"));
      block.append(element("p","graph-caption",
        "From saved JavaScript "+transport.source_ref+
        ". Static client code, not an observed server session."));
      const methods=element("div","chat-transport-grid");
      transport.methods.forEach(item=>{
        const row=element("details","chat-transport-method");
        row.append(element("summary","",item.method),
          element("p","",item.behavior),
          element("p","graph-caption",item.verification_boundary));
        methods.append(row);
      });
      block.append(methods);
      const bridge=element("details","chat-transport-bridge");
      bridge.append(element("summary","","Generation → stream service bridge"),
        element("p","",transport.generation_bridge.behavior),
        element("p","graph-caption",
          "Generation function "+transport.generation_bridge.caller_function_ordinal+
          " → "+transport.generation_bridge.callee_method+
          "; callbacks: "+transport.generation_bridge.callbacks.join(", ")+
          "; recovery inputs: "+transport.generation_bridge.recovery_inputs.join(", ")));
      block.append(bridge);
      const decode=element("details","chat-transport-decode");
      decode.append(element("summary","","Decoded events → message updates"));
      const steps=element("ol","");
      transport.decoded_pipeline.sequence.forEach(item=>{
        steps.append(element("li","",item.stage+": "+item.relationship));
      });
      decode.append(steps,element("p","graph-caption",
        transport.decoded_pipeline.verification_boundary));
      block.append(decode);
      const mutation=element("details","chat-transport-mutation");
      mutation.append(element("summary","","Decoded messages → client-state mutation"));
      const stages=element("ol","");
      transport.message_state_write.source_steps.forEach(item=>{
        stages.append(element("li","",item.stage+": "+item.detail));
      });
      mutation.append(stages,element("p","graph-caption",
        "Writer arguments: "+transport.message_state_write.writer_argument_roles.join(", ")),
        element("p","graph-caption",transport.message_state_write.limitations));
      block.append(mutation);
      const flow=element("details","chat-transport-edges");
      flow.append(element("summary","","Reviewed client-side transport relationships"));
      const rows=element("ul","");
      transport.static_edges.forEach(item=>{
        rows.append(element("li","",item.from+" → "+item.to+
          " ("+item.kind.replaceAll("_"," ")+")"));
      });
      flow.append(rows,element("p","graph-caption",
        "Conditional pathways are alternatives visible in the source; no server outcome is inferred."));
      block.append(flow);
      const ws=element("details","chat-transport-websocket");
      ws.append(element("summary","","WebSocket stream-item validation"),
        element("p","",transport.websocket_item_behavior));
      block.append(ws);
      section.append(block);
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
      const exportsInfo=element("details","chat-implementation-exports");
      exportsInfo.append(element("summary","","Module export relationships"));
      const exportList=element("ul","");
      implTrace.reviewed_module_exports.forEach(item=>{
        exportList.append(element("li","",item.source_ref+" / function "+
          item.exported_function_ordinal+": "+item.meaning));
      });
      exportsInfo.append(exportList,element("p","graph-caption",
        "Export bindings do not establish which consumers executed."));
      block.append(exportsInfo);
      const direct=element("details","chat-implementation-direct-calls");
      direct.append(element("summary","","Verified source-level function calls"));
      const edges=element("ul","");
      implTrace.direct_calls.forEach(link=>edges.append(element("li","",
        link.source_ref+" / "+link.role+": function "+link.caller+
        " → function "+link.callee)));
      direct.append(edges,element("p","graph-caption",
        implTrace.direct_calls.length+" reviewed direct calls among "+implTrace.direct_call_candidate_count+
        " source-local candidates; "+implTrace.unreviewed_direct_call_count+
        " require inspection. No actual execution or server result is verified."));
      block.append(direct);
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
    const sourceQueue=record.visuals?.static_source_queue;
    if(sourceQueue){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Automatic static-source research queue"));
      const count=sourceQueue.task_statuses;
      block.append(element("p","graph-caption",
        sourceQueue.task_count+" tasks generated from captured source: "+
        (count.done||0)+" complete, "+(count.in_progress||0)+" in progress, "+
        (count.queued||0)+" queued. This work uses saved JavaScript, not live account access."));
      const started=(count.in_progress||0)+(count.done||0);
      const accepted=count.done||0;
      const progress=element("progress","chat-static-progress");
      progress.max=sourceQueue.task_count;
      progress.value=started;
      progress.setAttribute("aria-label","Static source research tasks started, not completed");
      block.append(progress,element("p","graph-caption",
        Math.round(100*started/sourceQueue.task_count)+"% started · "+
        Math.round(100*accepted/sourceQueue.task_count)+
        "% accepted complete. Partial evidence does not close a task."));
      const grouped=element("div","chat-static-task-list");
      sourceQueue.tasks.forEach(task=>{
        const row=element("details","chat-static-task");
        row.append(element("summary","",task.title),
          element("p","graph-caption",
            "Area: "+task.queue+" · Status: "+task.status+
            " · Dependencies: "+task.dependency_count+
            " · Evidence findings: "+task.evidence_count));
        grouped.append(row);
      });
      block.append(grouped);section.append(block);
    }
    const research=record.visuals?.feature_research;
    if(research){
      const block=element("div","chat-subsection");
      block.append(element("h3","","Optional runtime and completed research backlog"));
      const counts={done:0,queued:0,requires_new_evidence:0};
      research.tasks.forEach(t=>{counts[t.status]=(counts[t.status]||0)+1;});
      block.append(element("p","graph-caption",
        counts.done+" tasks completed · "+counts.queued+" offline tasks open · "+
        counts.requires_new_evidence+" optional live-verification proposals (not blockers to static analysis)."));
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
