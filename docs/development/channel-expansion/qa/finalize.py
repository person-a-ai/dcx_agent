from pathlib import Path
import json,re,subprocess,datetime,hashlib
import struct,zlib
q=Path(__file__).resolve().parent; root=q.parents[3]
p=q.parent/'qa.json'; report=json.loads(p.read_text()); plan=(q.parent/'QA_PLAN-channel-expansion.md').read_text()
now=datetime.datetime.now(datetime.timezone.utc).isoformat();head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();fp=subprocess.check_output(['/Users/yunho/.local/bin/development-harness','fingerprint'],text=True).strip();status=subprocess.check_output(['git','status','--short'],text=True)
tracked=subprocess.check_output(['git','diff','--name-only'],text=True);staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True)
integrity={'time':now,'head':head,'fingerprint':fp,'trackedDiff':tracked,'stagedDiff':staged,'status':status,'headMatches':head==report['head'],'fingerprintMatches':fp==report['fingerprint']}
(q/'integrity-after.json').write_text(json.dumps(integrity,indent=2))
active=re.findall(r'^QA-(?:E2E|NEG|EDGE|REG)-\d{3}$',plan,re.M);assert len(active)==17
assert set(active)=={s['id'] for s in report['scenarios']}
assert not tracked and not staged and integrity['headMatches'] and integrity['fingerprintMatches']
extra={
'QA-E2E-002':['e2e002-visual-supplement.json','e2e002-values-visible.png'],
'QA-E2E-003':['seed.js','seed-output.json','e2e003-gate.json','logs-main/list.log','logs-main/queue-dump.json'],
'QA-E2E-004':['e2e004-running.json','e2e004-progress.json','e2e004-005-final.json','logs-main/worker_state.json','logs-main/queue-dump.json'],
'QA-E2E-005':['logs-main/report.json','edge002-verified.png'],
'QA-E2E-006':['e2e006-start.json','e2e006-channels.png'],
'QA-NEG-002':['controller-launcher-inspected.sh'],
'QA-NEG-003':['neg003-gate.json','neg003-paused.json','neg003-finish.json','neg003-log-check.json','logs-blocked/list.log','logs-blocked/detail.log','logs-blocked/report.json','logs-blocked/worker_state.json','logs-blocked/queue-dump.json','qa-hook-inspected.py'],
'QA-EDGE-001':['logs-empty/list.log','logs-empty/queue-dump.json'],
'QA-EDGE-002':['edge002-create-dialog.json','edge002-new-version.json','edge002-observed.json','edge002-pass.json','edge002-verified.json'],
'QA-EDGE-003':['edge003-settings.json','edge003-result.json','edge003-mobile-new-rows.json','edge003-mobile-four-rows.png','edge003-settings-375-left.png','edge003-settings-375-right.png','edge003-active-result-375-0.png','edge003-active-result-375-200.png','edge003-active-result-375-1000.png','edge003-settings-1100-left.png','edge003-settings-1200-left.png','edge003-settings-1300-left.png'],
'QA-REG-001':['sample-seed.js','sample-session.json','reg001-gate.json','reg001-start.json','logs-sample/report.json','logs-sample/worker_state.json','logs-sample/queue-dump.json'],
}
for s in report['scenarios']:
 block=re.search(r'```\n'+re.escape(s['id'])+r'\n(.*?)```',plan,re.S).group(1)
 s['expected']=block.split('Then:\n',1)[1].strip()
 path=root/s['evidence'];assert path.exists(),str(path)
 text=path.read_text();text+='\nApproved plan (verbatim):\n\n```\n'+s['id']+'\n'+block+'```\n'
 text+='\nAdditional evidence:\n\n'
 for name in extra.get(s['id'],[]):
  assert (q/name).exists(),name
  text+=f'- [{name}]({name})\n'
 text+='- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.\n- [Accumulated browser requests and console](browser-final-audit.json)\n- [Final source integrity](integrity-after.json)\n- [Screenshot inspection record](visual-inspection.md)\n'
 path.write_text(text)
