/* ===== Configuration : les adresses sont uniquement ici (contrat v1.2, section 2.3) ===== */
const CONFIG = {
  API: 'http://localhost:8000/api/v1',
  WS: 'ws://localhost:8000/api/v1/ws',
  IMAGES: 'http://localhost:8000'   // + image_url (ex. /images/dechet_001.jpg), jamais /api/v1
};
const CLASSES = {
  plastique:['Plastique','#E0A400','Bac 1'],
  papier_carton:['Papier / carton','#2F6FB5','Bac 2'],
  verre:['Verre','#2E9E5B','Bac 3'],
  metal:['MÃ©tal','#7A8791','Bac 4'],
  textile:['Textile','#8B5FBF','Bac 5'],
  autre:['Autre','#8A5A3C','Bac 6'],
  tapis_vide:['Tapis vide','#D97706','ContrÃ´le manuel']
};
const BAC = {bac_1:'Bac 1',bac_2:'Bac 2',bac_3:'Bac 3',bac_4:'Bac 4',bac_5:'Bac 5',bac_6:'Bac 6'};

const $ = s => document.querySelector(s);
const el = (t, o = {}, ...k) => {
  const e = document.createElement(t);
  for (const [a, v] of Object.entries(o)) a === 'class' ? e.className = v : a.startsWith('on') ? e[a] = v : e.setAttribute(a, v);
  e.append(...k.filter(x => x != null)); return e;
};
const fmt = d => new Date(d).toLocaleString('fr-FR');
const label = t => (CLASSES[t] || [t])[0];
const img = u => CONFIG.IMAGES + u;
const token = () => sessionStorage.getItem('rm_token');
const me = () => JSON.parse(sessionStorage.getItem('rm_user') || 'null');
const showErr = x => { const e = $('#globalErr'); if (e) e.textContent = x.message; };

/* ===== API ===== */
function errText(d, s) {
  const x = d && d.detail;
  if (typeof x === 'string') return x;
  if (Array.isArray(x)) return x.map(e => (e.loc ? e.loc.slice(1).join('.') + ' : ' : '') + e.msg).join(' ; ');
  return 'Erreur ' + s;
}
async function api(path, opt = {}) {
  const headers = {'Content-Type': 'application/json'};
  if (token()) headers.Authorization = 'Bearer ' + token();
  let r;
  try { r = await fetch(CONFIG.API + path, {...opt, headers}); }
  catch { throw new Error('Serveur injoignable. VÃ©rifiez que le backend tourne sur ' + CONFIG.API); }
  if (r.status === 401 && path !== '/login') { logout(); throw new Error('Session expirÃ©e. Reconnectez-vous.'); }
  let d = null; try { d = await r.json(); } catch {}
  if (!r.ok) throw new Error(errText(d, r.status));
  return d;
}
function logout() { sessionStorage.clear(); location.href = 'login.html'; }

/* ===== Ã‰lÃ©ments communs ===== */
function statusBadge(t) {
  if (t.statut === 'trie') return el('span', {class:'badge b-trie'}, 'TriÃ©');
  return t.correction ? el('span', {class:'badge b-done'}, 'CorrigÃ© : ' + label(t.correction.type_corrige))
                      : el('span', {class:'badge b-todo'}, 'Ã€ traiter');
}
function showMetrics(s) {
  const m = $('#metrics'); m.replaceChildren();
  const item = (v, t) => el('span', {}, el('b', {}, String(v)), ' ' + t);
  m.append(item(s.total_tris, 'dÃ©chets triÃ©s'), item(s.nombre_a_traiter, 'Ã  traiter en contrÃ´le manuel'),
    item(Math.round(s.taux_incertitude * 100) + ' %', "taux d'incertitude"),
    item(s.debit_objets_minute.toFixed(1), 'objets par minute (5 derniÃ¨res minutes)'));
}

/* ===== Simulation ===== */
let simOn = false;
async function loadSim() {
  try {
    const {etat} = await api('/simulation/etat'); simOn = etat === 'en_cours';
    $('#simPill').className = 'pill ' + (simOn ? 'on' : 'off');
    $('#simPill span').textContent = simOn ? 'Simulation en cours' : 'Simulation arrÃªtÃ©e';
    $('#simBtn').textContent = simOn ? 'ArrÃªter la simulation' : 'DÃ©marrer la simulation';
  } catch (x) { showErr(x); }
}
async function toggleSim() {
  const b = $('#simBtn'); b.disabled = true;
  try { await api(simOn ? '/simulation/stop' : '/simulation/start', {method:'POST'}); await loadSim(); }
  catch (x) { showErr(x); } finally { b.disabled = false; }
}

/* ===== WebSocket ===== */
let ws = null, wsTries = 0;
function setWs(on, txt) { $('#wsPill').className = 'pill ' + (on ? 'on' : 'off'); $('#wsPill span').textContent = txt; }
function connectWS(hooks) {
  ws = new WebSocket(CONFIG.WS + '?token=' + encodeURIComponent(token()));
  ws.onopen = () => { setWs(true, 'En direct'); if (wsTries > 0 && hooks.onReconnect) hooks.onReconnect(); wsTries = 0; };
  ws.onmessage = m => {
    let msg; try { msg = JSON.parse(m.data); } catch { return; }
    if (msg.event === 'nouveau_tri' && hooks.onTri) hooks.onTri(msg.data);
  };
  ws.onclose = () => {
    setWs(false, 'Reconnexionâ€¦');
    api('/simulation/etat').catch(() => {});          // jeton expirÃ© : 401 renvoie Ã  la connexion
    setTimeout(() => connectWS(hooks), Math.min(1000 * 2 ** wsTries++, 15000));
  };
}

/* ===== Initialisation d'une page (en-tÃªte, simulation, direct) ===== */
function initPage(active, hooks = {}) {
  if (!token()) { location.replace('login.html'); return false; }

   const links = [
  ['index.html', 'Direct'],
  ['statistiques.html', 'Statistiques'],
  ['historique.html', 'Historique']
].map(([h, t]) =>
  el('a', {
    href: h,
    class: h === active ? 'on' : '',
    ...(h === active ? {'aria-current': 'page'} : {})
  }, t)
);
  document.body.prepend(el('header', {}, el('h1', {}, 'RecyMind'), el('nav', {}, ...links),
    el('span', {class:'pill off', id:'wsPill'}, el('i', {class:'dot'}), el('span', {}, 'Hors ligne')),
    el('span', {class:'pill off', id:'simPill'}, el('i', {class:'dot'}), el('span', {}, 'Simulation arrÃªtÃ©e')),
    el('button', {id:'simBtn', onclick:toggleSim}, 'DÃ©marrer la simulation'),
    el('span', {class:'who'}, me().username),
    el('button', {class:'ghost', onclick:logout}, 'Se dÃ©connecter')));
  loadSim(); setInterval(loadSim, 4000); connectWS(hooks);
  return true;
}
