/* UNIVER WORKBENCH — custom narration-led animation, deterministic at any frame. */
(function(){'use strict';const D=window.DATA,stage=document.getElementById('stage');
const E=(tag,cls,p,text)=>{let x=document.createElement(tag);x.className=cls||'';if(text!=null)x.textContent=text;if(p)p.appendChild(x);return x};
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>1-Math.pow(1-clamp(x),3),p=(t,a,d=.5)=>ease((t-a)/d);
function sheet(parent,cls){let s=E('div','u-sheet '+(cls||''),parent);s.innerHTML='<div class="sheet-toolbar"><span class="brand-symbol">✳</span><b>MY WORKSPACE</b><div class="toolbar-actions">↶ &nbsp; B &nbsp; I &nbsp; ≡ &nbsp; ▦</div></div><div class="sheet-formula"><span>fx</span><b>=SUM(B2:B4)</b><i>90</i></div><div class="sheet-grid"><div class="gridcorner"></div><div class="col">A</div><div class="col">B</div><div class="col">C</div><div class="col">D</div><div class="row">1</div><div class="cell label">ITEM</div><div class="cell label">VALUE</div><div class="cell label">TEAM</div><div class="cell label">STATUS</div><div class="row">2</div><div class="cell">Design</div><div class="cell v">40</div><div class="cell">North</div><div class="cell green">Done</div><div class="row">3</div><div class="cell">Build</div><div class="cell v">30</div><div class="cell">East</div><div class="cell yellow">Review</div><div class="row">4</div><div class="cell">Launch</div><div class="cell v">20</div><div class="cell">West</div><div class="cell green">Done</div><div class="row">5</div><div class="cell total">TOTAL</div><div class="cell total value-total">90</div><div class="cell"></div><div class="cell"></div></div><div class="sheet-tab"><b>Sheet 1</b><span>＋</span></div>';return s}
function header(root,idx,title,subtitle){let x=E('div','u-header',root);E('div','u-kicker',x,'UNIVER OFFICE SDK   /   '+idx);E('div','u-title',x,title);E('div','u-sub',x,subtitle);return x}
function make(s){let r=E('div','scene',stage);r.style.display='none';let bg=E('div','u-bg',r);bg.setAttribute('data-house-camera','');let o={root:r, parts:[],animations:[]};let add=x=>{o.parts.push(x);return x};if(s.archetype==='endcard')return o;
 if(s.archetype==='uni_hook'){
  header(r,'01','BUILD YOUR OWN\nAI OFFICE','SHEETS + DOCS  ·  YOUR APP');
  let zone=E('div','hook-zone',r);let ring=E('div','hook-ring',zone);ring.innerHTML='<i></i><i></i><i></i>';o.ring=ring;
  let sh=sheet(zone,'hook-sheet');o.hooksheet=sh;
  let doc=add(E('div','hook-doc',zone));doc.innerHTML='<div class="doc-chip">DOC</div><strong>Project plan</strong><i></i><i></i><i></i><i></i><b>✓ &nbsp; Ready to edit</b>';
  let agent=add(E('div','hook-agent',zone));agent.innerHTML='<span>✦</span><b>AI AGENT</b>';
  let badge=add(E('div','hook-badge',zone));badge.innerHTML='<span>✳</span> UNIVER <small>OFFICE SDK</small>';
  o.parts=[agent,badge,doc];
  let proof=E('div','official-proof',r);proof.innerHTML='<span>OFFICIAL UNIVER REPOSITORY</span>';let im=E('img','',proof);im.src=s.evidence_data;im.alt='Official Univer Office SDK repository banner';
  E('div','u-foot',r,'ILLUSTRATIVE INTERFACE  ·  NOT A LIVE DEMO');
 }
 if(s.archetype==='uni_sheet'){
  header(r,'02','SHEETS + DOCS,\nBUILT IN','A STARTING POINT FOR YOUR PRODUCT');
  let zone=E('div','sheet-zone',r);o.board=sheet(zone,'feature-sheet');
  let h1=add(E('div','cell-highlight edit-highlight',zone));h1.innerHTML='<span>EDITABLE</span>';
  let h2=add(E('div','formula-callout',zone));h2.innerHTML='<b>ƒx</b><span>FORMULAS</span><strong>40 + 30 + 20 = 90</strong>';
  let h3=add(E('div','sort-callout',zone));h3.innerHTML='<b>↓</b><span>SORT</span>';
  let h4=add(E('div','document-strip',zone));h4.innerHTML='<span class="doc-mark">▤</span><div><b>DOCUMENTS</b><small>Rich text and formatting</small></div><span class="doc-lines">━━<br>━━━━</span>';
  E('div','u-foot',r,'EXAMPLE VALUES ARE ILLUSTRATIVE');
 }
 if(s.archetype==='uni_plugin'){
  header(r,'03','PLUG IN.\nCONNECT. BUILD.','CHOOSE THE COMPONENTS YOUR APP NEEDS');
  let z=E('div','plugin-zone',r);let socket=E('div','socket',z);socket.innerHTML='<div class="socket-head"><span>YOUR APP</span><b>◆</b></div><div class="socket-line">OFFICE WORKSPACE</div><div class="socket-ports"><i></i><i></i><i></i></div>';
  [['▦','SHEETS','mint'],['▤','DOCS','violet'],['ƒx','FORMULAS','orange']].forEach(v=>{let k=add(E('div','plug '+v[2],z));k.innerHTML='<span>'+v[0]+'</span><b>'+v[1]+'</b>'});
  let link=E('div','plugin-link',z);link.innerHTML='<span></span>';o.link=link;
  let ai=add(E('div','plugin-agent',z));ai.innerHTML='<span>✦</span><div><small>YOUR</small><b>AI AGENT</b></div>';
  let api=add(E('div','api-label',z));api.innerHTML='FACADE API <span>↔</span>';
  E('div','u-foot',r,'CONCEPTUAL ARCHITECTURE  ·  PLUGINS + APIS');
 }
 if(s.archetype==='uni_agent'){
  header(r,'04','PEOPLE + AGENTS','ONE WORKSPACE. YOUR APP IN CONTROL.');
  let z=E('div','agent-zone',r);let sh=sheet(z,'agent-sheet');o.agentSheet=sh;
  let agent=add(E('div','actor actor-ai',z));agent.innerHTML='<div>✦</div><b>AI AGENT</b><small>YOUR INTEGRATION</small>';
  let cells=add(E('div','agent-edit',z));cells.innerHTML='<span>✦</span> EDIT CONTENT';
  let person=add(E('div','actor actor-person',z));person.innerHTML='<div>●</div><b>PERSON</b><small>YOUR INTERFACE</small>';
  let edits=add(E('div','person-edit',z));edits.innerHTML='<span>↗</span> EDIT SHEET';
  let paths=E('div','agent-paths',z);paths.innerHTML='<svg viewBox="0 0 900 600"><path d="M188 70 C250 145 300 145 343 210"/><path d="M722 70 C660 145 610 145 560 210"/></svg>';o.paths=paths;
  E('div','u-foot',r,'CONCEPTUAL EXAMPLE  ·  YOUR AGENT + YOUR APP');
 }
 if(s.archetype==='uni_scope'){
  header(r,'05','KNOW THE\nBOUNDARIES','WHAT IS INCLUDED — AND WHAT YOU BRING');let z=E('div','scope-zone',r);
  let core=E('div','scope-core',z);core.innerHTML='<div class="scope-icon">✳</div><div><small>OPEN-SOURCE CORE</small><b>SHEETS + DOCS</b><span>Editing, formulas, plugins, APIs</span></div><div class="scope-tag">CORE</div>';
  let ext=add(E('div','scope-extension',z));ext.innerHTML='<div class="scope-icon">＋</div><div><small>SEPARATELY LICENSED</small><b>ADVANCED FEATURES</b><span>Collaboration + some AI extensions</span></div><div class="scope-tag">EXTENSIONS</div>';
  let model=add(E('div','scope-model',z));model.innerHTML='<div class="scope-icon">✦</div><div><small>YOU PROVIDE</small><b>MODEL + ORCHESTRATION</b><span>Connect your existing agent</span></div><div class="scope-tag">YOUR STACK</div>';
  E('div','u-foot',r,'CHECK CURRENT FEATURE + LICENSING DETAILS');
 }
 o.times=window.HouseMotion.cueTimes((s.payload||{}).cue_phrases||[],s,o.parts.length,{});return o}
D.scenes.forEach(s=>s._uni=make(s));window.setTime=function(t){let s=D.scenes.find(x=>t>=x.t0&&t<x.t1)||D.scenes[D.scenes.length-1];D.scenes.forEach(x=>x._uni.root.style.display=x===s?'block':'none');let o=s._uni;if(s.archetype==='endcard'){o.root.style.display='none';return}let q=p(t,s.t0,.30);o.root.style.opacity=String(.85+.15*q);o.root.style.transform=`translateY(${(1-q)*12}px)`;o.parts.forEach((x,i)=>{let v=p(t,o.times[i]??s.t0,.42);x.style.opacity=String(v);x.style.transform=`translateY(${(1-v)*24}px) scale(${.94+.06*v})`});let rel=clamp((t-s.t0)/(s.t1-s.t0));if(o.ring)o.ring.style.transform=`rotate(${rel*24}deg)`;if(o.hooksheet)o.hooksheet.style.transform=`rotate(-4deg) translateY(${-8*Math.sin(rel*3)}px)`;if(o.link){let v=p(t,o.times[2]??s.t0,.6);o.link.style.transform=`scaleY(${v})`}if(o.paths)o.paths.style.opacity=String(p(t,s.t0+.1,.6));};window.ready=true;
})();
