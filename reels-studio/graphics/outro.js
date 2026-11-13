/* Shared house endcard: the earlier velocity-black brand card, not a template-specific sign-off. */
(function () {
  "use strict";
  function ramp(x,a,b) { return Math.max(0,Math.min(1,(x-a)/Math.max(.001,b-a))); }
  function ease(x) { return 1-Math.pow(1-x,3); }
  function el(tag,cls,parent,text) { var n=document.createElement(tag); n.className=cls; if(text!=null)n.textContent=text; parent.appendChild(n); return n; }
  window.buildOutro=function(parent,s) {
    var D=window.DATA||{}, b=D.brand||{}, p=s.payload||{};
    var root=el("div","yt-outro",parent);
    var title=el("div","yt-outro-title",root,s.headline||"YOUR CALL");
    var logo=el("img","yt-outro-logo",root); logo.src=b.logo||""; logo.alt=b.name||"";
    var name=el("div","yt-outro-name",root,b.name||"Hypeless");
    var handle=el("div","yt-outro-handle",root,b.handle||D.handle||"");
    var follow=el("div","yt-outro-follow",root,b.cta_button||"Follow");
    var chip=el("div","yt-outro-chip",root);
    var kw=el("span","yt-outro-kw",chip,"COMMENT "+String(p.keyword||"").toUpperCase());
    var prompt=el("div","yt-outro-prompt",root,p.prompt||"for the repo link");
    var cursor=el("div","yt-outro-cursor",root);
    cursor.innerHTML="<svg width='70' height='70' viewBox='0 0 24 24'><path d='M4 2 L20 12 L13 13.5 L16.5 21 L13.5 22.5 L10 14.5 L4 19 Z' fill='#fff' stroke='#000' stroke-width='1'/></svg>";
    return {root:root,logo:logo,name:name,handle:handle,follow:follow,chip:chip,kw:kw,prompt:prompt,cursor:cursor};
  };
  window.updateOutro=function(r,s,u,d) {
    var ev=s.ev||{}, press=typeof ev.press==='number'?ev.press-s.t0:Math.min(2.3,d*.48);
    var enter=ease(ramp(u,0,.35));
    r.chip.style.opacity=String(enter); r.chip.style.transform='scale('+(0.94+0.06*enter).toFixed(3)+')';
    var a=ease(ramp(u,Math.max(0,press-.7),press));
    var hit=ramp(u,press,press+.12)-ramp(u,press+.3,press+.45);
    r.cursor.style.opacity=String(a>0.02?1:0);
    r.cursor.style.transform='translate('+(-340*a).toFixed(1)+'px,'+(-560*a).toFixed(1)+'px)';
    r.follow.style.transform='scale('+(1-.12*hit).toFixed(3)+')';
  };
})();
