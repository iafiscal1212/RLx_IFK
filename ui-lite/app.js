async function fetchJSON(url, opts={}){
  const r = await fetch(url, {headers:{'content-type':'application/json'}, ...opts});
  const t = await r.text();
  try{ return {ok:r.ok, json: JSON.parse(t)} }catch{ return {ok:r.ok, text:t} }
}

async function ping(){
  const el = document.getElementById('health');
  const r = await fetchJSON('/api/v1/health');
  if(r.ok){
    el.innerHTML = `<span class="ok">OK</span> — ${r.json.message}`;
  }else{
    el.innerHTML = `<span class="err">ERROR</span>`;
  }
}

document.getElementById('sendForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {
    author: fd.get('author'),
    text: fd.get('text'),
    group_id: fd.get('group_id')
  };
  const r = await fetchJSON('/api/v1/chat/send', {method:'POST', body: JSON.stringify(body)});
  document.getElementById('sendOut').textContent = JSON.stringify(r.ok ? r.json : r.text, null, 2);
});

document.getElementById('deliveryForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData(e.target);
  const url = `/api/v1/chat/delivery/${fd.get('message_id')}?recipient=${encodeURIComponent(fd.get('recipient'))}`;
  const r = await fetchJSON(url);
  document.getElementById('deliveryOut').textContent = JSON.stringify(r.ok ? r.json : r.text, null, 2);
});

document.getElementById('renderForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd = new FormData(e.target);
  const url = `/api/v1/render/summary?message_id=${fd.get('message_id')}&recipient=${fd.get('recipient')}&lang=${fd.get('lang')}`;
  const r = await fetchJSON(url);
  document.getElementById('renderOut').textContent = JSON.stringify(r.ok ? r.json : r.text, null, 2);
});

ping();
