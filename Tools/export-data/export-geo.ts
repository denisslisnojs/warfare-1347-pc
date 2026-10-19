(globalThis as any).localStorage = { getItem: () => 'ru', setItem: () => {} };
import { writeFileSync, copyFileSync } from 'node:fs';
import { resolve } from 'node:path';
const MOBILE = resolve(process.env.MOBILE_SRC ?? '../../../Warfare1347-mobile/src');
const OUT = resolve('../world/data');
const geo = await import(`file://${MOBILE}/map/geodata.ts`);
writeFileSync(resolve(OUT, 'geodata.json'), JSON.stringify({ ranges: geo.RANGES, rivers: geo.RIVERS, lakes: geo.LAKES, longLakes: geo.LONG_LAKES }, null, 1) + '\n', 'utf8');
copyFileSync(resolve(MOBILE, 'data/land.json'), resolve(OUT, 'land.json'));
console.log('ranges', geo.RANGES.length, 'rivers', geo.RIVERS.length, 'lakes', geo.LAKES.length + geo.LONG_LAKES.length);
