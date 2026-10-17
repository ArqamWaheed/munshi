"""Owner's front desk UI. Run the dev server + worker first, then:  uvicorn app.server:app --port 8000
Paste a WhatsApp message -> start RoomHoldWorkflow -> poll its query. Guest replies and deposits are signals;
the holds list comes from Temporal visibility; "Run morning brief" executes NightlyBriefWorkflow now.
"""
from __future__ import annotations

import html

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from temporalio.client import WorkflowFailureError
from temporalio.service import RPCError

from munshi import config as cfg
from munshi.schema import GuestContext
from munshi.temporal.start_inquiry import get_status, list_holds, run_brief, send_deposit, send_reply, start_hold
from munshi.temporal.worker import connect
from munshi.tracing import init_sentry

init_sentry("web")
app = FastAPI(title="Munshi")
_client = None


async def client():
    global _client
    if _client is None:
        _client = await connect()
    return _client


class StartReq(BaseModel):
    message: str = Field(min_length=1)
    demo_speed: float = cfg.DEMO_SPEED
    provider: str = "tinker"
    repeat_guest: bool = False


class DepositReq(BaseModel):
    amount_pkr: int = Field(gt=0)
    reference: str | None = None


class ReplyReq(BaseModel):
    text: str = Field(min_length=1)


def _not_found(e: RPCError) -> HTTPException:
    # Signalling a finished workflow (or a typo'd id) is an owner mistake, not a server error.
    return HTTPException(409, f"workflow not running: {e.message}")


@app.post("/api/inquiries")
async def start(req: StartReq) -> dict:
    wf_id = await start_hold(await client(), req.message, req.demo_speed, req.provider,
                             GuestContext(is_repeated_guest=int(req.repeat_guest)))
    return {"workflow_id": wf_id}


@app.get("/api/inquiries")
async def holds() -> list[dict]:
    return await list_holds(await client())


@app.get("/api/inquiries/{wf_id}")
async def status(wf_id: str) -> dict:
    return (await get_status(await client(), wf_id)).model_dump(mode="json")


@app.post("/api/inquiries/{wf_id}/deposit")
async def deposit(wf_id: str, req: DepositReq) -> dict:
    try:
        await send_deposit(await client(), wf_id, req.amount_pkr, req.reference)
    except RPCError as e:
        raise _not_found(e) from e
    return {"ok": True}


@app.post("/api/inquiries/{wf_id}/reply")
async def reply(wf_id: str, req: ReplyReq) -> dict:
    try:
        await send_reply(await client(), wf_id, req.text)
    except RPCError as e:
        raise _not_found(e) from e
    return {"ok": True}


