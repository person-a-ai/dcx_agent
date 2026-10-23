import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { deriveCrawlLoad, limits, VLOG_DEFAULTS, vlogConfigError } from './crawlConfig';
import { skipReasonLabel, skipRows, vlogDocsLabel } from './finishPartial';
import { Settings, channelDescriptions } from '../../components/crawl/Settings';
import { Progress } from '../../components/crawl/Progress';
import type { CrawlStatus } from '../api/crawl';

const sources = ['youtube_vlog', 'threads', 'naver_kin', 'cook82'];
const config = () => deriveCrawlLoad({ data: { crawlConfig: { channels: sources } } }, {
  defaults: { adWords: [], excludeSources: [] }, available_sources: sources, gate: null,
}, null, false).config;
const status = (report: CrawlStatus['report'] = null): CrawlStatus => ({
  status: report ? 'done' : 'running', kind: 'detail', gate: null, estimate: null,
  channels: { youtube_vlog: { status: 'done' }, naver_kin: { status: 'done' }, threads: { status: 'done' } },
  progress: { done: 12, target: 15, full: 12, snippet: 0, restricted: 0, per_minute: 3,
    list_tasks: {}, channels: {}, skipped: { youtube_vlog: { no_ko_captions: 2, deleted: 1 }, naver_kin: { deleted: 1 } } },
  defaults: { adWords: [], excludeSources: [] }, added_keywords_count: 0, collection_keywords: [], report,
});

