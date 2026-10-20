import { existsSync } from 'node:fs';
import { expect, it } from 'vitest';
import * as api from './api';

it('keeps only the session and chat helpers in the v1 api module', () => {
  expect(Object.keys(api).sort()).toEqual(['getSession', 'saveSession', 'sendChat', 'sendInsightChat']);
});

it('removes orphaned v1 screens and components', () => {
  for (const file of ['src/app/insights/LegacyInsightsPage.tsx', 'src/components/PersonaCard.tsx',
    'src/components/ProgressBar.tsx', 'src/components/Spinner.tsx', 'src/components/SuggestedWordsPanel.tsx']) {
    expect(existsSync(file), file).toBe(false);
  }
});

it('keeps SNAGraph for the v2 WordNetwork', () => {
  expect(existsSync('src/components/SNAGraph.tsx')).toBe(true);
});
