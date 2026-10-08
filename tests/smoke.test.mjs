// Run with: node --test tests/smoke.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Script} from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('JavaScript files parse without syntax errors',()=>{for(const p of ['app.js','v3.js','v4.js','v41.js','service-worker.js'])assert.doesNotThrow(()=>new Script(read(p)),p)});
test('HTML loads all JS and CSS assets',()=>{const html=read('index.html');for(const p of ['style.css','v3.css','v4.css','v41.css','app.js','v3.js','v4.js','v41.js'])assert.ok(html.includes('./'+p),p)});
test('service worker precaches all app assets',()=>{const worker=read('service-worker.js');for(const p of ['v41.css','v41.js','index.html','manifest.webmanifest'])assert.ok(worker.includes('./'+p),p)});
test('IndexedDB name remains unchanged for existing users',()=>{assert.ok(read('app.js').includes("indexedDB.open('minha-agenda-v2',1)"));assert.ok(read('v41.js').includes("indexedDB.open('minha-agenda-v2',1)"))});
test('backup imports v2/v3 and calendar events',()=>{const source=read('app.js');assert.ok(source.includes('![2,3].includes(data.version)'));assert.ok(source.includes("'event'"));assert.ok(source.includes("version:3,exportedAt"))});
test('manifest is valid and offline scope stays relative',()=>{const manifest=JSON.parse(read('manifest.webmanifest'));assert.equal(manifest.scope,'./');assert.equal(manifest.start_url,'./')});
