"""Minimal demo UI. Run the dev server + worker first, then:  uvicorn app.server:app --port 8000
Paste a WhatsApp message -> start RoomHoldWorkflow -> poll its query -> "Deposit received" sends the signal.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from munshi import config as cfg
from munshi.schema import GuestContext
from munshi.temporal.start_inquiry import get_status, send_deposit, start_hold
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
    message: str
    demo_speed: float = cfg.DEMO_SPEED
    provider: str = "tinker"
    repeat_guest: bool = False


class DepositReq(BaseModel):
    amount_pkr: int
    reference: str | None = None


@app.post("/api/inquiries")
async def start(req: StartReq) -> dict:
    wf_id = await start_hold(await client(), req.message, req.demo_speed, req.provider,
                             GuestContext(is_repeated_guest=int(req.repeat_guest)))
    return {"workflow_id": wf_id}


@app.get("/api/inquiries/{wf_id}")
async def status(wf_id: str) -> dict:
    return (await get_status(await client(), wf_id)).model_dump(mode="json")


@app.post("/api/inquiries/{wf_id}/deposit")
async def deposit(wf_id: str, req: DepositReq) -> dict:
    await send_deposit(await client(), wf_id, req.amount_pkr, req.reference)
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return PAGE


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Munshi front desk</title>
<style>
:root{--bg:#f7f5f0;--fg:#1d1b18;--muted:#6b665e;--card:#fff;--line:#e3ded4;--accent:#0d6b5f;--warn:#b54708}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px;display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media(max-width:760px){main{grid-template-columns:1fr}}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
h1{grid-column:1/-1;margin:8px 0 0;font-size:22px} h2{font-size:15px;margin:0 0 8px;color:var(--muted)}
textarea{width:100%;box-sizing:border-box;min-height:120px;font:inherit;padding:8px}
button{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:8px 14px;font:inherit;cursor:pointer}
pre{white-space:pre-wrap;background:#f1eee8;padding:8px;border-radius:6px;font-size:13px;margin:0}
.big{font-size:28px;font-variant-numeric:tabular-nums}.warn{color:var(--warn)} label{color:var(--muted)}
</style></head><body><main>
<h1>Munshi <span style="font-weight:400;color:var(--muted)">WhatsApp front desk</span></h1>
<section style="grid-column:1/-1"><h2>Guest message (pasted or exported)</h2>
<textarea id="msg">AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai? advance kitni?</textarea>
<p><label>Demo speed <input id="speed" type="number" value="60" style="width:60px"></label>
<label><input id="rep" type="checkbox"> repeat guest</label>
<label>Parser <select id="prov"><option>tinker</option><option>gemma</option></select></label>
<button onclick="go()">Start hold workflow</button> <span id="wf"></span></p></section>
<section><h2>Parsed (fine-tuned model)</h2><pre id="parsed">-</pre></section>
<section><h2>Risk (TabPFN) and quote</h2><div id="risk" class="big">-</div><pre id="quote">-</pre></section>
<section><h2>Nearby rates (SerpApi Google Hotels)</h2><pre id="comps">-</pre></section>
<section><h2>Draft reply (Gemma 4, from parsed fields only)</h2><pre id="draft">-</pre></section>
<section style="grid-column:1/-1"><h2>Hold</h2><div id="hold" class="big">-</div>
<p><button onclick="dep()">Deposit received</button> <span id="outcome"></span></p><pre id="follow"></pre></section>
</main><script>
let id=null,timer=null,expires=null;const $=s=>document.getElementById(s);
async function go(){const r=await fetch('/api/inquiries',{method:'POST',headers:{'content-type':'application/json'},
 body:JSON.stringify({message:$('msg').value,demo_speed:+$('speed').value,provider:$('prov').value,repeat_guest:$('rep').checked})});
 id=(await r.json()).workflow_id;$('wf').textContent=id;clearInterval(timer);timer=setInterval(poll,1000)}
async function poll(){const s=await (await fetch('/api/inquiries/'+id)).json();
 $('parsed').textContent=s.parsed?JSON.stringify(s.parsed,null,1)+'\\nmodel: '+s.parser_model:s.stage;
 if(s.risk){$('risk').textContent=(s.risk.p_cancel*100).toFixed(0)+'% cancel risk';}
 if(s.quote){$('quote').textContent=`Rs ${s.quote.nightly_pkr.toLocaleString()}/night x ${s.quote.nights} x ${s.quote.rooms} room = Rs ${s.quote.total_pkr.toLocaleString()}\\nadvance Rs ${s.quote.advance_pkr.toLocaleString()}, hold ${s.quote.hold_hours}h (${s.quote.risk_band} risk)\\nattempts: ${JSON.stringify(s.attempts)}`}
 if(s.comps){$('comps').textContent=`source: ${s.comps.source}, median Rs ${s.comps.median_nightly_pkr??'-'}\\n`+s.comps.comps.map(c=>`${c.name}: Rs ${c.nightly_pkr?.toLocaleString()}`).join('\\n')}
 if(s.draft)$('draft').textContent=s.draft; expires=s.hold_expires_at?new Date(s.hold_expires_at):null;
 $('outcome').textContent='stage: '+s.stage+' / outcome: '+s.outcome; if(s.followup)$('follow').textContent=s.followup;
 if(s.outcome!=='pending'){clearInterval(timer);timer=null;$('hold').textContent=s.outcome.toUpperCase()}
 else if(expires){const ms=expires-new Date();$('hold').textContent=ms>0?new Date(ms).toISOString().substr(11,8)+' left':'expiring...';
 $('hold').className='big'+(ms<60000?' warn':'')}}
async function dep(){if(!id)return;await fetch('/api/inquiries/'+id+'/deposit',{method:'POST',headers:{'content-type':'application/json'},
 body:JSON.stringify({amount_pkr:5000,reference:'demo'})});if(!timer)timer=setInterval(poll,1000)}
</script></body></html>"""
