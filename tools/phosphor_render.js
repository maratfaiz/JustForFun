/**
 * Рендерит иконки Phosphor в PNG под имена приложения.
 *
 *   npm pack @phosphor-icons/core && tar xzf phosphor-icons-core-*.tgz
 *   npm install @resvg/resvg-js
 *   node tools/phosphor_render.js package/assets out/raw 1024
 *
 * Дальше tools/phosphor_finish.py собирает две составные иконки и
 * раскладывает цветной вариант.
 */
const fs = require('fs');
const path = require('path');
const { Resvg } = require('@resvg/resvg-js');

const [, , assetsDir, outDir, sizeArg, weightArg] = process.argv;
if (!assetsDir || !outDir) {
  console.error('usage: node phosphor_render.js <assets> <out> [size] [weight]');
  process.exit(1);
}
const size = parseInt(sizeArg || '1024', 10);
const WEIGHT = weightArg || 'fill';
const map = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'phosphor-map.json'), 'utf8'));

// Сердце нужно в двух видах независимо от общего веса. Снежинка и волны —
// линейные формы: в весе fill Phosphor заворачивает их в залитую плашку с
// вырезом, поэтому они остаются контурными.
const FORCE = {
  'icon-heart-outline': 'bold',
  'icon-heart-fill': 'fill',
  'icon-freeze': 'bold',
  'icon-ambience-ocean': 'bold',
};
// детали для составных иконок — в том же весе, что и весь набор
const PARTS = {
  'part-circle': ['circle', WEIGHT],
  'part-star': ['star', 'fill'],
  'part-chat-teardrop': ['chat-teardrop', WEIGHT],
};

fs.mkdirSync(outDir, { recursive: true });

function render(phName, weight, outName) {
  const suffix = weight === 'regular' ? '' : `-${weight}`;
  const file = path.join(assetsDir, weight, `${phName}${suffix}.svg`);
  if (!fs.existsSync(file)) { console.error(`MISSING ${file}`); return; }
  const svg = fs.readFileSync(file, 'utf8').replace(/currentColor/g, '#000000');
  const png = new Resvg(svg, {
    fitTo: { mode: 'width', value: size },
    background: 'rgba(0,0,0,0)',
  }).render().asPng();
  fs.writeFileSync(path.join(outDir, `${outName}.png`), png);
}

for (const [name, phName] of Object.entries(map)) {
  render(phName, FORCE[name] || WEIGHT, name);
}
for (const [name, [phName, weight]] of Object.entries(PARTS)) {
  render(phName, weight, name);
}
fs.writeFileSync(path.join(outDir, 'weight.txt'), WEIGHT);
console.log(`${outDir}: ${Object.keys(map).length} иконок @ ${size}px (${WEIGHT})`);
