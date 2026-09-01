import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const raiz = new URL('../../', import.meta.url);

test('frontend não carrega o recomendador textual antigo', async () => {
  const oauth = await readFile(new URL('frontend/lib/spotify/oauth.ts', raiz), 'utf8');
  assert.doesNotMatch(oauth, /findRecommendations|\/search\?/);
});

test('manifesto do frontend não mantém D1 ou Drizzle', async () => {
  const manifesto = JSON.parse(await readFile(new URL('frontend/package.json', raiz), 'utf8'));
  assert.equal(manifesto.dependencies?.['drizzle-orm'], undefined);
  assert.equal(manifesto.devDependencies?.wrangler, undefined);
});

test('interface identifica exemplos como não reais', async () => {
  const pagina = await readFile(new URL('frontend/app/page.tsx', raiz), 'utf8');
  assert.match(pagina, /Dados ilustrativos/);
  assert.match(pagina, /não vou fingir que consigo recomendar/);
});

