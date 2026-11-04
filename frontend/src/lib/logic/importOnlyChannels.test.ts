import { describe, expect, it } from 'vitest';
import { contextLabels, IMPORT_ONLY_CHANNELS } from '../contextLabels';
import { settingsSources } from './crawlConfig';
import { channelNames } from '../../components/crawl/Settings';
import { stageZeroChannelOptions } from '../../app/pipeline/start/channelOptions';

describe('import-only channels', () => {
  it('have Korean display names', () => {
    expect(contextLabels.channels.daum_cafe).toBe('다음 카페');
    expect(contextLabels.channels.daum_brunch).toBe('브런치');
    expect(channelNames.daum_cafe).toBe('다음 카페');
    expect(channelNames.daum_brunch).toBe('브런치');
  });

  it.each([false, true])('hides unselected import-only channels with internalTools=%s', internalTools => {
    const fresh = stageZeroChannelOptions([], internalTools).map(option => option.value);
    expect(fresh).not.toContain('daum_cafe');
    expect(fresh).not.toContain('daum_brunch');
    expect(fresh).toContain('naver_cafe');
    const imported = stageZeroChannelOptions(['naver_cafe', 'daum_cafe'], internalTools);
    expect(imported).toContainEqual({ value: 'daum_cafe', label: '다음 카페' });
    expect(imported.map(option => option.value)).not.toContain('daum_brunch');
    expect(stageZeroChannelOptions(['daum_brunch'], internalTools))
      .toContainEqual({ value: 'daum_brunch', label: '브런치' });
  });

  it('preserves the internal-tools restriction for fixture channels', () => {
    expect(stageZeroChannelOptions(['fixture'], false).map(option => option.value)).not.toContain('fixture');
    expect(stageZeroChannelOptions([], true).map(option => option.value)).toContain('fixture');
    expect(settingsSources(['fixture', 'naver_cafe'], [], [])).toEqual(['naver_cafe']);
    expect(settingsSources(['fixture'], [], ['fixture'])).toEqual(['fixture']);
  });

  it('are not offered in crawl settings unless selected or available', () => {
    const known = Object.keys(channelNames);
    expect(settingsSources(known, [], ['naver_cafe'])).not.toContain('daum_cafe');
    expect(settingsSources(known, [], ['naver_cafe'])).not.toContain('daum_brunch');
    expect(settingsSources(known, ['daum_cafe'], [])).toContain('daum_cafe');
    expect(settingsSources(known, [], ['daum_brunch'])).toContain('daum_brunch');
    expect(IMPORT_ONLY_CHANNELS).toEqual(['daum_cafe', 'daum_brunch']);
  });
});
