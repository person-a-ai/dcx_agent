import { contextLabels, IMPORT_ONLY_CHANNELS } from '@/lib/contextLabels';

const importOnly: readonly string[] = IMPORT_ONLY_CHANNELS;

export function stageZeroChannelOptions(selected: readonly string[], internalTools: boolean) {
  return Object.entries(contextLabels.channels)
    .map(([value, label]) => ({ value, label }))
    .filter(option => (internalTools || option.value !== 'fixture')
      && (!importOnly.includes(option.value) || selected.includes(option.value)));
}
