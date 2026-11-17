/* APKSTART / ORBIT — original narration-timed product explainer, deterministic for frame seeking. */
(function(){'use strict';
const D=window.DATA,stage=document.getElementById('stage');
const el=(tag,cls,parent,text)=>{const x=document.createElement(tag);x.className=cls||'';if(text!=null)x.textContent=text;if(parent)parent.appendChild(x);return x};
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>1-Math.pow(1-clamp(x),3);
const phase=(t,at,d=.48)=>ease((t-at)/d);
function header(r,s,kicker,sub){let top=el('div','orb-heading',r);el('div','orb-eyebrow',top,kicker);el('div','orb-title',top,s.headline);el('div','orb-subtitle',top,sub);return top}
function createScene(s){
 const root=el('div','scene',stage);root.dataset.scene=s.id;root.style.display='none';let bg=el('div','orb-bg',root);bg.setAttribute('data-house-camera','');
 let c={root,parts:[],special:[]};const add=x=>{c.parts.push(x);return x};
 if(s.archetype==='endcard')return c;
 if(s.archetype==='apk_hook'){
   header(root,s,'01  /  THE PAYOFF','A familiar desktop experience, powered by Android');
   const hero=el('div','orb-hero',root);if(!s.evidence_data)throw Error('Missing generated conceptual hero');
   const img=el('img','orb-hero-img',hero);img.src=s.evidence_data;img.alt='Conceptual Android to desktop illustration';
   const screen=add(el('div','orb-hero-chip chip-phone',hero));screen.innerHTML='<span class="chip-dot"></span> ANDROID';
   const desktop=add(el('div','orb-hero-chip chip-desktop',hero));desktop.innerHTML='<span class="chip-dot"></span> WINDOWS';
   const badge=add(el('div','orb-brand-badge',hero));badge.innerHTML='<b>APK</b><span>START</span>';
   const orbit=el('div','orb-hero-rings',hero);orbit.innerHTML='<i></i><i></i><i></i>';c.hero=hero;c.img=img;c.orbit=orbit;
   el('div','orb-foot',root,'CONCEPTUAL VISUAL  ·  NOT A PRODUCT RECORDING');
 }
 if(s.archetype==='apk_setup'){
   header(root,s,'02  /  HOW IT STARTS','A one-time runtime setup, then an APK file');
   const field=el('div','orb-stage setup-stage',root);field.innerHTML='<div class="orb-stage-grid"></div>';
   const line=el('div','setup-spine',field);const fill=el('div','setup-spine-fill',line);c.fill=fill;
   [['01','ANDROID RUNTIME','SET UP ONCE','runtime'],['02','APK FILE','ASSOCIATE FILE TYPE','file'],['03','DOUBLE CLICK','INSTALL YOUR APP','click']].forEach(([n,h,sub,icon])=>{
     let row=add(el('div','setup-node',field));let iconbox=el('div','setup-icon icon-'+icon,row);iconbox.innerHTML=icon==='runtime'?'<span>◆</span>':icon==='file'?'<span>.apk</span>':'<span>↗</span>';let label=el('div','setup-text',row);el('small','',label,n+'  /  '+sub);el('strong','',label,h);let tick=el('div','setup-tick',row,'✓');
   });el('div','orb-foot',root,'ILLUSTRATED WORKFLOW  ·  SETUP REQUIRED');
 }
 if(s.archetype==='apk_launch'){
   header(root,s,'03  /  MAKE IT FEEL AT HOME','Shortcut in. Separate window out.');
   const field=el('div','orb-stage launch-stage',root);el('div','desk-orbit',field);
   const shortcut=add(el('div','desk-shortcut',field));shortcut.innerHTML='<div class="desk-icon"><span>✦</span></div><b>APP</b><small>DESKTOP SHORTCUT</small>';
   const trail=el('div','desk-trail',field);trail.innerHTML='<svg viewBox="0 0 300 160" preserveAspectRatio="none"><path d="M5 135 C 80 135, 80 20, 280 20"/></svg><div class="trail-dot"></div>';c.trail=trail;
   const app=add(el('div','desk-window',field));app.innerHTML='<div class="desk-window-bar"><span>APP WINDOW</span><i>―　□　×</i></div><div class="desk-window-body"><div class="desk-app-icon">✦</div><div class="desk-lines"><i></i><i></i><i></i></div><div class="desk-widget"><span></span><span></span><span></span></div></div><div class="resize-grip">◢</div>';
   const resize=add(el('div','resize-label',field));resize.innerHTML='<span>↗</span> RESIZABLE';
   const proof=el('div','proof-strip',root);proof.innerHTML='<div class="proof-label">OFFICIAL APKSTART SCREENSHOT</div>';if(!s.evidence_data)throw Error('Missing ApkStart official UI screenshot');let image=el('img','proof-image',proof);image.src=s.evidence_data;image.alt='Actual screenshot from the ApkStart repository';c.proof=proof;
 }
 if(s.archetype==='apk_engine'){
   header(root,s,'04  /  UNDER THE HOOD','Windows-style experience. Android under the surface.');
   const field=el('div','orb-stage engine-stage',root);el('div','engine-connector',field);
   [['01','ANDROID TOOLS','APK + ANDROID','tool'],['02','VIRTUAL MACHINE','RUNS THE SYSTEM','vm'],['03','APP WINDOW','ON YOUR DESKTOP','win']].forEach(([n,title,sub,icon])=>{
     let item=add(el('div','engine-layer '+icon,field));el('div','engine-orb',item,icon==='tool'?'◇':icon==='vm'?'▦':'▣');let txt=el('div','engine-text',item);el('small','',txt,n+'  /  '+sub);el('strong','',txt,title);el('div','engine-mark',item,'↗')});
   el('div','orb-foot',root,'CONCEPTUAL LAYERS  ·  NOT NATIVE WINDOWS CODE');
 }
 if(s.archetype==='apk_catch'){
   header(root,s,'05  /  THE REALITY CHECK','What to know before you install');
   const field=el('div','orb-stage catch-stage',root);
   [['↧','RUNTIME DOWNLOAD','First setup needs components','violet'],['⌁','ARM-ONLY APPS','May need translation support','blue'],['✓','TRUSTED APKs','Install only files you trust','green']].forEach(([icon,title,sub,kind])=>{
     let row=add(el('div','catch-row '+kind,field));el('div','catch-icon',row,icon);let text=el('div','catch-text',row);el('strong','',text,title);el('span','',text,sub);el('div','catch-edge',row);
   });let badge=el('div','catch-badge',field,'READ THE DETAILS');c.badge=badge;
 }
 c.times=window.HouseMotion.cueTimes((s.payload||{}).cue_phrases||[],s,c.parts.length,{});return c;
}
D.scenes.forEach(s=>s._orbit=createScene(s));
window.setTime=function(t){
 const s=D.scenes.find(x=>t>=x.t0&&t<x.t1)||D.scenes[D.scenes.length-1];D.scenes.forEach(x=>x._orbit.root.style.display=x===s?'block':'none');if(s.archetype==='endcard'){s._orbit.root.style.display='none';return}
 const o=s._orbit;let enter=phase(t,s.t0,.30);o.root.style.opacity=String(.8+.2*enter);o.root.style.clipPath=`inset(0 ${(1-enter)*8}% 0 0 round 0px)`;
 o.parts.forEach((x,i)=>{let q=phase(t,o.times[i]??s.t0,.48);x.style.opacity=String(q);x.style.transform=`translateY(${(1-q)*30}px) scale(${.92+.08*q})`});
 if(o.img){let drift=clamp((t-s.t0)/Math.max(1,s.t1-s.t0));o.img.style.transform=`scale(${1.02+.055*drift})`;o.orbit.style.transform=`rotate(${drift*18}deg)`}
 if(o.fill){let q=phase(t,o.times[0]??s.t0,Math.max(.5,(o.times[o.times.length-1]||s.t1)-(o.times[0]||s.t0)));o.fill.style.transform=`scaleY(${q})`}
 if(o.trail){let q=phase(t,o.times[1]??s.t0,.65);o.trail.style.opacity=String(q);o.trail.querySelector('path').style.strokeDashoffset=String(390*(1-q));o.trail.querySelector('.trail-dot').style.transform=`translate(${q*235}px,${-q*95}px)`}
 if(o.proof){let q=phase(t,s.t0+.2,.4);o.proof.style.opacity=String(q)}
 if(o.badge)o.badge.style.transform=`rotate(${-4+2*Math.sin((t-s.t0)*2)}deg)`;
};window.ready=true;
})();