@app.post("/api/brief")
async def brief() -> dict:
    try:
        return (await run_brief(await client())).model_dump(mode="json")
    except WorkflowFailureError as e:
        raise HTTPException(502, f"brief workflow failed: {e.cause}") from e


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return PAGE.replace("{{HOTEL}}", html.escape(cfg.HOTEL_NAME))


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Munshi front desk</title>
<style>
:root{--bg:#f7f5f0;--fg:#1d1b18;--muted:#6b665e;--card:#fff;--line:#e3ded4;--accent:#0d6b5f;--accent-soft:#e3f1ee;
 --warn:#b54708;--warn-soft:#fdf0e6;--bad:#b42318;--bad-soft:#fdecea;--guest:#fff;--us:#d9fdd3;--chat:#efeae2}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;padding:14px 16px;border-bottom:1px solid var(--line);background:var(--card)}
header h1{margin:0;font-size:20px} header .hotel{color:var(--muted)} header .sp{flex:1}
.layout{display:grid;grid-template-columns:300px 1fr;gap:16px;max-width:1200px;margin:0 auto;padding:16px}
@media(max-width:860px){.layout{grid-template-columns:1fr}}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;min-width:0}
h2{font-size:13px;letter-spacing:.04em;text-transform:uppercase;margin:0 0 10px;color:var(--muted)}
textarea,input,select{font:inherit;border:1px solid var(--line);border-radius:6px;padding:6px 8px;background:#fff;color:var(--fg)}
textarea{width:100%;min-height:96px;resize:vertical}
button{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:7px 12px;font:inherit;cursor:pointer}
button.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)} button:disabled{opacity:.5;cursor:default}
pre{white-space:pre-wrap;background:#f1eee8;padding:8px;border-radius:6px;font-size:13px;margin:0;overflow-wrap:anywhere}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center} .muted{color:var(--muted);font-size:13px}
.side{display:grid;gap:16px;align-content:start} .main{display:grid;gap:16px;grid-template-columns:1fr 1fr;align-content:start}
.main .wide{grid-column:1/-1} @media(max-width:600px){.main{grid-template-columns:1fr}}
.holds{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.holds li{border:1px solid var(--line);border-radius:8px;padding:8px 10px;cursor:pointer}
.holds li.sel{border-color:var(--accent);background:var(--accent-soft)} .holds .id{font-family:ui-monospace,monospace;font-size:12px}
.chip{display:inline-block;font-size:12px;border-radius:999px;padding:1px 8px;background:#eee;color:var(--fg)}
.chip.pending{background:var(--warn-soft);color:var(--warn)} .chip.confirmed{background:var(--accent-soft);color:var(--accent)}
.chip.released,.chip.needs_clarification{background:var(--bad-soft);color:var(--bad)}
.chat{background:var(--chat);border-radius:8px;padding:10px;display:grid;gap:6px}
.bubble{max-width:85%;padding:6px 10px;border-radius:8px;white-space:pre-wrap;box-shadow:0 1px 0 rgba(0,0,0,.08)}
.bubble.guest{background:var(--guest);justify-self:start} .bubble.us{background:var(--us);justify-self:end}
.bubble .who{display:block;font-size:11px;color:var(--muted)}
.big{font-size:28px;font-variant-numeric:tabular-nums;line-height:1.2} .warn{color:var(--warn)}
dl{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;margin:0} dt{color:var(--muted)} dd{margin:0;font-variant-numeric:tabular-nums}
.empty{color:var(--muted);text-align:center;padding:40px 0} .err{color:var(--bad);font-size:13px}
</style></head><body>
<header><h1>Munshi</h1><span class="hotel">{{HOTEL}} &middot; WhatsApp front desk</span><span class="sp"></span>
<a class="muted" href="http://localhost:8233" target="_blank" rel="noopener">Temporal UI</a></header>
<div class="layout">
<div class="side">
 <section><h2>New guest message</h2>
  <textarea id="msg" aria-label="Guest message">AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai? advance kitni?</textarea>
  <div class="row" style="margin-top:8px">
   <label class="muted">Demo speed <input id="speed" type="number" value="60" min="1" style="width:70px"></label>
   <label class="muted"><input id="rep" type="checkbox"> repeat guest</label>
   <label class="muted">Parser <select id="prov"><option>tinker</option><option>gemma</option></select></label>
  </div>
  <div class="row" style="margin-top:8px"><button id="go">Start hold</button><span id="goErr" class="err"></span></div>
 </section>
 <section><h2>Holds</h2><ul id="holds" class="holds"><li class="muted">Loading&hellip;</li></ul></section>
 <section><h2>Morning brief</h2><div class="row"><button class="ghost" id="briefBtn">Run morning brief</button>
  <span class="muted">runs NightlyBriefWorkflow now</span></div></section>
</div>
<div class="main" id="main"><section class="wide empty" id="none">Start a hold or pick one from the list.</section></div>
</div>
<template id="detail">
 <section class="wide"><div class="row"><h2 style="margin:0">Conversation</h2><span class="sp" style="flex:1"></span>
  <span class="id muted" data-k="id"></span><span class="chip" data-k="chip"></span></div>
  <div class="chat" data-k="chat" style="margin-top:10px"></div>
  <div class="row" data-k="actions" style="margin-top:10px"></div></section>
 <section><h2>Parsed (fine-tuned model)</h2><pre data-k="parsed">-</pre></section>
 <section><h2>Risk (TabPFN) and quote</h2><div class="big" data-k="risk">-</div><dl data-k="quote" style="margin-top:8px"></dl></section>
 <section data-k="compsSec" style="display:none"><h2>Nearby rates (SerpApi Google Hotels)</h2><pre data-k="comps">-</pre></section>
 <section><h2>Hold</h2><div class="big" data-k="hold">-</div><dl data-k="paid" style="margin-top:8px"></dl>
  <div class="row" data-k="depRow" style="margin-top:10px">
   <label class="muted">Rs <input data-k="amt" type="number" min="1" style="width:110px"></label>
   <input data-k="ref" placeholder="JazzCash / bank ref" style="width:150px"><button data-k="depBtn">Deposit received</button></div>
  <div class="err" data-k="depErr"></div></section>
</template>
<script>
const $=s=>document.getElementById(s), rs=n=>n==null?'-':'Rs '+Number(n).toLocaleString('en-PK');
let id=null,timer=null,view=null,amtTouched=false;
async function api(path,body){const r=await fetch(path,body===undefined?{}:{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
 if(!r.ok){let m=r.statusText;try{m=(await r.json()).detail||m}catch(e){} throw new Error(typeof m==='string'?m:JSON.stringify(m))} return r.json()}
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e}
function bubble(who,text,cls){const b=el('div','bubble '+cls);b.append(el('span','who',who),document.createTextNode(text));return b}
function dl(node,pairs){node.replaceChildren(...pairs.flatMap(([k,v])=>[el('dt',null,k),el('dd',null,v)]))}
function copyBtn(text){const b=el('button','ghost','Copy reply');b.onclick=async()=>{try{await navigator.clipboard.writeText(text);b.textContent='Copied'}catch(e){b.textContent='Copy failed'}};return b}

$('go').onclick=async()=>{$('goErr').textContent='';$('go').disabled=true;
 try{const r=await api('/api/inquiries',{message:$('msg').value,demo_speed:+$('speed').value,provider:$('prov').value,repeat_guest:$('rep').checked});
  select(r.workflow_id);loadHolds()}catch(e){$('goErr').textContent=e.message}finally{$('go').disabled=false}};
$('briefBtn').onclick=async()=>{const b=$('briefBtn');b.disabled=true;id=null;view=null;clearInterval(timer);timer=null;
 document.querySelectorAll('#holds li').forEach(li=>li.classList.remove('sel'));
 const sec=el('section','wide'),h=el('h2',null,'Morning brief'),p=el('pre',null,'Running NightlyBriefWorkflow...');
 p.style.fontSize='14px';sec.append(h,p);$('main').replaceChildren(sec);
 try{const r=await api('/api/brief',{});h.textContent='Morning brief · '+r.arrivals+' arrival(s) · '+r.path.split(/[\\\\/]/).pop();p.textContent=r.text}
 catch(e){p.textContent='Failed: '+e.message}finally{b.disabled=false}};

async function loadHolds(){const ul=$('holds');
 try{const rows=await api('/api/inquiries');
  if(!rows.length){ul.replaceChildren(el('li','muted','No holds yet.'));return}
  ul.replaceChildren(...rows.map(r=>{const li=el('li',r.workflow_id===id?'sel':'');
   const top=el('div','row');top.append(el('span','id',r.workflow_id),el('span','chip '+(r.outcome||''),r.outcome||r.temporal_status.toLowerCase()));
   li.append(top,el('div','muted',[r.stage,r.check_in&&('in '+r.check_in),r.total_pkr&&rs(r.total_pkr)].filter(Boolean).join(' · ')||'worker offline?'));
   li.onclick=()=>select(r.workflow_id);return li}))}
 catch(e){ul.replaceChildren(el('li','err','Cannot list holds: '+e.message))}}

function select(wf){id=wf;amtTouched=false;const main=$('main');main.replaceChildren($('detail').content.cloneNode(true));
 view={};main.querySelectorAll('[data-k]').forEach(n=>view[n.dataset.k]=n);view.id.textContent=wf;
 view.amt.oninput=()=>amtTouched=true;
 view.depBtn.onclick=async()=>{view.depErr.textContent='';
  try{await api('/api/inquiries/'+id+'/deposit',{amount_pkr:+view.amt.value,reference:view.ref.value||null});amtTouched=false;view.ref.value='';poll()}
  catch(e){view.depErr.textContent=e.message}};
 document.querySelectorAll('#holds li').forEach(li=>li.classList.toggle('sel',li.querySelector('.id')?.textContent===wf));
 clearInterval(timer);timer=setInterval(poll,1000);poll()}

function chat(s){const out=[bubble('Guest',s.guest_message||'-','guest')];
 // clarification rounds: our question, then the guest's answer
 s.questions.forEach((q,i)=>{out.push(bubble('Munshi (question)',q,'us'));if(s.guest_replies[i]!=null)out.push(bubble('Guest',s.guest_replies[i],'guest'))});
 s.guest_replies.slice(s.questions.length).forEach(t=>out.push(bubble('Guest',t,'guest')));
 const who=k=>s.template_fallbacks.includes(k)?'Template ('+k+'): Gemma unavailable or its draft failed the checker'
  :'Gemma draft ('+k+')'+(s.attempts['draft_'+k+'_rewrites']?' · rewritten after the checker rejected a number':'');
 if(s.quote&&s.draft)out.push(bubble(who('quote'),s.draft,'us'));
 else if(!s.questions.length&&s.draft)out.push(el('div','muted',s.draft));  // e.g. parser failed: owner replies by hand
 if(s.followup)out.push(bubble(who(s.outcome),s.followup,'us'));
 return out}

function actions(s){  // rebuilt only when what they act on changes, so typing in the reply box survives polling
 const text=s.followup||(s.quote?s.draft:s.questions.at(-1)),key=[s.stage,s.outcome,text].join('|');
 if(view.actions.dataset.key===key)return;view.actions.dataset.key=key;const act=[];
 if(text)act.push(copyBtn(text));
 if(s.stage==='awaiting guest reply'){const inp=el('input');inp.placeholder="Guest's answer, e.g. 'kal se 2 raat'";inp.style.flex='1';
  const b=el('button',null,'Send guest reply');b.onclick=async()=>{if(!inp.value)return;b.disabled=true;
   try{await api('/api/inquiries/'+id+'/reply',{text:inp.value});poll()}catch(e){b.disabled=false;view.depErr.textContent=e.message}};
  act.push(inp,b)}
 view.actions.replaceChildren(...act)}

async function poll(){if(!id)return;const wf=id;let s;
 try{s=await api('/api/inquiries/'+wf)}catch(e){if(view)view.chip.textContent='unreachable';return}
 if(wf!==id)return;  // a different hold was selected while this request was in flight
 view.chip.className='chip '+s.outcome;view.chip.textContent=s.outcome==='pending'?s.stage:s.outcome.replace('_',' ');
 view.chat.replaceChildren(...chat(s));actions(s);
 view.parsed.textContent=s.parsed?JSON.stringify(s.parsed,null,1)+'\\nmodel: '+s.parser_model:s.stage;
 if(s.risk)view.risk.textContent=(s.risk.p_cancel*100).toFixed(0)+'% cancel risk';
 if(s.quote){const q=s.quote;const med=s.comps?.median_nightly_pkr;
  dl(view.quote,[['Nightly',rs(q.nightly_pkr)+(med?' (nearby median '+rs(med)+')':' (base rate)')],['Stay',q.nights+' night(s) × '+q.rooms+' room(s)'],['Total',rs(q.total_pkr)],
  ['Advance',rs(q.advance_pkr)+' ('+q.risk_band+' risk)'],['Hold',q.hold_hours+' h'],['Risk model',s.risk.model],['Attempts',JSON.stringify(s.attempts)]]);
  if(!amtTouched)view.amt.value=Math.max(q.advance_pkr-(s.deposit?.amount_pkr||0),0)||q.advance_pkr}
 const hasComps=!!s.comps?.comps.length;view.compsSec.style.display=hasComps?'':'none';  // SerpApi is optional
 if(hasComps)view.comps.textContent=`source: ${s.comps.source}, median ${rs(s.comps.median_nightly_pkr)}\\n`+s.comps.comps.map(c=>`${c.name}: ${rs(c.nightly_pkr)}`).join('\\n');
 const paid=s.deposit?.amount_pkr||0;
 const paidRow=['Paid',rs(paid)+(s.deposit?.reference?' ('+s.deposit.reference+')':'')];
 dl(view.paid,!s.quote?[]:s.outcome==='pending'?[paidRow,['Still due',rs(Math.max(s.quote.advance_pkr-paid,0))]]:[paidRow]);
 const holding=s.stage==='holding';view.depRow.style.display=holding?'flex':'none';
 if(s.outcome!=='pending'){view.hold.className='big';view.hold.textContent=s.outcome.replace('_',' ').toUpperCase()+
   (s.outcome==='released'&&paid?' · refund '+rs(paid):'');
  if(s.stage==='done'){clearInterval(timer);timer=null;loadHolds()}}  // outcome is set before the follow-up is drafted
 else{const exp=s.hold_expires_at||s.reply_expires_at;
  if(exp){const ms=new Date(exp)-new Date();view.hold.textContent=(ms>0?new Date(ms).toISOString().substr(11,8)+' left':'expiring...')+
   (s.reply_expires_at?' for guest reply':'');view.hold.className='big'+(ms<60000?' warn':'')}
  else view.hold.textContent=s.stage}}

loadHolds();setInterval(loadHolds,5000);
</script></body></html>"""
