from pathlib import Path
import json,os,datetime,subprocess
q=Path('docs/development/channel-expansion/qa'); head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); fingerprint=subprocess.check_output(['/Users/yunho/.local/bin/development-harness','fingerprint'],text=True).strip()
ids=[f'QA-{group}-{i:03}' for group,n in [('E2E',6),('NEG',4),('EDGE',4),('REG',3)] for i in range(1,n+1)]
r={'verdict':'FAIL','head':head,'fingerprint':fingerprint,'executor':'codex','role':'browser-qa','freshSession':True,'dispatch':os.environ['CODEX_THREAD_ID'],'browser':{'tool':'Playwright MCP, isolated Chrome','session':os.environ['CODEX_THREAD_ID']+' / new MCP isolated context','preflight':'FAIL','evidence':str(q/'preflight.md')},'servers':'controller-started (see preflight.md)','scenarios':[{'id':i,'url':'','result':'NOT_RUN','expected':'Approved QA plan literal assertions','actual':'Pending execution','evidence':str(q/(i+'.md'))} for i in ids],'findings':[]}
(q.parent/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
(q/'integrity-before.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n'+head+'\n'+fingerprint+'\n'+subprocess.check_output(['git','status','--short'],text=True))
for i in ids:(q/(i+'.md')).write_text('# '+i+'\n\nNOT_RUN — pending execution.\n')
