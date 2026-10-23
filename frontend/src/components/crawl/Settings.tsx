import { useState } from 'react';
import { Badge, Card, Input, Switch, Table } from '@/components/ds';
import type { CrawlConfig } from '@/lib/api/crawl';
import { parseList, settingsSources, limits } from '@/lib/logic/crawlConfig';
import { contextLabels } from '@/lib/contextLabels';
import { INTERNAL_TOOLS } from '@/lib/internalTools';
export const channelNames:Record<string,string> = {naver_cafe:'네이버 카페',naver_blog:'네이버 블로그',youtube:'유튜브 댓글',youtube_vlog:'유튜브 브이로그',threads:'Threads',naver_kin:'지식iN',cook82:'82쿡',ppomppu:'뽐뿌',clien:'클리앙',fixture:contextLabels.channels.fixture};
export const channelDescriptions: Record<string, string> = {
  naver_cafe: '검색 결과 화면 · 본문 (회원 전용 글은 제외)', naver_blog: '검색 결과 화면 · 본문',
  youtube: '영상 검색 · 댓글 스레드',
  youtube_vlog: '"키워드 브이로그" 영상 검색 · 한국어 자막을 화제 단위로 나눠 문서화',
  threads: '검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건',
  naver_kin: '질문 검색 · 질문 제목과 본문 (답변 제외)', cook82: '자유게시판 검색 · 본문 · 댓글',
  ppomppu: '사이트 검색 · 본문 · 댓글', clien: '사이트 검색 · 본문 · 댓글',
};
const NEW_CHANNELS = new Set(['youtube_vlog', 'threads', 'naver_kin', 'cook82']);
function ListInput({label,value,onChange}:{label:string;value:string[];onChange:(value:string[])=>void}) {
  // Keep an unfinished comma/space visible while emitting only normalized entries.
  const [text,setText]=useState<string|null>(null);
  return <Input label={label} hint="쉼표로 구분합니다. 포함 소스를 비우면 전체를 수집합니다." value={text??value.join(',')} onChange={e=>{setText(e.target.value);onChange(parseList(e.target.value));}} onBlur={()=>setText(null)}/>;
}
export function Settings({config,onChange,availableSources,axes,disabled,vlogError=''}:{config:CrawlConfig;onChange:(c:CrawlConfig)=>void;availableSources?:string[];axes:Record<string,number>;disabled:boolean;vlogError?:string}) {
  const set = <K extends keyof CrawlConfig>(key:K,value:CrawlConfig[K]) => onChange({...config,[key]:value});
  const sources = settingsSources(Object.keys(channelNames),config.channels,availableSources ?? []).filter(source => INTERNAL_TOOLS || source !== 'fixture');
  return <div className="crawl-columns"><div className="crawl-stack"><Card><h2 className="ds-t-card">채널</h2><p className="ds-t-caption">0-A 수집 채널에서 가져왔습니다</p><div className="crawl-channel-scroll" role="region" aria-label="수집 채널 스크롤" tabIndex={0}><Table aria-label="수집 채널"><thead><tr><th>채널</th><th>목록 · 본문</th>{INTERNAL_TOOLS && <th>연결 <Badge>내부용</Badge></th>}<th>사용</th></tr></thead><tbody>{sources.map(source=>{
    const available = availableSources?.includes(source) ?? false;
    return <tr key={source} style={available ? undefined : {opacity:0.55}}><td>{channelNames[source]??source} {NEW_CHANNELS.has(source) && <Badge tone="info">새 채널</Badge>} {!available && <Badge>사용 불가</Badge>}</td><td>{channelDescriptions[source] ?? '사이트 검색 · 본문 · 댓글'}{!available && source==='threads' && <p className="ds-t-caption">Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다.</p>}</td>{INTERNAL_TOOLS && <td><Badge tone={available ? 'success':'neutral'}>{available ? '사용 가능':'사용 불가'}</Badge></td>}<td><Switch label={`${channelNames[source]??source} 사용하기`} checked={available && config.channels.includes(source)} disabled={disabled || !available} onChange={checked=>{const channels=checked?[...config.channels,source]:config.channels.filter(s=>s!==source);onChange({...config,channels,perChannel:Object.fromEntries(channels.map(s=>[s,config.perChannel[s]??limits(s)]))});}}/></td></tr>;
  })}</tbody></Table></div></Card><Card><h2 className="ds-t-card">범위 · 필터</h2><fieldset disabled={disabled}><div className="crawl-fields"><Input label="시작일" type="date" value={config.dateFrom??''} onChange={e=>set('dateFrom',e.target.value||null)}/><Input label="종료일" type="date" value={config.dateTo??''} onChange={e=>set('dateTo',e.target.value||null)}/><Input label="목표 문서 수" type="number" min={1} value={config.target_total??''} hint="도달하면 상세 수집을 정상 종료합니다." onChange={e=>set('target_total',e.target.value?Number(e.target.value):null)}/></div>{(['adWords','excludeSources','includeSources'] as const).map((key,i)=><ListInput key={key} label={['광고어','제외 소스','포함 소스'][i]} value={config[key]} onChange={value=>set(key,value)}/>)}<Switch label="제품명 포함 글만 남기기" checked={config.product_name_filter} disabled={disabled} onChange={v=>set('product_name_filter',v)}/><p className="ds-t-caption">꺼 두는 것을 권장합니다. 켜면 제품명이 없는 글이 빠집니다. 제품 밖 경험을 놓칠 수 있습니다.</p><details><summary>고급 설정 펼치기 · 채널별 동시성 · 요청 간격 · 상한</summary>{config.channels.filter(source => INTERNAL_TOOLS || source !== 'fixture').map(source=><div key={source}><h3 className="ds-t-label">{channelNames[source]??source}</h3><div className="crawl-fields">{(['concurrency','min_interval_s','max_per_keyword'] as const).map((key,i)=><Input key={key} type="number" label={['동시성','요청 간격(초)','키워드당 상한'][i]} min={key==='min_interval_s'?0:1} max={key==='concurrency'?64:undefined} step={key==='min_interval_s'?0.1:1} value={(config.perChannel[source]??limits(source))[key]} onChange={e=>set('perChannel',{...config.perChannel,[source]:{...(config.perChannel[source]??limits(source)),[key]:Number(e.target.value)}})}/>)}</div></div>)}<h3 className="ds-t-label">유튜브 댓글</h3><div className="crawl-fields"><Input label="키워드당 영상 수" type="number" min={1} value={config.youtube.videos_per_keyword} onChange={e=>set('youtube',{...config.youtube,videos_per_keyword:Number(e.target.value)})}/><Input label="영상당 최대 댓글" type="number" min={0} value={config.youtube.max_comments} onChange={e=>set('youtube',{...config.youtube,max_comments:Number(e.target.value)})}/></div>
{config.channels.includes('youtube_vlog') && <fieldset aria-label="유튜브 브이로그 설정" aria-describedby={vlogError ? 'vlog-config-error' : undefined}>
  <h3 className="ds-t-label">유튜브 브이로그</h3><div className="crawl-fields">
    <Input label="키워드당 영상 수" type="number" min={1} step={1} value={config.youtube_vlog.videos_per_keyword} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,videos_per_keyword:Number(e.target.value)})}/>
    <Input label="최소 길이(분)" type="number" min={0} step={1} value={config.youtube_vlog.min_duration_s/60} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,min_duration_s:Math.round(Number(e.target.value)*60)})}/>
    <Input label="최대 길이(분)" type="number" min={1} step={1} value={config.youtube_vlog.max_duration_s/60} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,max_duration_s:Math.round(Number(e.target.value)*60)})}/>
  </div><p className="ds-t-caption">1분 미만 쇼츠와 60분이 넘는 영상은 목록에서 뺍니다. 한국어 자막이 없는 영상은 건너뛰고 결과에 건수를 남깁니다.</p>
</fieldset>}
</details>{vlogError && <p id="vlog-config-error" role="alert" className="ds-t-caption crawl-config-error">{vlogError}</p>}</fieldset></Card></div><Card><h2 className="ds-t-card">확정 키워드</h2><dl>{Object.entries(axes).map(([axis,count])=><div className="crawl-between" key={axis}><dt>{({physical:'물리',psychological:'심리',behavioral:'행동'} as Record<string,string>)[axis]??axis}</dt><dd>{count}</dd></div>)}</dl><p>합계 {Object.values(axes).reduce((a,b)=>a+b,0)}개</p><p className="ds-t-caption">검색어에는 제품명을 붙이지 않습니다. 예상 소요 시간은 목록 수집 후 표시합니다.{config.channels.includes('youtube_vlog') && ' 유튜브 브이로그는 검색어 뒤에 "브이로그"를 붙입니다.'}</p></Card></div>;
}
