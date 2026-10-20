from pathlib import Path
import json,sys,datetime,re
q=Path(__file__).resolve().parent
f=q/sys.argv[1];raw=json.loads(f.read_text()); text='\n'.join(c.get('text','') for c in raw['content']); data=json.JSONDecoder().raw_decode(text.split('### Result\n',1)[1])[0]
r=json.loads((q.parent/'qa.json').read_text());r['browser']['preflight']='PASS'
for item in data.get('results',[]):
 id=item['id']; entry=next(x for x in r['scenarios'] if x['id']==id);entry.update(url=data['url'],result=item['result'],expected=item['expected'],actual=item['actual'])
 (q/(id+'.md')).write_text('# '+id+' — '+item['result']+'\n\nUTC: '+data['time']+'\n\nURL: '+data['url']+'\n\nSteps: '+item['steps']+'\n\nExpected: '+item['expected']+'\n\nActual: '+item['actual']+'\n\nEvidence: ['+f.name+']('+f.name+')\n\nScreenshots: '+', '.join(data.get('screenshots',[]))+'\n\nDOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.\n')
 if item['result'] in ['FAIL','BLOCKED']:r['findings'].append({'id':id,'detail':item['actual'],'evidence':entry['evidence']})
(q.parent/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
