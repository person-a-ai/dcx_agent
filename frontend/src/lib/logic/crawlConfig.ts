import { reconcileGateSelection } from './qaFix';
import { availableChannels, localDate } from './finalFix';
import type { CrawlConfig, CrawlSession, CrawlStatus, Limits } from '../api/crawl';

export const parseList = (value: string): string[] => value.split(',').map(s => s.trim()).filter(Boolean);

type Filters = Pick<CrawlConfig, 'adWords' | 'excludeSources'>;
export function prefillFilters(saved: Partial<Filters> | null | undefined, defaults: Filters): Filters {
  return {
    adWords: [...(saved?.adWords ?? defaults.adWords)],
    excludeSources: [...(saved?.excludeSources ?? defaults.excludeSources)],
  };
}

export function enabledChannelConfig<T extends { channels: string[]; perChannel: Record<string, unknown> }>(config: T): T {
  return { ...config, perChannel: Object.fromEntries(Object.entries(config.perChannel).filter(([source]) => config.channels.includes(source))) };
}

export function settingsSources(known: string[], selected: string[], available: string[]): string[] {
  return [...new Set([...known.filter(source => source !== 'fixture' || available.includes(source)), ...available, ...selected])];
}

const DEFAULTS: Record<string, [number, number]> = {
  youtube: [2, 0], youtube_vlog: [2, 0], threads: [1, 2],
  naver_blog: [1, 0.5], naver_cafe: [1, 0.5], naver_kin: [1, 0.5],
  clien: [1, 0.5], ppomppu: [1, 0.5], cook82: [1, 0.5],
};
export const limits = (source: string): Limits => {
  const [concurrency, min_interval_s] = DEFAULTS[source] ?? [4, 0];
  return { concurrency, min_interval_s, max_per_keyword: 1000 };
};
export const VLOG_DEFAULTS = { videos_per_keyword: 20, min_duration_s: 60, max_duration_s: 3600 };

export function vlogConfigError(config: CrawlConfig['youtube_vlog']): string {
  if (!Number.isInteger(config.videos_per_keyword) || config.videos_per_keyword < 1)
    return '키워드당 영상 수는 1 이상의 정수로 입력하세요.';
  if (!Number.isFinite(config.min_duration_s) || config.min_duration_s < 0)
    return '최소 길이는 0분 이상으로 입력하세요.';
  if (!Number.isFinite(config.max_duration_s) || config.min_duration_s >= config.max_duration_s)
    return '최소 길이는 최대 길이보다 작아야 합니다.';
  return '';
}

function normalizeChannelLimits(channels: string[], saved: Record<string, Partial<Limits>> | undefined): Record<string, Limits> {
  return Object.fromEntries(Object.entries(saved ?? Object.fromEntries(channels.map(source => [source, {}])))
    .map(([source, entry]) => [source, { ...limits(source), ...entry }]));
}

export function deriveCrawlLoad(result: {data: CrawlSession}, initial: Pick<CrawlStatus, 'defaults' | 'available_sources' | 'snapshot_id' | 'collectionId'> & {gate: {kw: string}[] | null}, context: {channels: string[]} | null, internal: boolean, now = new Date()) {
  const data = result.data;
  const raw = data.crawlConfig;
  const from = new Date(now);
  from.setDate(from.getDate() - 365);
  const channels = availableChannels(raw?.channels ?? data.projectContext?.channels ?? context?.channels ?? ['naver_cafe', 'naver_blog'], initial.available_sources, internal);
  const base: CrawlConfig = {
    channels,
    dateFrom: raw?.dateFrom === undefined ? localDate(from) : raw.dateFrom,
    dateTo: raw?.dateTo === undefined ? localDate(now) : raw.dateTo,
    ...prefillFilters(raw, initial.defaults),
    includeSources: raw?.includeSources ?? [],
    product_name_filter: raw?.product_name_filter ?? false,
    perChannel: normalizeChannelLimits(channels, raw?.perChannel),
    youtube: raw?.youtube ?? {videos_per_keyword: 20, max_comments: 500},
    youtube_vlog: { ...VLOG_DEFAULTS, ...(raw?.youtube_vlog ?? {}) },
    target_total: raw?.target_total === undefined ? 1000000 : raw.target_total,
  };
  const draft = data.drafts?.crawl;
  const {saved: gate, excluded: selection} = reconcileGateSelection(null, initial, raw?.gateExclusions ?? [], draft?.gate);
  const config = draft?.config
    ? {...draft.config, channels: availableChannels(draft.config.channels, initial.available_sources, internal),
      youtube_vlog: { ...VLOG_DEFAULTS, ...(draft.config.youtube_vlog ?? {}) },
      perChannel: normalizeChannelLimits(draft.config.channels, draft.config.perChannel)} : base;
  return {
    data, config, savedConfig: raw?.channels ? {...base, channels: raw.channels} : null,
    gate, selection, keywords: approvedCrawlKeywords(data),
  };
}

export const approvedCrawlKeywords = (session: CrawlSession | null) => (session?.keywords ?? []).filter(k => k.status === 'approved');
