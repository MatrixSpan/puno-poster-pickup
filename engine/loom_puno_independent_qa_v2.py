"""Independent local-only QA of the exact extracted LOOM prototype.
No external access, no code modifications. Run next to loom_puno_field_v2_candidate.py.
"""
from pathlib import Path
from runpy import run_path
import ast
import hashlib
import json

P = Path(__file__).with_name('loom_puno_field_v2_candidate.py')
source = P.read_text(encoding='utf-8')
n = run_path(str(P))
F = n['Field']; LAWS = n['LAWS']
DS = {'KIP': n['kip_respond'], 'L': n['l_respond']}
results = []

def report(name, expected, actual, details=''):
    results.append((name, expected, actual, details))
    print(f'{name}: {actual} (required: {expected})' + (f' — {details}' if details else ''))

try:
    ast.parse(source)
    report('Q01 Python syntax', 'PASS', 'PASS')
except SyntaxError as e:
    report('Q01 Python syntax', 'PASS', 'FAIL', str(e))

tree=ast.parse(source)
has_suite=any(isinstance(x,ast.If) and '__name__' in ast.unparse(x.test) for x in tree.body) or any(isinstance(x, ast.FunctionDef) and x.name.startswith('test_') for x in tree.body)
report('Q02 promised executable 11-test suite', 'PRESENT', 'PRESENT' if has_suite else 'ABSENT')

f=F(LAWS,DS)
report('Q03 wake roots', 'PASS', 'PASS' if len(f.conditions)==2 and len(f.trace)==3 else 'FAIL', f'{len(f.conditions)} roots; {len(f.trace)} trace events')

for name,tag,content in [('Q04 human text admission','text','radiator'),('Q05 UNKNOWN form admission','other',{'opaque':True})]:
    try:
        f=F(LAWS,DS);f.admit(content,'human',tag)
        report(name,'PASS','PASS')
    except Exception as e:
        report(name,'PASS','FAIL',type(e).__name__+': '+str(e))

try:
    f=F(LAWS,DS);f.admit('hello','human','text',route_to='L')
    report('Q06 L direct receipt','PASS','PASS')
    blob=f.serialize_trace()
    recreated=F.reconstruct(blob,DS)
    report('Q07 L receipt replay','PASS','PASS' if recreated.serialize_trace()==blob else 'FAIL')
except Exception as e:
    report('Q06/Q07 L direct receipt and replay','PASS','FAIL',type(e).__name__+': '+str(e))

try:
    F.reconstruct(blob,{'L':n['l_respond']})
    report('Q08 missing dialect detection','PASS','FAIL','Missing KIP accepted')
except n['FieldIntegrityError']:
    report('Q08 missing dialect detection','PASS','PASS')

try:
    altered=json.loads(blob);altered[-1]['why']=['altered after recording']
    F.reconstruct(json.dumps(altered),DS)
    report('Q09 trace tamper detection','PASS','FAIL','Edited event accepted')
except n['FieldIntegrityError']:
    report('Q09 trace tamper detection','PASS','PASS')

def mutate_trace(own,enc,tail,mint):
    tail[0]['kind']='resident-overwrote-law-header'
    return own, {'expressions':[], 'unknowns':[], 'why':[]}
f=F(LAWS,{'Bad':mutate_trace});f.admit('hi','human','text','Bad')
report('Q10 runtime trace immutability','PASS','PASS' if f.trace[0]['kind']=='law-header' else 'FAIL',f'trace[0].kind={f.trace[0]["kind"]}')

def mutate_in_place(own,enc,tail,mint):
    own[enc['self_addr']]['unlogged']=1
    return own, {'expressions':[], 'unknowns':[], 'why':[]}
f=F(LAWS,{'Bad':mutate_in_place});f.admit('hi','human','text','Bad')
root=f.participants['Bad']['root']
modified=f.conditions[root]['state'].get('unlogged')==1
logged=any(x['kind']=='transformation' for x in f.trace)
report('Q11 state transformation auditability','PASS','PASS' if not modified or logged else 'FAIL',f'state_changed={modified}, transformation_logged={logged}')

try:
    a=n['Addr'](1); pid=n['Addr'](3)
    enc={'self_addr':a,'packet_addr':pid,'packet':{'source':'human','form_tag':'other','content':'?','provenance':{'source':'human'}}}
    n['kip_respond']({a:{}},enc,[],lambda st,why='':n['Addr'](5))
    report('Q12 KIP UNKNOWN branch','PASS','PASS')
except Exception as e:
    report('Q12 KIP UNKNOWN branch','PASS','FAIL',type(e).__name__+': '+str(e))

print('SHA256 original extracted Python:',hashlib.sha256(P.read_bytes()).hexdigest())
print('SUMMARY:',sum(1 for x in results if x[1]==x[2]),'of',len(results),'checks meet expected behaviour')
