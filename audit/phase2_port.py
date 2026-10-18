from __future__ import annotations
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

TARGET = Path('/home/ubuntu/sim800-platform-all-new9')
SOURCE = Path('/home/ubuntu/siblings/sim800l-data-16')
OUT = Path('/home/ubuntu/sim800-audit-output')
SOURCE_URL = 'https://github.com/AliNazarvand/sim800l-data-16'
SOURCE_SHA = subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'], text=True).strip()
NOW = datetime.now(timezone.utc).isoformat()
MAPPING = {
 'dat_01_at_command':'commands', 'dat_02_urc':'urcs', 'dat_03_error_code':'error_codes',
 'dat_04_timing_timeout':'timings', 'dat_05_state_machine':'states', 'dat_06_init_sequence':'init_sequences',
 'dat_07_hardware_reference':'hardware', 'dat_08_firmware_compatibility':'firmware_matrix',
 'dat_09_sms':'sms', 'dat_10_gprs_data':'gprs', 'dat_11_http_ftp_ssl':'http_ftp_ssl',
 'dat_12_audio':'audio', 'dat_13_sim_management':'sim', 'dat_14_operator_apn':'apn_mcc_mnc',
 'dat_15_power_management':'power', 'dat_16_board_evb':'boards', 'dat_17_certificate_key_store':'certificates',
 'dat_18_certification':'certifications',
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def port():
    result=[]
    for stem, name in MAPPING.items():
        src = SOURCE/'data'/f'{stem}.yaml'
        dst = TARGET/'dataset'/f'{name}.jsonl'
        records = yaml.safe_load(src.read_text(encoding='utf8')) or []
        existing=[]
        if dst.exists() and dst.stat().st_size:
            existing=[json.loads(x) for x in dst.read_text(encoding='utf8').splitlines() if x.strip()]
        keys={json.dumps({k:v for k,v in r.items() if k != '_provenance'}, sort_keys=True, ensure_ascii=False) for r in existing}
        added=0; rejected=0
        with dst.open('a', encoding='utf8', newline='\n') as f:
            for i,r in enumerate(records,1):
                if not isinstance(r,dict): rejected+=1; continue
                key=json.dumps(r, sort_keys=True, ensure_ascii=False)
                if key in keys: continue
                out=dict(r)
                out['_provenance']={
                    'source_repo': SOURCE_URL, 'source_commit': SOURCE_SHA,
                    'source_path': f'data/{src.name}', 'source_sha256': sha(src),
                    'ported_at': NOW, 'source_record_index': i,
                }
                f.write(json.dumps(out, ensure_ascii=False, sort_keys=True)+'\n'); added+=1
        result.append({'source':src.name,'destination':f'dataset/{name}.jsonl','source_records':len(records),'added':added,'rejected':rejected,'source_sha256':sha(src)})
    (OUT/'phase2-data-port.json').write_text(json.dumps({'source_commit':SOURCE_SHA,'records':result},indent=2,ensure_ascii=False)+'\n')

def infer_type(v):
    if v is None: return 'null'
    if isinstance(v,bool): return 'boolean'
    if isinstance(v,int) and not isinstance(v,bool): return 'integer'
    if isinstance(v,float): return 'number'
    if isinstance(v,str): return 'string'
    if isinstance(v,list):
        types=[]
        for x in v:
            t=infer_type(x)
            if isinstance(t, dict) and 'type' in t: t=t['type']
            if t not in types: types.append(t)
        item={'type':types[0]} if len(types)==1 and isinstance(types[0], str) else ({'type':types} if types else {})
        return {'type':'array','items':item}
    if isinstance(v,dict):
        props={k:infer_property([x.get(k) for x in [v] if k in x]) for k in v}
        return {'type':'object','properties':props,'additionalProperties':True}
    return {}

def infer_property(values):
    nonnull=[v for v in values if v is not None]
    types=[]
    for v in nonnull:
        t=infer_type(v); t=t.get('type') if isinstance(t,dict) else t
        if t not in types: types.append(t)
    schema=infer_type(nonnull[0]) if nonnull else {}
    if not isinstance(schema, dict): schema={'type':schema}
    if len(types)>1: schema['type']=types
    if any(v is None for v in values) and 'null' not in types: schema['type']=types+['null']
    return schema

def schema_for(records, title):
    if not records: return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':title,'type':'object','additionalProperties':True,'$comment':'insufficient evidence: no valid records'}
    kinds=[]
    objs=[r for r in records if isinstance(r,dict)]
    for r in records:
        t=infer_type(r); t=t.get('type') if isinstance(t,dict) else t
        if t not in kinds: kinds.append(t)
    s={'$schema':'https://json-schema.org/draft/2020-12/schema','title':title,'type':kinds[0] if len(kinds)==1 else kinds,'additionalProperties':True}
    if objs:
        keys=sorted({k for r in objs for k in r})
        s['properties']={k:infer_property([r[k] for r in objs if k in r]) for k in keys}
        req=[k for k in keys if all(k in r for r in objs)]
        if req: s['required']=req; s['$comment']='required inferred from 100% of sampled records; data-only required'
    return s

def schemas():
    rows=[]
    for stem,name in MAPPING.items():
        dst=TARGET/'dataset'/f'{name}.jsonl'; sp=TARGET/'data'/'schemas'/f'{name}.schema.json'
        if sp.stat().st_size: continue
        records=[json.loads(x) for x in dst.read_text(encoding='utf8').splitlines() if x.strip()]
        s=schema_for(records,name)
        Draft202012Validator.check_schema(s)
        sp.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
        rows.append({'schema':str(sp.relative_to(TARGET)),'records':len(records),'required':s.get('required',[]),'status':'created'})
    (OUT/'phase1-schema-inference.json').write_text(json.dumps({'schemas':rows,'algorithm':'Draft 2020-12; required iff present in 100% of observed records; additionalProperties=true; no data-only enum'},indent=2,ensure_ascii=False)+'\n')

if __name__=='__main__':
    port(); schemas(); print('port_and_schema_inference_complete')
