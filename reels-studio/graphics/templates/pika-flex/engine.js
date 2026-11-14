/* Pika H3 Flex: a reference-to-video lightbox. Illustrations, not product footage. */
(function () {
  'use strict';
  const D=window.DATA, stage=document.getElementById('stage');
  const E=(tag,cls,parent,text)=>{let n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;if(parent)parent.appendChild(n);return n;};
  const clamp=x=>Math.max(0,Math.min(1,x));
  const cue=(s,n)=>window.HouseMotion.cueTimes((s.payload||{}).cue_phrases,s,n,{});
  function reveal(e,t,at,dx=0,dy=30){let p=1-Math.pow(1-clamp((t-at)/.48),3);e.style.opacity=p;e.style.transform=`translate(${(1-p)*dx}px,${(1-p)*dy}px)`;}
  function waveform(parent,variant){let w=E('div','pk-wave '+(variant||''),parent);for(let i=0;i<46;i++){let b=E('i','',w);b.style.height=(9+Math.abs(Math.sin(i*1.37)+.45*Math.sin(i*.42))*50)+'px';}return w;}
  function thumbnail(parent,label,variant){let box=E('div','pk-thumb '+variant,parent);E('div','pk-thumb-label',box,label);E('div','pk-sun',box);E('div','pk-hill one',box);E('div','pk-hill two',box);return box;}
  function film(parent){let f=E('div','pk-film',parent);for(let i=0;i<3;i++){let cell=E('div','pk-film-cell',f);let art=E('div','pk-art art'+i,cell);E('i','pk-art-sun',art);E('i','pk-art-land',art);}return f;}
  function label(root,k,h){let x=E('div','pk-top',root);E('div','pk-eyebrow',x,k);E('div','pk-headline',x,h);}
  function build(s){let root=E('div','scene pk-scene',stage);root.dataset.scene=s.id;root.style.display='none';let r={root,parts:[],times:[]},p=s.payload||{};
    if(s.archetype==='endcard'){E('div','house-endcard-host',root);return r;}
    if(s.archetype==='title_burst'){
      label(root,'PIKA H3 FLEX  /  REFERENCE-TO-VIDEO','FROM REFERENCES\nTO A SHOT');
      let board=E('div','pk-hook-board',root); thumbnail(board,'IMAGE REFERENCE','a');let a=E('div','pk-audio-ref',board);E('span','',a,'AUDIO REFERENCE');waveform(a);E('div','pk-connect',board,'↘');let preview=E('div','pk-hook-result',root);E('div','pk-result-title',preview,'GENERATED VIDEO');film(preview);E('div','pk-disclaimer',root,'CONCEPT ILLUSTRATION · NOT PRODUCT FOOTAGE');r.parts=[board,preview];r.times=[s.t0+.15,s.t0+1.35];
    } else if(s.archetype==='spec_plates' && s.idx===1){
      label(root,'INPUTS  /  UP TO 12 TOTAL',s.headline);let area=E('div','pk-inputs',root);
      let a=thumbnail(area,'IMAGES','a'),b=thumbnail(area,'VIDEO','b'),c=E('div','pk-input-audio',area);E('span','',c,'AUDIO');waveform(c);E('div','pk-input-note',root,'AT LEAST ONE IMAGE OR VIDEO');r.parts=[a,b,c];r.times=cue(s,3);
    } else if(s.archetype==='design_process'){
      label(root,'REFERENCE-GUIDED GENERATION',s.headline);let canvas=E('div','pk-proof-frame',root);if(!s.evidence_data)throw new Error('Pika product evidence missing');let img=E('img','pk-proof-image',canvas);img.src=s.evidence_data;img.alt='Pika reference-to-video playground';E('div','pk-proof-credit',root,'PIKA API PLAYGROUND · OFFICIAL EXAMPLE');let note=E('div','pk-note',root,'RESULTS VARY · NOT A FULL EDITABLE TIMELINE');r.parts=[canvas,note];r.times=[s.t0+.1,(cue(s,3))[2]];
    } else if(s.archetype==='spec_plates'){
      label(root,'HOSTED AUDIO SEPARATION',s.headline);let rack=E('div','pk-track-rack',root);let mix=E('div','pk-track pk-mixed',rack);E('span','pk-track-name',mix,'MIXED AUDIO');waveform(mix);r.mix=mix;['DIALOGUE','MUSIC','EFFECTS'].forEach((x,i)=>{let track=E('div','pk-track t'+i,rack);E('span','pk-track-name',track,x);waveform(track);r.parts.push(track);});E('div','pk-footnote',root,'SEPARATE STEMS · API FEES APPLY');r.times=cue(s,3);
    } else {
      label(root,'DELIVERY  /  KNOW THE LIMIT',s.headline);let line=E('div','pk-delivery',root);let a=E('div','pk-delivery-local',line);E('span','',a,'LOCAL');E('strong','',a,'768p');E('small','',a,'MAX NATIVE · MIXED AUDIO');let b=E('div','pk-delivery-host',line);E('span','',b,'HOSTED');E('strong','',b,'4K');E('small','',b,'UPSCALE + SEPARATE STEMS');E('div','pk-footnote',root,'HOSTED SERVICES MAY COST EXTRA');r.parts=[a,b];r.times=cue(s,2);
    }return r;
  }
  D.scenes.forEach((s,i)=>{s.idx=i;s._pk=build(s);});
  window.setTime=function(t){let s=D.scenes.find(x=>t>=x.t0&&t<x.t1)||D.scenes[D.scenes.length-1];D.scenes.forEach(x=>x._pk.root.style.display=x===s?'block':'none');if(s.archetype==='endcard'){s._pk.root.style.display='none';return;}s._pk.parts.forEach((e,i)=>reveal(e,t,s._pk.times[i]??s.t0+i*.35,0,22));if(s._pk.mix){let first=s._pk.times[0]??s.t0;let fade=clamp((t-first)/.35);s._pk.mix.style.opacity=1-fade;s._pk.mix.style.display=fade>=1?'none':'flex';}let proof=s._pk.root.querySelector('.pk-proof-image');if(proof){let steps=s.evidence_focus||[],local=Math.max(0,t-s.t0),a=steps[0],b=steps[1];for(let j=1;j<steps.length;j++){a=steps[j-1];b=steps[j];if(local<=b.at)break;}if(!a||!b)throw new Error('Product evidence focus plan missing');let k=Math.min(1,Math.max(0,(local-a.at)/(b.at-a.at)));let width=a.box[2]+k*(b.box[2]-a.box[2]);proof.style.transform='scale('+(1/width)+')';}};
  window.ready=true;
})();