images=[]
for path in sorted(q.glob('*.png')):
 blob=path.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n';offset=8;chunks=[]
 while offset<len(blob):
  size=struct.unpack('>I',blob[offset:offset+4])[0];kind=blob[offset+4:offset+8];payload=blob[offset+8:offset+8+size];crc=struct.unpack('>I',blob[offset+8+size:offset+12+size])[0];assert zlib.crc32(kind+payload)&0xffffffff==crc
  chunks.append(kind);offset+=12+size
 assert chunks[0]==b'IHDR' and chunks[-1]==b'IEND' and b'IDAT' in chunks
 images.append({'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(q/'screenshot-manifest.json').write_text(json.dumps(images,indent=2))
(q/'visual-inspection.md').write_text('''# Visual inspection

The QA executor opened saved PNGs with the local view_image tool. Inspected states include preflight; new channels; invalid range; boundary values; 5/2/30 values (e2e002-values-visible.png); expanded gate; running/completed progress; skip reasons; preprocessing choices and completion; unavailable Threads; paused and partially completed Threads; empty gate; new project channels; past version; fixture result and preprocess action.

Mobile screenshots were inspected at 375px: all four new channel names fit vertically after scrolling (edge003-mobile-four-rows.png); local horizontal scrolling exposes 채널, 사유, 건수 in three separate captures. Settings and result desktop screenshots at 1100, 1200, 1300px were inspected. The document width matched each viewport; table overflow remained local. Narrow labels wrap; no required column becomes unreachable.

Some early fullPage screenshots retain the viewport of the app's inner scrolling container. Relevant controls were subsequently scrolled into view and supplemental screenshots saved. Functional conclusions also use live DOM and API evidence, not screenshots alone.

All PNG paths and checksums are verified in screenshot-manifest.json. Failed locator attempts and the temporary native-disabled-only QA check are preserved; edge002-verified.json verifies aria-disabled with Playwright isDisabled. No product code was changed to resolve these QA script errors.
''')
(q/'preflight.md').write_text((q/'preflight.md').read_text()+f'\nFinal verification {now}: HEAD and fingerprint unchanged; tracked and staged diffs empty. Own browser tab closed; controller servers untouched. All 17 scenarios passed. Browser warnings also included the existing logo aspect-ratio warning; no errors. See integrity-after.json and visual-inspection.md.\n')
auto=sorted(str(x.resolve()) for x in Path('.playwright-mcp').glob('*2026-10-20T13-35*'))
(q/'tool-artifacts.md').write_text('# Tool-managed artifacts outside QA directory\n\n'+ '\n'.join('- `'+x+'`' for x in auto)+'\n\nPlaywright MCP automatically wrote its snapshot/console files here. The isolated Chrome profile/cache is tool-managed; its path was not exposed. QA explicitly wrote only qa/ and qa.json. Test API/UI operations created data in the controller-provided stores as intended by the plan.\n')
# Keep assertion failures only; the earlier native-disabled-only QA-script false negative was corrected by live verification.
assert all(s['result']=='PASS' for s in report['scenarios']);assert report['findings']==[]
report['verdict']='PASS';p.write_text(json.dumps(report,ensure_ascii=False,indent=2))
(q/'summary.md').write_text('# Independent browser QA — PASS\n\n17/17 active scenarios passed at `'+head+'`.\n\nFingerprint: `'+fp+'`.\n\nDispatch: `'+report['dispatch']+'`.\n\n| ID | Result | Actual |\n|---|---|---|\n'+''.join('| ['+s['id']+']('+s['id']+'.md) | '+s['result']+' | '+s['actual'].replace('|',' / ').replace('\n',' ')+' |\n' for s in report['scenarios'])+'\nNo findings. Product tracked files and Git index unchanged. Controller servers untouched. Browser closed. See tool-artifacts.md for MCP-generated files outside qa/.\n')
print(json.dumps({'verdict':report['verdict'],'scenarios':len(report['scenarios']),'pngs_verified':len(images),'integrity':integrity},indent=2))
