from pathlib import Path
import shutil,sqlite3,json,datetime
q=Path(__file__).resolve().parent
sp=Path('/private/tmp/claude-501/-Users-yunho--claude-spares-spare-d69SsJ/9251127c-9663-4223-85bb-09f9c61d81cd/scratchpad')
s=json.loads((q/'sessions.json').read_text())
items=[('main','r6main',s['main']['QA 채널 확장']['sid']),('empty','r6main',s['main']['QA 빈 결과']['sid']),('blocked','r6neg003',s['blocked']['QA 채널 확장']['sid'])]
if (q/'sample-session.json').exists():items.append(('sample','r6reg001',json.loads((q/'sample-session.json').read_text())['sid']))
for name,env,sid in items:
 src=sp/('qa-data-'+env)/'crawl'/sid/'collections'/'c1'
 if not src.exists():continue
 dst=q/('logs-'+name);dst.mkdir(exist_ok=True)
 for f in ['list.log','detail.log','report.json','worker_state.json','manifest.json','meta.json']:
  if (src/f).exists():shutil.copyfile(src/f,dst/f)
 db=sqlite3.connect('file:'+str(src/'queue.sqlite')+'?mode=ro',uri=True);backup=sqlite3.connect(dst/'queue.sqlite');db.backup(backup);backup.close()
 tables=db.execute("select name,sql from sqlite_master where type='table'").fetchall()
 data={n:db.execute('select * from "'+n+'"').fetchall() for n,sql in tables}
 (dst/'queue-dump.json').write_text(json.dumps({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(src),'schemas':tables,'data':data},ensure_ascii=False,indent=2,default=str));db.close()
 print(name,[(f.name,f.stat().st_size) for f in dst.iterdir()])
shutil.copyfile('backend/tests/qa_hooks/channel_expansion_qa.py',q/'qa-hook-inspected.py')
shutil.copyfile(sp/'qa_env.sh',q/'controller-launcher-inspected.sh')
