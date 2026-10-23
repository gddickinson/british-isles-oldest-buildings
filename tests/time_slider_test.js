// node tests/time_slider_test.js — the Map page's year slider (app/static/time_slider.js): scale and what stands when
const fs = require("fs"), vm = require("vm"), assert = require("assert");
const ctx = { document: {}, Event: class {}, setTimeout, clearInterval, setInterval };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(__dirname + "/../app/static/time_slider.js", "utf8") + "\nthis.TS = TimeSlider;", ctx);
const T = ctx.TS;
for (const y of [-3000, 43, 1066, 1500, 1850, 1999]) assert.ok(Math.abs(T.toYear(T.toPos(y)) - y) <= 1, String(y));
assert.strictEqual(T.toYear(0), -4000);
assert.strictEqual(T.label(-500), "500 BC");
assert.strictEqual(T.label(700), "AD 700");
assert.strictEqual(T.endOf({ date_text: "1836–1987" }), 1987);
assert.strictEqual(T.endOf({ date_text: "between 1800 and 1839" }), null);
assert.ok(T.standing({ year_start: 1836, date_text: "1836–1987" }, 1900));
assert.ok(!T.standing({ year_start: 1836, date_text: "1836–1987" }, 1990));
assert.ok(!T.standing({ year_start: 1836 }, 1800));
assert.ok(!T.standing({ year_start: null }, 2000));
console.log("time_slider: all checks passed");
