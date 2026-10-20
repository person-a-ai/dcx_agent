async (page) => {
  const all = {};
  const calls = [];
  for (const [env,port] of [['main',8010],['unavailable',8011],['blocked',8012],['sample',8013]]) {
    const api = `http://localhost:${port}`;
    const request = async (method,path,data) => {
      const response = await page.request.fetch(api+path,{method,data,timeout:30000});
      const body = await response.json();
      calls.push({time:new Date().toISOString(),env,method,path,status:response.status(),body});
      if (!response.ok() && !(path.endsWith('/config') && body.error?.code === 'sources_unavailable')) throw new Error(JSON.stringify(calls));
      return body;
    };
    all[env]={};
    for (const [name,words,channels] of [
      ['QA 채널 확장',['에어컨 청소','제습기','qa-empty'],env==='blocked'?['threads']:env==='unavailable'?['youtube_vlog','naver_kin','cook82']:['youtube_vlog','threads','naver_kin','cook82']],
      ['QA 빈 결과',['qa-empty'],env==='unavailable'?['youtube_vlog','naver_kin','cook82']:['youtube_vlog','threads','naver_kin','cook82']],
      ['QA 샘플',['에어컨 청소'],['fixture']]
    ]) {
      const {sid}=await request('POST','/context',{bk:name,oneLiner:'생활 가전 사용 경험을 조사하는 QA 프로젝트',researchQuestion:{text:'생활 가전을 사용하는 경험은 어떠한가?'},projectType:{choice:'new'},taskMode:'explore',constraints:[],channels,productCategory:{l1:'생활가전',source:'user'}});
      for(const kw of words) await request('POST',`/keywords/${sid}/manual`,{kw,axis:'physical',sub:'product_physical'});
      await request('PUT',`/crawl/${sid}/config`,{channels});
      await request('PATCH',`/session/${sid}`,{step:'crawling'});
      const session=await request('GET',`/session/${sid}`);
      all[env][name]={sid,requestedKeywords:words,keywords:session.data.keywords,channels};
    }
  }
  page.qaSessions=all; return {time:new Date().toISOString(),sessions:all,calls};
}
