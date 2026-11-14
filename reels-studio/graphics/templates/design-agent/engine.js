/* Design Agent: editorial brand-studio storyboard, not a product UI recording. */
(function(){'use strict';
 const D=window.DATA,stage=document.getElementById('stage');
 const el=(tag,cls,parent,text)=>{let x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;if(parent)parent.appendChild(x);return x;};
 const C=(s,n)=>window.HouseMotion.cueTimes((s.payload||{}).cue_phrases,s,n,{});
 function animate(e,t,at,rotation){let v=Math.max(0,Math.min(1,(t-at)/.5)),k=1-Math.pow(1-v,3);e.style.opacity=k;e.style.transform=`translateY(${(1-k)*36}px) rotate(${(rotation||0)*(1-k)}deg)`;}
 function heading(root,k,t){let h=el('header','da-header',root);el('div','da-kicker',h,k);el('div','da-headline',h,t);}
 function asset(parent,label,num){let n=el('div','da-asset asset-'+num,parent);el('div','da-asset-shape shape-'+num,n);el('div','da-asset-name',n,label);return n;}
 function build(s){let r={root:el('div','scene da-scene',stage),parts:[],times:[]},p=s.payload||{},root=r.root;root.dataset.scene=s.id;root.style.display='none';
  if(s.archetype==='endcard'){el('div','house-endcard-host',root);return r;}
  if(s.archetype==='title_burst'){
    heading(root,'LANGCHAIN  /  DESIGN AGENT',s.headline);let brief=el('div','da-message',root);el('div','da-msg-label',brief,'ILLUSTRATED REQUEST');el('div','da-msg-text',brief,'Make a launch video\nin our brand.');let art=el('div','da-artboard',root);el('div','da-art-label',art,'BRAND ARTBOARD');asset(art,'MOTION',2);el('div','da-caption-note',root,'SCHEMATIC · NOT A SLACK RECORDING');r.parts=[brief,art];r.times=[s.t0+.1,s.t0+1.5];
  }else if(s.archetype==='brand_inputs'){
    heading(root,'01  /  BRAND SYSTEM',s.headline);let board=el('div','da-brand-board',root);let a=el('div','da-swatches',board);['#3a4eeb','#f28774','#f1c84b'].forEach(c=>{let x=el('i','',a);x.style.background=c;});el('b','',a,'COLOR');let b=el('div','da-type',board);el('strong','',b,'Aa');el('b','',b,'TYPE');let c=el('div','da-grid-unit',board);for(let i=0;i<16;i++)el('i','',c);el('b','',c,'SPACING');let out=el('div','da-output',root);(p.outputs||[]).forEach((v,i)=>r.parts.push(asset(out,v,i)));r.parts=[a,b,c,...r.parts];r.times=C(s,6);
  }else if(s.archetype==='design_process'){
    heading(root,'02  /  REQUEST TO DELIVERABLE',s.headline);let flow=el('div','da-flow',root);(p.items||[]).forEach((item,i)=>{let row=el('div','da-flow-row',flow);el('span','da-number',row,'0'+(i+1));let body=el('div','da-flow-body',row);el('b','',body,item.title);el('small','',body,item.sub);r.parts.push(row)});r.times=C(s,3);
  }else if(s.archetype==='proof_chart'){
    heading(root,'03  /  LANGCHAIN REPORTS',s.headline);let fig=el('div','da-proof',root);let count=el('div','da-count',fig);el('strong','',count,'3,000+');el('small','',count,'INTERNAL ASSETS');let chart=el('div','da-chart',fig);el('div','da-chart-label',chart,'MEDIAN MODEL SPEND PER REQUEST');let bars=el('div','da-bars',chart);let a=el('div','da-bar before',bars);a.style.width='100%';el('b','',a,'$'+p.before);let b=el('div','da-after-group',bars);let small=el('div','da-bar after',b);small.style.width=(100*p.after/p.before)+'%';el('b','da-after-label',b,'$'+Number(p.after).toFixed(2));el('div','da-chart-note',fig,'HISTORICAL VENDOR FIGURES · NOT TOTAL COST');r.parts=[count,a,b];r.times=C(s,3);
  }else{
    heading(root,'04  /  THE REAL-WORLD CHECK',s.headline);let sheet=el('div','da-review-sheet',root);let rows=p.rows||[];rows.forEach((x,i)=>{let z=el('div','da-check-row',sheet);el('div','da-check-icon',z,i===0?'↗':i===1?'$':'✓');let body=el('div','da-check-body',z);el('b','',body,x.t||'');el('small','',body,x.sub||'');r.parts.push(z)});r.times=C(s,r.parts.length);
  }return r;
 }
 D.scenes.forEach((s,i)=>{s.idx=i;s._da=build(s);});window.setTime=function(t){let s=D.scenes.find(x=>t>=x.t0&&t<x.t1)||D.scenes[D.scenes.length-1];D.scenes.forEach(x=>x._da.root.style.display=x===s?'block':'none');if(s.archetype==='endcard'){s._da.root.style.display='none';return;}s._da.parts.forEach((x,i)=>animate(x,t,s._da.times[i]??s.t0+i*.3,(i%2?2:-2)));};window.ready=true;
})();
