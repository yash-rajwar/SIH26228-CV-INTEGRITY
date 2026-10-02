"""COMP-IFACE: self-contained, loopback-only, read-only analyst console.

ACC-2026-10-02-03 separates audit observation from trusted diagnostics.
HTTPServer is intentionally synchronous: the supervisor-owned SQLite connection
stays on its creating thread. No submitted asset is opened by this interface.
"""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import json
import sqlite3
from urllib.parse import urlsplit

from assurance_system.exceptions import AssuranceSystemError
from assurance_system.supervisor.audit_chain import AuditChainWriter


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080  # TASK-024 owner-approved default; CLI --port overrides.

_CSS = r"""
:root{color-scheme:dark;--bg:#0a101c;--panel:#111c2c;--raised:#172438;--line:#27364d;--text:#e6edf8;--muted:#a4b3cb;--blue:#6a9eff;--cyan:#79d5e5;--radius:14px}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 'Segoe UI',system-ui,sans-serif}button,input,select{font:inherit}button{cursor:pointer}button,input,select{color:var(--text);background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:9px 12px}button:hover{background:var(--raised);border-color:#6484b4}button,input,select,a{transition:background 180ms,border-color 180ms}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}a{color:var(--blue)}[hidden]{display:none!important}svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
.shell{display:grid;grid-template-columns:252px minmax(0,1fr);min-height:100vh}.sidebar{position:sticky;top:0;height:100vh;padding:32px 20px 22px;background:linear-gradient(165deg,#121e31,#0d1625);border-right:1px solid var(--line);display:flex;flex-direction:column}.brandmark{width:44px;height:44px;border:1px solid #456eaf;background:#1b3051;display:grid;place-items:center;border-radius:13px;color:var(--cyan);margin-bottom:14px}.brand{font-size:22px;font-weight:650;letter-spacing:-.5px}.brand-sub{color:#c9d5e8;font-size:15px}.eyebrow{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:1.6px}.brand-note{margin-top:8px;color:var(--muted);font-size:12px}.nav-label{margin:40px 12px 10px}nav{display:grid;gap:6px}nav button{display:flex;align-items:center;gap:12px;text-align:left;background:transparent;border-color:transparent;padding:12px;color:var(--muted)}nav button[aria-current=page]{color:#e6f0ff;background:#203759;border-color:#385986;box-shadow:inset 3px 0 var(--blue)}.sidebar-foot{margin-top:auto;padding:20px 8px 0;border-top:1px solid var(--line)}.badges{display:flex;gap:8px;flex-wrap:wrap}.badge{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.5px;border:1px solid #3d5577;border-radius:6px;padding:4px 7px;color:#c6d9f8;background:#1b2a40;white-space:normal;overflow-wrap:anywhere}.badge.alt{color:var(--cyan);border-color:#3b6676;background:#193040}.sidebar-foot p{font-size:11px;color:var(--muted);margin-bottom:0}.main{min-width:0}.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:24px 32px;border-bottom:1px solid var(--line);background:#0e1726}.topbar h1{font-size:23px;font-weight:600;letter-spacing:-.5px;margin:0}.subtitle{margin:3px 0 0;color:var(--muted);font-size:12px}.tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.tools input{width:220px;background:#111e31}.refresh{display:flex;gap:7px;align-items:center}.toolbar-meta{display:flex;justify-content:space-between;gap:15px;padding:12px 32px;color:var(--muted);font-size:11px}.content{padding:10px 32px 32px;max-width:1800px;margin:auto}.intro{display:flex;align-items:end;justify-content:space-between;gap:14px;margin:12px 0 22px}.intro h2{font-size:27px;letter-spacing:-.7px;font-weight:600;margin:0}.intro p{color:var(--muted);margin:5px 0 0}.panel{background:linear-gradient(145deg,#142033,#111b2b);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 10px 28px #0002;padding:22px;margin-bottom:20px;min-width:0}.panel h3{font-size:15px;font-weight:600;margin:0}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:20px}.panel-note{color:var(--muted);font-size:12px;margin:5px 0}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:22px}.metric{margin:0;position:relative;padding:20px}.metric-top{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px}.metric svg{color:var(--blue)}.metric strong{display:block;font-size:34px;font-weight:600;letter-spacing:-1px;margin:12px 0 0}.metric small{color:var(--muted);font-size:11px}.overview-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(250px,1fr);gap:20px}.states{display:grid;gap:12px}.state-row{display:flex;justify-content:space-between;align-items:center;gap:15px;padding:11px 0;border-bottom:1px solid var(--line)}.state-row strong{font-size:18px;color:var(--cyan)}.pipeline{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));margin:28px 0 18px;gap:12px}.step{position:relative;border:1px solid var(--line);background:#101b2d;border-radius:12px;padding:14px 10px;min-width:0}.step:not(:last-child):after{content:'→';position:absolute;right:-13px;top:29px;color:var(--muted);z-index:1}.step-num{font:11px Consolas,monospace;color:var(--blue);margin-bottom:10px}.step-title{font-size:12px;min-height:40px}.step .badge{font-size:9px;margin-top:10px}.filters{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 18px}.filters label{display:grid;gap:5px;color:var(--muted);font-size:11px;flex:1;min-width:130px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;text-align:left;font-size:12px}th{background:#1a2940;color:var(--muted);font-size:10px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;white-space:nowrap}td,th{padding:13px 12px;border-bottom:1px solid var(--line)}td{vertical-align:top}tbody tr:hover{background:#1b2b42}td button{max-width:170px;text-align:left;padding:5px 8px}.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px;overflow-wrap:anywhere;user-select:text}.truncate{display:block;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.master-detail{display:grid;grid-template-columns:minmax(230px,.8fr) minmax(0,1.5fr);gap:20px}.record-list{display:grid;gap:10px;align-content:start;max-height:680px;overflow:auto;padding:2px}.record-button{text-align:left;padding:15px;display:grid;gap:7px;width:100%;border-radius:11px}.record-button[aria-pressed=true]{border-color:var(--blue);background:#203450}.record-heading{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.record-meta{color:var(--muted);font-size:11px}.detail{min-width:0}.detail-title{font-size:18px;margin:0 0 12px}.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;margin:18px 0}.field{min-width:0}.field dt{font-size:10px;color:var(--muted);letter-spacing:.5px;text-transform:uppercase}.field dd{margin:4px 0 0;overflow-wrap:anywhere}details{border-top:1px solid var(--line);padding:12px 0}summary{cursor:pointer;color:#c8d9f3;font-size:12px;font-weight:600}details ul{padding-left:20px}details li{margin:8px 0;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0d1727;border:1px solid #263750;border-radius:9px;padding:14px;font:12px/1.7 Consolas,monospace;color:#c3d6ef;max-height:none}details p{overflow-wrap:anywhere}.detail-actions{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.empty{padding:40px 20px;text-align:center;border:1px dashed #354762;border-radius:12px;background:#101b2b;color:var(--muted)}.empty strong{display:block;color:#d6e1f1;margin-bottom:7px;font-weight:500}.integrity{display:flex;align-items:center;justify-content:space-between;gap:16px;background:#1b2b45;border:1px solid #46658f;border-left:4px solid var(--blue);padding:20px;border-radius:12px;margin-bottom:22px}.integrity strong{font-size:20px;letter-spacing:.5px}.timeline{border-left:1px solid #41618b;margin-left:8px;padding-left:25px}.event{position:relative;margin:0 0 18px}.event:before{content:'';position:absolute;left:-31px;top:28px;width:10px;height:10px;border-radius:50%;background:var(--cyan);border:2px solid var(--bg)}.event-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.event-top h3{font-size:13px;overflow-wrap:anywhere}.event time{color:var(--muted);font:11px Consolas,monospace}.coverage-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.coverage-grid .panel{margin:0}.notice{border:1px solid #426284;background:#15283f;color:#cfddf1;border-radius:10px;padding:15px;margin:12px 0 20px}.error{border:1px solid #8296b6;background:#223149;padding:16px;border-radius:10px;margin-bottom:20px;overflow-wrap:anywhere}.loading{color:var(--muted);padding:30px}.footer{color:var(--muted);font-size:11px;padding-top:5px;border-top:1px solid var(--line)}
@media(min-width:1600px){.cards{grid-template-columns:repeat(6,minmax(0,1fr))}}
@media(max-width:1200px){.sidebar{padding:25px 15px}.shell{grid-template-columns:230px minmax(0,1fr)}.topbar{align-items:flex-start;flex-direction:column}.overview-grid{grid-template-columns:1fr}.content{padding:10px 22px 25px}.pipeline{gap:8px}.step{padding:12px 7px}}
@media(max-width:950px){.shell{grid-template-columns:1fr}.sidebar{height:auto;position:static;padding:18px 22px;border-right:0;border-bottom:1px solid var(--line)}.brandmark,.nav-label,.sidebar-foot{display:none}.brand{font-size:19px}.brand-sub,.brand-note{display:inline;font-size:11px;margin-right:12px}nav{display:flex;flex-wrap:wrap;margin-top:15px;gap:4px}nav button{font-size:11px;padding:9px}.topbar{padding:20px 22px;flex-direction:row}.toolbar-meta{padding:12px 22px}.master-detail{grid-template-columns:minmax(220px,.8fr) minmax(0,1.2fr)}}
@media(max-width:650px){.topbar,.intro{flex-direction:column;align-items:flex-start}.tools{width:100%}.tools input{flex:1;min-width:100px;width:100%}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.master-detail,.coverage-grid{grid-template-columns:1fr}.pipeline{grid-template-columns:1fr}.step{display:flex;align-items:center;gap:12px}.step-title{min-height:0;flex:1}.step-num{margin:0}.step .badge{margin:0}.step:not(:last-child):after{content:'↓';right:50%;top:auto;bottom:-13px}.fields{grid-template-columns:1fr}.panel{padding:18px}.content{padding:5px 16px 22px}.toolbar-meta{padding:12px 16px;flex-wrap:wrap}.record-list{max-height:360px}.integrity{align-items:flex-start;flex-direction:column}.intro h2{font-size:23px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

_JS = r"""
'use strict';
const $=id=>document.getElementById(id);
const titles={overview:['Overview','Persisted observations, explicit boundaries.'],findings:['Findings','Interpretations with their limitations intact.'],evidence:['Evidence Explorer','Follow records, identifiers and byte identity.'],audit:['Audit Timeline','Temporal history and non-mutating chain inspection.'],coverage:['Coverage & Deferred','Coverage explicitly not assessed.'],provenance:['Provenance','Record binding, replay state and signing availability.']};
let data=null,section='overview',selectedFinding=null,selectedEvidence=null;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e}
function val(v){return v===null||v===undefined?'UNAVAILABLE':typeof v==='object'?JSON.stringify(v,null,2):String(v)}
function badge(v){return node('span',val(v),'badge'+(['DEFERRED_IN_SCOPE','SIGNING_UNAVAILABLE','REFERENCE_UNAVAILABLE','UNAVAILABLE','CHAIN_CORRUPT'].includes(v)?' alt':''))}
function empty(parent,title,body='No corresponding records are stored. State: UNAVAILABLE.'){const e=node('div',undefined,'empty');e.append(node('strong',title),node('span',body));parent.append(e)}
function clear(e){e.replaceChildren()}
function icon(){return document.querySelector('.brandmark svg').cloneNode(true)}
function btn(text,action){const b=node('button',text);b.type='button';b.addEventListener('click',action);return b}
function field(parent,key,value){const box=node('div',undefined,'field');box.append(node('dt',key.replaceAll('_',' ')),node('dd',val(value),'mono'));parent.append(box)}
function expand(parent,label,value,open=false){const d=node('details');d.open=open;d.append(node('summary',label));if(Array.isArray(value)){const ul=node('ul');for(const v of value)ul.append(node('li',val(v)));if(!value.length)ul.append(node('li','UNAVAILABLE — no values stored'));d.append(ul)}else d.append(node('pre',val(value)));parent.append(d)}
function detail(parent,record,heading){clear(parent);if(!record){empty(parent,'Select a record','Full identifiers, limitations and non-claims appear here.');return}parent.append(node('h3',heading,'detail-title'));const f=node('dl',undefined,'fields');for(const [k,v] of Object.entries(record)){if(!['raw_signal','limitations','non_claims','dependency_declaration','evidence_record_digests'].includes(k))field(f,k,v)}parent.append(f);expand(parent,'Limitations',record.limitations,true);expand(parent,'Non-claims',record.non_claims,true);if(record.evidence_record_digests)expand(parent,'Evidence record digests',record.evidence_record_digests,true);if(record.dependency_declaration!==undefined)expand(parent,'Dependency declaration',record.dependency_declaration);if(record.raw_signal!==undefined)expand(parent,'Raw signal · untrusted display data',record.raw_signal);}
function search(rows){const q=$('search').value.trim().toLowerCase();return rows.filter(r=>!q||String(r.asset_id||'').toLowerCase().includes(q))}
function choose(name){section=name;for(const [key,[title,sub]]of Object.entries(titles)){$('view-'+key).hidden=key!==name;const b=document.querySelector('[data-view="'+key+'"]');if(key===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')} $('section-title').textContent=titles[name][0];$('section-subtitle').textContent=titles[name][1];render();}
function assetRecords(rows,asset){return rows.filter(r=>r.asset_id===asset)}
function observed(rows,key){if(!rows.length)return 'UNAVAILABLE';if(rows.every(r=>r[key]==='DEFERRED_IN_SCOPE'))return 'DEFERRED_IN_SCOPE';if(rows.every(r=>['UNAVAILABLE','ASSESSMENT_ERROR','SIGNING_UNAVAILABLE'].includes(r[key])))return 'UNAVAILABLE';return 'OBSERVED'}
function renderPipeline(){const asset=$('pipeline-asset').value;const records=assetRecords(data.evidence,asset),findings=assetRecords(data.findings,asset);const digests=new Set(records.map(r=>r.record_digest).filter(Boolean));const prov=data.provenance.filter(p=>(p.evidence_record_digests||[]).some(d=>digests.has(d)));const stages=[['Ingestion','UNAVAILABLE'],['C2 Data Integrity',observed(records.filter(r=>String(r.worker_id).startsWith('COMP-W-C2')),'assessment_status')],['C3 Model Integrity',observed(records.filter(r=>String(r.worker_id).startsWith('COMP-W-C3')),'assessment_status')],['C4 Provenance',prov.length?'OBSERVED':'UNAVAILABLE'],['C5 Interpretation',observed(findings,'detection_status')],['Evidence Store',records.length||findings.length?'OBSERVED':'UNAVAILABLE']];clear($('pipeline'));stages.forEach(([title,state],i)=>{const s=node('div',undefined,'step');s.append(node('div','0'+(i+1),'step-num'),node('div',title,'step-title'),badge(state));$('pipeline').append(s)});}
function renderOverview(){clear($('metrics'));for(const [label,count,caption]of [['Assets observed',data.counts.assets,'Distinct persisted asset identifiers'],['Findings',data.counts.findings,'Recorded C5 interpretations'],['Evidence records',data.counts.evidence,'Worker observations retained'],['Deferred records',data.counts.deferred,'Explicit coverage boundaries'],['Audit events',data.counts.audit,'Persisted temporal history'],['Synthetic records',data.counts.synthetic,'Labelled findings and evidence']]){const card=node('article',undefined,'panel metric'),top=node('div',undefined,'metric-top');top.append(node('span',label),icon());card.append(top,node('strong',count),node('small',caption));$('metrics').append(card)}clear($('states'));for(const [state,count]of Object.entries(data.assessment_states)){const r=node('div',undefined,'state-row');r.append(badge(state),node('strong',count));$('states').append(r)}if(!Object.keys(data.assessment_states).length)empty($('states'),'No assessment states stored');const previous=$('pipeline-asset').value;clear($('pipeline-asset'));$('pipeline-asset').append(new Option('Select a stored asset',''));for(const asset of data.assets)$('pipeline-asset').append(new Option(asset,asset));if(data.assets.includes(previous))$('pipeline-asset').value=previous;renderPipeline();clear($('boundary-summary'));for(const text of ['UNAVAILABLE remains unavailable.','Deferred methods are not assessment results.','An anomaly does not establish malicious intent.','Record identity does not establish causal execution.'])$('boundary-summary').append(node('p',text,'panel-note'));}
function options(id,rows,key){const select=$(id),prev=select.value;clear(select);select.append(new Option('All',''));for(const value of [...new Set(rows.map(r=>r[key]).filter(v=>v!==null&&v!==undefined))].sort())select.append(new Option(String(value),String(value)));select.value=prev;}
function renderFindings(){options('method-filter',data.findings,'method_id');options('detection-filter',data.findings,'detection_status');options('applicability-filter',data.findings,'applicability_status');const rows=search(data.findings).filter(r=>['method','detection','applicability'].every(name=>!$(name+'-filter').value||String(r[name==='method'?'method_id':name+'_status'])===$(name+'-filter').value)&&($('synthetic-filter').value!=='synthetic'||r.is_synthetic));clear($('findings-body'));$('findings-empty').hidden=rows.length>0;for(const r of rows){const tr=node('tr');const first=node('td');const b=btn(r.asset_id,()=>{selectedFinding=r.finding_id;renderFindingDetail(r);});b.className='mono truncate';b.title=val(r.asset_id);first.append(b);tr.append(first);for(const key of ['method_id','detection_status','interpretation_status','applicability_status','analyst_disposition_prompt','is_synthetic','created_at']){const td=node('td');td.append(key.endsWith('status')?badge(r[key]):node('span',key==='is_synthetic'?(r[key]?'SYNTHETIC':'No'):val(r[key])));tr.append(td)}$('findings-body').append(tr)}const selected=rows.find(r=>r.finding_id===selectedFinding);renderFindingDetail(selected);$('finding-count').textContent=rows.length+' records';}
function renderFindingDetail(r){detail($('finding-detail'),r,'Finding detail');if(!r)return;const matching=data.evidence.filter(e=>e.asset_id===r.asset_id&&(e.method_id===r.method_id||(r.dependency_declaration?.co_firing_detectors||[]).includes(e.worker_id)||(r.dependency_declaration?.co_firing_detectors||[]).includes(e.method_id)));const actions=node('div',undefined,'detail-actions');for(const e of matching)actions.append(btn('Evidence · '+e.method_id,()=>{selectedEvidence=e.record_id;$('search').value=e.asset_id;choose('evidence')}));if(!matching.length)actions.append(node('p','Evidence correlation UNAVAILABLE — no stored asset/method/dependency match.','panel-note'));$('finding-detail').append(actions);}
function renderEvidence(){const rows=search(data.evidence);clear($('evidence-list'));if(!rows.length)empty($('evidence-list'),'No evidence records');for(const r of rows){const b=btn('',()=>{selectedEvidence=r.record_id;renderEvidence()});b.className='record-button';b.setAttribute('aria-pressed',String(r.record_id===selectedEvidence));const head=node('div',undefined,'record-heading');head.append(node('strong',r.method_id),badge(r.assessment_status));b.append(head,node('span',r.asset_id,'mono'),node('span',val(r.worker_id)+' · '+val(r.assessment_timestamp),'record-meta'));$('evidence-list').append(b)}const r=rows.find(e=>e.record_id===selectedEvidence);detail($('evidence-detail'),r,'Evidence record');if(r){const links=node('div',undefined,'detail-actions');links.append(btn('Findings for this asset',()=>{$('search').value=r.asset_id;choose('findings')}));$('evidence-detail').append(links);expand($('evidence-detail'),'Audit correlation','UNAVAILABLE — persisted audit payload digests do not expose record identifiers. No relationship inferred.');}}
function renderAudit(){clear($('chain-status'));$('chain-status').append(node('div','Audit Chain Integrity','eyebrow'),node('strong',data.chain.status));$('chain-caption').textContent=data.chain.intact===true?'Stored links and durable chain state inspected. Tail completeness is not established.':data.chain.status==='CHAIN_CORRUPT'?'Violations detected. Historical events remain visible; no repair or diagnostic write performed.':'Inspection unavailable. No intact-chain result established.';clear($('chain-violations'));if(data.chain.violations?.length)expand($('chain-violations'),'Inspection violations',data.chain.violations,true);clear($('audit-events'));for(const r of data.audit){const card=node('article',undefined,'panel event'),head=node('div',undefined,'event-top');head.append(node('h3','#'+r.event_id+' · '+r.event_type),node('time',r.timestamp));card.append(head);const fields=node('dl',undefined,'fields');for(const key of ['chain_link_hash','previous_event_digest','supervisor_version_id']){field(fields,key,typeof r[key]==='string'&&key.endsWith('hash')?r[key].slice(0,20)+'…':r[key])}card.append(fields);expand(card,'Full event · identifiers and digests',r);$('audit-events').append(card)}if(!data.audit.length)empty($('audit-events'),'No audit events stored');}
function renderCoverage(){clear($('coverage-records'));for(const r of search(data.deferred)){const card=node('article',undefined,'panel');const head=node('div',undefined,'panel-head');head.append(node('h3',r.method_id),badge(r.assessment_status));card.append(head,node('p',r.deferral_reason),node('p',r.asset_id,'mono'));expand(card,'Limitations',r.limitations,true);expand(card,'Non-claims',r.non_claims,true);expand(card,'Stored record',r);$('coverage-records').append(card)}if(!$('coverage-records').children.length)empty($('coverage-records'),'No coverage records','Coverage status UNAVAILABLE — no stored declaration for this filter.');}
function renderProvenance(){clear($('provenance-records'));const q=$('search').value.trim().toLowerCase();const visibleDigests=new Set(search(data.evidence).map(r=>r.record_digest));const rows=data.provenance.filter(p=>!q||(p.evidence_record_digests||[]).some(d=>visibleDigests.has(d)));for(const r of rows){const card=node('article',undefined,'panel');const head=node('div',undefined,'panel-head');head.append(node('h3','Provenance · '+val(r.sequence_number)),badge(r.signing_status));card.append(head);const fields=node('dl',undefined,'fields');for(const key of ['provenance_id','artifact_unit_digest','sequence_number','replay_nonce','signing_key_id','signature_algorithm','signing_status','canonicalization_algorithm','timestamp'])field(fields,key,r[key]);card.append(fields);expand(card,'Evidence record digests',r.evidence_record_digests,true);expand(card,'PF-002 non-claim',r.pf_002_non_claim,true);expand(card,'Full stored record',r);$('provenance-records').append(card)}if(!rows.length)empty($('provenance-records'),'No correlated provenance records','Signing/binding status UNAVAILABLE for this filter. No signature is implied.');}
function render(){if(!data)return;renderOverview();renderFindings();renderEvidence();renderAudit();renderCoverage();renderProvenance();}
async function refresh(){$('refresh').disabled=true;$('loading').hidden=false;$('error').hidden=true;try{const response=await fetch('/api/dashboard',{cache:'no-store',credentials:'omit'});if(!response.ok)throw Error('Evidence snapshot unavailable (HTTP '+response.status+').');data=await response.json();$('refreshed').textContent='Last refreshed · '+data.refreshed_at;render()}catch(e){$('error').textContent=String(e.message)+' No new state established. Previously rendered records, if any, are stale.';$('error').hidden=false;$('refreshed').textContent='Refresh unavailable · prior snapshot may be stale'}finally{$('refresh').disabled=false;$('loading').hidden=true}}
for(const b of document.querySelectorAll('[data-view]'))b.addEventListener('click',()=>choose(b.dataset.view));$('refresh').addEventListener('click',refresh);$('search').addEventListener('input',render);$('pipeline-asset').addEventListener('change',renderPipeline);for(const id of ['method-filter','detection-filter','applicability-filter','synthetic-filter'])$(id).addEventListener('change',renderFindings);refresh();
"""

_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 3 7v6c0 4 9 8 9 8s9-4 9-8V7Z"/><path d="M8 11h8M8 15h5"/></svg>'
_NAV_ICONS = (
    '<path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/>',
    '<path d="M6 3h12v18H6zM9 8h6M9 12h6M9 16h4"/>',
    '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M7 10h6"/>',
    '<path d="M5 3v18M5 6h14M5 12h10M5 18h14"/><circle cx="5" cy="6" r="2"/>',
    '<path d="m12 3 9 5v8l-9 5-9-5V8zM3 8l9 5 9-5M12 13v8"/>',
    '<path d="M8 8V5h11v11h-3M5 8h11v13H5zM8 12h5M8 16h5"/>',
)


def _page() -> str:
    navigation = "".join(
        f'<button type="button" data-view="{key}"'
        + (' aria-current="page"' if key == "overview" else '')
        + f'><svg viewBox="0 0 24 24" aria-hidden="true">{icon}</svg>{label}</button>'
        for (key, label), icon in zip(
            (("overview", "Overview"), ("findings", "Findings"),
             ("evidence", "Evidence Explorer"), ("audit", "Audit Timeline"),
             ("coverage", "Coverage &amp; Deferred"), ("provenance", "Provenance")),
            _NAV_ICONS,
        )
    )
    # Static markup only. All untrusted data arrives separately as JSON and is
    # placed into DOM text nodes; there is no data-in-script interpolation.
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CV Integrity · Assurance Console</title><style>{_CSS}</style></head><body>
<div class="shell"><aside class="sidebar" aria-label="Console navigation">
<div class="brandmark">{_ICON}</div><div class="brand">CV Integrity</div>
<div class="brand-sub">Assurance Console</div><div class="brand-note">Offline Evidence Analysis</div>
<div class="eyebrow nav-label">Analyst workspace</div><nav aria-label="Primary">{navigation}</nav>
<div class="sidebar-foot"><div class="badges"><span class="badge alt">OFFLINE</span><span class="badge">READ ONLY</span></div><p>Evidence-first · bounded interpretation<br>No operational signing claim</p></div></aside>
<main class="main"><header class="topbar"><div><h1 id="section-title">Overview</h1><p id="section-subtitle" class="subtitle">Persisted observations, explicit boundaries.</p></div>
<div class="tools"><input id="search" type="search" aria-label="Filter by asset identifier" placeholder="Search asset identifier…"><button id="refresh" type="button" class="refresh">{_ICON}Refresh</button><span class="badge">READ ONLY</span></div></header>
<div class="toolbar-meta"><span>LOCAL EVIDENCE WORKSPACE</span><span id="refreshed" aria-live="polite">Not yet refreshed</span></div>
<div class="content"><div id="error" class="error" role="alert" hidden></div><div id="loading" class="loading" role="status">Reading persisted observations…</div>
<section id="view-overview" aria-label="Overview"><div class="intro"><div><div class="eyebrow">Evidence / Overview</div><h2>Evidence at a glance</h2><p>Recorded facts. Explicit coverage. No inferred conclusions.</p></div><span class="badge alt">PERSISTED OBSERVATIONS</span></div>
<div id="metrics" class="cards"></div><article class="panel"><div class="panel-head"><div><h3>Observed Pipeline State</h3><p class="panel-note">Conceptual flow · not live execution telemetry</p></div><select id="pipeline-asset" aria-label="Select pipeline asset"><option value="">Select a stored asset</option></select></div><div id="pipeline" class="pipeline"></div><p class="panel-note">OBSERVED means a corresponding record exists, not that every assessment completed. Ingestion telemetry and missing stages remain UNAVAILABLE.</p></article>
<div class="overview-grid"><article class="panel"><div class="panel-head"><h3>Assessment State Overview</h3><span class="eyebrow">Evidence counts</span></div><div id="states" class="states"></div></article><article class="panel"><div class="panel-head"><h3>Interpretation boundaries</h3>{_ICON}</div><div id="boundary-summary"></div><div class="notice">Coverage gaps and non-claims are part of the evidence, not footnotes.</div></article></div></section>
<section id="view-findings" aria-label="Findings" hidden><div class="intro"><div><div class="eyebrow">Analysis / Findings</div><h2>Finding workspace</h2><p>Exact recorded states, with context and non-claims.</p></div><span id="finding-count" class="badge">0 records</span></div>
<div class="panel"><div class="filters"><label>Method<select id="method-filter"><option value="">All</option></select></label><label>Detection status<select id="detection-filter"><option value="">All</option></select></label><label>Applicability<select id="applicability-filter"><option value="">All</option></select></label><label>Synthetic selector<select id="synthetic-filter"><option value="all">All records</option><option value="synthetic">Synthetic only</option></select></label></div>
<div class="table-wrap"><table><thead><tr><th scope="col">Asset</th><th scope="col">Method</th><th scope="col">Detection</th><th scope="col">Interpretation</th><th scope="col">Applicability</th><th scope="col">Disposition</th><th scope="col">Synthetic</th><th scope="col">Created</th></tr></thead><tbody id="findings-body"></tbody></table></div><div id="findings-empty" class="empty"><strong>No findings for this filter</strong>Finding status UNAVAILABLE — no matching persisted record.</div></div><article id="finding-detail" class="panel detail" aria-label="Finding detail"></article></section>
<section id="view-evidence" aria-label="Evidence Explorer" hidden><div class="intro"><div><div class="eyebrow">Investigation / Records</div><h2>Evidence Explorer</h2><p>Inspect the record without changing it.</p></div><span class="badge">SELECT-ONLY</span></div><div class="master-detail"><div id="evidence-list" class="record-list" aria-label="Evidence records"></div><article id="evidence-detail" class="panel detail" aria-label="Evidence detail"></article></div></section>
<section id="view-audit" aria-label="Audit Timeline" hidden><div class="intro"><div><div class="eyebrow">Governance / History</div><h2>Audit Timeline</h2><p>Complete stored history, no repair or diagnostic writes.</p></div></div><article class="integrity"><div id="chain-status"></div><p id="chain-caption" class="panel-note"></p></article><div id="chain-violations"></div><div id="audit-events" class="timeline"></div></section>
<section id="view-coverage" aria-label="Coverage and Deferred" hidden><div class="intro"><div><div class="eyebrow">Boundaries / Coverage</div><h2>Coverage &amp; Deferred</h2><p>Coverage explicitly not assessed.</p></div></div><div class="notice">DEFERRED_IN_SCOPE · REFERENCE_UNAVAILABLE · COMPLETENESS_UNAVAILABLE remain explicit. Their absence is not a positive finding.</div><div id="coverage-records" class="coverage-grid"></div></section>
<section id="view-provenance" aria-label="Provenance" hidden><div class="intro"><div><div class="eyebrow">Governance / Record Binding</div><h2>Provenance</h2><p>Stored binding and replay state; no causal-execution implication.</p></div></div><div class="notice">Operational signing provisioning remains partial. SIGNING_UNAVAILABLE is displayed as recorded; no signature is implied.</div><div id="provenance-records"></div></section>
<footer class="footer">CV Integrity · Offline Evidence Analysis · Local-clock timestamps · Read-only analyst interface</footer></div></main></div><script>{_JS}</script></body></html>'''


class Dashboard:
    """Serve current store observations without persistence authority."""

    def __init__(self, store, *, audit_chain_factory=AuditChainWriter):
        self._store = store
        self._audit_chain = audit_chain_factory(store)

    def snapshot(self) -> dict:
        """A fixed number of public SELECT queries; no generic SQL/asset access."""
        findings = self._store.query_findings()
        evidence = self._store.query_all_evidence()
        deferred = self._store.query_deferred()
        provenance = self._store.query_provenance_records()
        # AuditWriteError is deliberately not caught: failed inspection cannot
        # become an intact result. HTTP reports failure without hiding corruption.
        chain = self._audit_chain.inspect_chain_integrity()
        audit = self._store.query_audit_trail()
        assets = sorted({r["asset_id"] for r in findings + evidence + deferred})
        return {
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings, "evidence": evidence, "deferred": deferred,
            "provenance": provenance, "audit": audit, "assets": assets,
            "chain": dict(asdict(chain), status="CHAIN INTACT" if chain.intact else "CHAIN_CORRUPT"),
            "assessment_states": dict(sorted(Counter(r["assessment_status"] for r in evidence).items())),
            "counts": {
                "assets": len(assets), "findings": len(findings),
                "evidence": len(evidence), "deferred": len(deferred),
                "audit": len(audit),
                "synthetic": sum(bool(r.get("is_synthetic")) for r in findings + evidence),
            },
        }

    def _make_server(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> HTTPServer:
        """Construction seam: port zero is supported for local integration tests."""
        address = ipaddress.ip_address(host)
        if not address.is_loopback or address.version != 4:
            raise ValueError("Dashboard must bind to a loopback address")
        if not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError("Invalid dashboard port")
        dashboard = self
        markup = _page().encode("utf-8")
        script_hash = base64.b64encode(hashlib.sha256(_JS.encode()).digest()).decode()
        style_hash = base64.b64encode(hashlib.sha256(_CSS.encode()).digest()).decode()
        csp = (
            "default-src 'none'; connect-src 'self'; "
            f"script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
        )

        class Handler(BaseHTTPRequestHandler):
            def _reply(self, code, body=b"", content_type="text/plain; charset=utf-8"):
                self.send_response(code)
                for key, value in {
                    "Content-Type": content_type, "Content-Length": str(len(body)),
                    "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                    "X-Frame-Options": "DENY", "Cache-Control": "no-store",
                    "Content-Security-Policy": csp,
                }.items():
                    self.send_header(key, value)
                if code == 405:
                    self.send_header("Allow", "GET, HEAD")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)

            def do_GET(self):
                # Reject foreign Host values to bound DNS-rebinding exposure.
                host_header = self.headers.get("Host", "").split(":", 1)[0]
                if host_header not in (host, "localhost"):
                    self._reply(403, b"Loopback host required")
                    return
                path = urlsplit(self.path).path
                if path == "/":
                    self._reply(200, markup, "text/html; charset=utf-8")
                elif path == "/api/dashboard":
                    try:
                        payload = json.dumps(dashboard.snapshot(), ensure_ascii=True, allow_nan=False).encode()
                    except (AssuranceSystemError, sqlite3.Error, ValueError, TypeError, KeyError):
                        # Fail visibly, never synthesize an intact/positive result.
                        self._reply(503, b"UNAVAILABLE: evidence or audit inspection failed")
                    else:
                        self._reply(200, payload, "application/json; charset=utf-8")
                else:
                    self._reply(404, b"Not found")

            do_HEAD = do_GET

            def _not_allowed(self):
                self._reply(405, b"Read-only dashboard")

            do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = _not_allowed

            def send_error(self, code, message=None, explain=None):
                # BaseHTTPRequestHandler's unknown-verb 501 must also respect
                # the GET/HEAD-only contract, with the same response headers.
                self._reply(405 if code == 501 else code, b"Request rejected")

            def log_message(self, format, *args):
                # Avoid logging attacker-controlled HTTP text to an analyst terminal.
                pass

        return HTTPServer((host, port), Handler)

    def run(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        with self._make_server(host, port) as server:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
