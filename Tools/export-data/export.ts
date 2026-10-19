(globalThis as any).localStorage = { getItem: () => 'ru', setItem: () => {} };

import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const MOBILE = resolve(process.env.MOBILE_SRC ?? '../../../Warfare1347-mobile/src');
const OUT = resolve('../../Assets/StreamingAssets/Data');

const { TROOPS, traitsOf } = await import(`file://${MOBILE}/data/troops.ts`);

const troops = Object.values(TROOPS as Record<string, any>).map((t) => ({
  id: t.id,
  name: t.name,
  faction: t.faction,
  tier: t.tier,
  line: t.line,
  role: t.role,
  hp: t.hp,
  armor: { cut: round(t.armor.cut), pierce: round(t.armor.pierce), blunt: round(t.armor.blunt) },
  damage: round(t.damage),
  damageType: t.damageType,
  attackTime: round(t.attackTime),
  range: round(t.range),
  speed: round(t.speed),
  crit: round(t.crit),
  dodge: round(t.dodge),
  block: round(t.block),
  hireCost: t.hireCost,
  upgradeCost: t.upgradeCost,
  xpToUpgrade: t.xpToUpgrade,
  upgradesTo: t.upgradesTo,
  traits: [...traitsOf(t)].sort(),
  look: t.look,
  description: t.description,
}));

function round(v: number) {
  return Math.round(v * 1000) / 1000;
}

mkdirSync(OUT, { recursive: true });
writeFileSync(resolve(OUT, 'troops.json'), JSON.stringify({ troops }, null, 2) + '\n', 'utf8');
console.log(`troops: ${troops.length}`);