describe('channel expansion', () => {
  it('uses backend channel defaults including the unknown-source fallback', () => {
    for (const [source, concurrency, min_interval_s] of [
      ['youtube_vlog', 2, 0], ['threads', 1, 2], ['naver_kin', 1, 0.5], ['cook82', 1, 0.5], ['unknown', 4, 0],
    ] as const) expect(limits(source)).toEqual({ concurrency, min_interval_s, max_per_keyword: 1000 });
    expect(VLOG_DEFAULTS).toEqual({ videos_per_keyword: 20, min_duration_s: 60, max_duration_s: 3600 });
  });

  it('labels known skip reasons and preserves unknown reasons', () => {
    expect(['no_ko_captions', 'deleted', 'restricted', 'blocked', 'parse_error', 'other'].map(skipReasonLabel))
      .toEqual(['한국어 자막 없음', '삭제된 글', '회원 전용 · 폐쇄 카페(제외)', '차단으로 여기까지 마침', '파싱 오류로 여기까지 마침', 'other']);
  });

  it('sorts positive reason counts and falls back only when the reason map is absent', () => {
    const report = { channels: {
      youtube_vlog: { skip_reasons: { no_ko_captions: 37, deleted: 2, empty: 0, invalid: -1 }, skipped: 100 },
      threads: { skip_reasons: { blocked: 9 } },
      clien: { skipped: 4, skip_reason: 'parse_error' },
      ppomppu: { skipped: 3 },
      cook82: { skip_reasons: {}, skipped: 20 },
      naver_kin: {},
    } };
    expect(skipRows(report)).toEqual([
      { source: 'youtube_vlog', reason: 'no_ko_captions', count: 37 },
      { source: 'threads', reason: 'blocked', count: 9 },
      { source: 'clien', reason: 'parse_error', count: 4 },
      { source: 'ppomppu', reason: 'blocked', count: 3 },
      { source: 'youtube_vlog', reason: 'deleted', count: 2 },
    ]);
    expect(skipRows({ channels: {} })).toEqual([]);
  });

  it('labels video and segment counts in that order with Korean number formatting', () => {
    expect(vlogDocsLabel(47, 12)).toBe('영상 12개 → 구간 47');
    expect(vlogDocsLabel(2510, 412)).toBe('영상 412개 → 구간 2,510');
    expect(vlogDocsLabel(0, 0)).toBe('영상 0개 → 구간 0');
  });

  it('labels only segments when a legacy report has no unique video count', () => {
    expect(vlogDocsLabel(2510)).toBe('구간 2,510');
  });

  it.each([
    { videos_per_keyword: 0 }, { videos_per_keyword: 1.5 }, { min_duration_s: -1 },
    { min_duration_s: 600, max_duration_s: 600 }, { min_duration_s: 1800, max_duration_s: 600 },
  ])('explains invalid vlog settings: %j', patch => {
    expect(vlogConfigError({ ...VLOG_DEFAULTS, ...patch })).toBeTruthy();
  });

  it('accepts the zero minimum and normal saved duration ranges', () => {
    expect(vlogConfigError({ videos_per_keyword: 5, min_duration_s: 0, max_duration_s: 60 })).toBe('');
    expect(vlogConfigError({ videos_per_keyword: 5, min_duration_s: 120, max_duration_s: 1800 })).toBe('');
  });

  it('describes the new channels and the exclusion of restricted cafe posts', () => {
    for (const source of sources) expect(channelDescriptions[source]).toBeTruthy();
    expect(channelDescriptions.threads).toContain('약 20건');
    expect(channelDescriptions.naver_cafe).toBe('검색 결과 화면 · 본문 (회원 전용 글은 제외)');
  });

  it('renders new badges, labeled minute inputs, the keyword hint and unavailable Threads', () => {
    const html = renderToStaticMarkup(createElement(Settings, {
      config: config(), onChange: () => {}, availableSources: sources.filter(s => s !== 'threads'), axes: {}, disabled: false,
    }));
    expect(html.match(/새 채널/g)).toHaveLength(4);
    expect(html).toContain('aria-label="수집 채널"');
    expect(html).toContain('Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다.');
    const threads = html.match(/<tr[^>]*><td>Threads[\s\S]*?<\/tr>/)?.[0] ?? '';
    expect(threads).toContain('disabled=""');
    expect(threads).toContain('aria-checked="false"');
    expect(html).toContain('유튜브 브이로그는 검색어 뒤에 &quot;브이로그&quot;를 붙입니다.');
    expect(html).toMatch(/최소 길이\(분\)<\/label><input[^>]+value="1"/);
    expect(html).toMatch(/최대 길이\(분\)<\/label><input[^>]+value="60"/);
  });

  it('hides vlog inputs when disabled as a channel and locks them in past versions', () => {
    const props = { config: config(), onChange: () => {}, availableSources: sources, axes: {}, disabled: true };
    const html = renderToStaticMarkup(createElement(Settings, props));
    expect(html).toMatch(/<fieldset disabled="">[\s\S]*최소 길이\(분\)[\s\S]*<\/fieldset>/);
    expect(renderToStaticMarkup(createElement(Settings, { ...props, config: { ...props.config, channels: ['threads'] } })))
      .not.toContain('최소 길이(분)');
  });

  it('shows inline validation even while advanced settings are collapsed', () => {
    const html = renderToStaticMarkup(createElement(Settings, {
      config: config(), onChange: () => {}, availableSources: sources, axes: {}, disabled: false,
      vlogError: '최소 길이는 최대 길이보다 작아야 합니다.',
    }));
    expect(html).toContain('role="alert"');
    expect(html).toContain('최소 길이는 최대 길이보다 작아야 합니다.');
    const page = readFileSync('src/app/pipeline/crawling/page.tsx', 'utf8');
    expect(page).toContain('vlogConfigError(config.youtube_vlog)');
    expect(page).toContain('!vlogError');
    expect(page).toContain('vlogError={vlogError}');
    expect(page).toContain("config.channels.includes('threads')");
    expect(page).toContain('키워드당 약 20건입니다.');
    expect(page).toContain('영상 1개가 문서 여러 건이 됩니다.');
    expect(page).toContain("pausedChannels.includes('threads')");
    expect(page).toContain('로그인은 시도하지 않습니다.');
  });

  it('renders progress skip totals with their leading reason and a dash for no skips', () => {
    const html = renderToStaticMarkup(createElement(Progress, { status: status() }));
    expect(html).toContain('aria-label="채널별 수집 상태"');
    expect(html).toContain('<th>건너뜀</th>');
    expect(html).toContain('3 (자막 없음)');
    expect(html).toContain('1 (삭제된 글)');
    expect(html).toMatch(/Threads<\/th>[\s\S]*?<td>—<\/td><\/tr>/);
  });

  it.each(['수집 채널', '채널별 건너뛴 사유'])('keeps %s in a named keyboard-accessible horizontal scroll region', label => {
    const html = label === '수집 채널'
      ? renderToStaticMarkup(createElement(Settings, {
        config: config(), onChange: () => {}, availableSources: sources, axes: {}, disabled: false,
      }))
      : renderToStaticMarkup(createElement(Progress, { status: status({
        channels: { youtube_vlog: {
          docs: 0, share: 0, status: 'done', errors_top: [], skip_reasons: { no_ko_captions: 3 },
        } },
        totals: { doc_count: 0 }, matrix: {},
      }) }));
    const region = html.match(new RegExp(`<div([^>]*)><table[^>]*aria-label="${label}"[^>]*>[\\s\\S]*?</table></div>`));
    expect(region).not.toBeNull();
    expect(region?.[1]).toContain('class="crawl-channel-scroll"');
    expect(region?.[1]).toContain('role="region"');
    expect(region?.[1]).toContain(`aria-label="${label} 스크롤"`);
    expect(region?.[1]).toContain('tabindex="0"');
  });

  it('limits channel table minimum widths to narrow screens and leaves cells free to wrap', () => {
    const css = readFileSync('src/components/crawl/crawl.css', 'utf8');
    const narrowRule = /@media\s*\(max-width:\s*768px\)\s*\{\s*\.crawl-channel-scroll \.ds-tbl\s*\{\s*min-width:\s*600px\s*;?\s*\}\s*\}/;
    expect(css).toMatch(narrowRule);
    expect(css.replace(narrowRule, '')).not.toMatch(/\.crawl-channel-scroll \.ds-tbl\s*\{/);
    expect(css).not.toMatch(/white-space:\s*nowrap/);
    expect(css).toMatch(/\.crawl-channel-scroll\s*\{[^}]*min-width:\s*0\s*;[^}]*overflow-x:\s*auto/);

    // This is a source contract, not a computed-style/browser overflow check.
    const dsCss = readFileSync('src/components/ds/ds.css', 'utf8');
    expect(dsCss).toMatch(/\.ds-tbl td,\s*\.ds-tbl th\s*\{\s*white-space:\s*normal;\s*overflow-wrap:\s*anywhere/);
  });

  it('preserves the progress-status table scroll region and unconditional minimum width', () => {
    const html = renderToStaticMarkup(createElement(Progress, { status: status() }));
    expect(html).toContain('class="crawl-status-scroll" role="region" aria-label="채널별 수집 상태 스크롤" tabindex="0"');
    const css = readFileSync('src/components/crawl/crawl.css', 'utf8');
    expect(css).toMatch(/\.crawl-status-scroll[\s\S]*?\{[^}]*min-width:\s*0\s*;[^}]*overflow-x:\s*auto/);
    expect(css).toMatch(/\.crawl-status-scroll \.ds-tbl\s*\{[^}]*min-width:\s*600px/);
  });

  it('renders reason rows and the unique channel video count despite overlapping keywords', () => {
    const channel = { docs: 47, urls_done: 8, share: 1, status: 'done', errors_top: [], skip_reasons: { no_ko_captions: 3 } };
    const cell = { docs: 20, urls_done: 5, listed: 7, filtered: 0, unique: 7 };
    const html = renderToStaticMarkup(createElement(Progress, { status: status({
      channels: { youtube_vlog: channel }, totals: { doc_count: 47 },
      matrix: { first: { youtube_vlog: cell }, second: { youtube_vlog: { ...cell, docs: 27, urls_done: 7 } } },
    }) }));
    expect(html).toContain('건너뛴 항목');
    expect(html).toContain('aria-label="채널별 건너뛴 사유"');
    expect(html).toContain('한국어 자막 없음');
    expect(html).toContain('3개 영상');
    expect(html).toContain('영상 8개 → 구간 47');
    expect(html).not.toContain('영상 12개 →');
  });

  it('renders only segments for old reports without a unique channel video count', () => {
    const channel = { docs: 6, share: 1, status: 'done', errors_top: [] };
    const cell = { docs: 6, urls_done: 2, listed: 3, filtered: 0, unique: 3 };
    const html = renderToStaticMarkup(createElement(Progress, { status: status({
      channels: { youtube_vlog: channel }, totals: { doc_count: 6 },
      matrix: { first: { youtube_vlog: cell }, second: { youtube_vlog: cell } },
    }) }));
    expect(html).toContain('(구간 6)');
    expect(html).not.toMatch(/영상 [\d,]+개 →/);
  });

  it('renders an explicit zero unique video count', () => {
    const html = renderToStaticMarkup(createElement(Progress, { status: status({
      channels: { youtube_vlog: { docs: 0, urls_done: 0, share: 0, status: 'done', errors_top: [] } },
      totals: { doc_count: 0 }, matrix: {},
    }) }));
    expect(html).toContain('영상 0개 → 구간 0');
  });

  it('renders the empty skips state', () => {
    expect(renderToStaticMarkup(createElement(Progress, { status: status({ channels: {}, matrix: {}, totals: {} }) })))
      .toContain('건너뛴 항목이 없습니다.');
  });
});
