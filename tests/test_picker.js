/**
 * Tests the setup wizard's team picker (app/static/js/sports-autocomplete.js).
 *
 * The picker shows team names but submits ESPN team ids, via a hidden field.
 * That mapping is the only thing standing between what a user picks and what
 * lands in config, and it is invisible from Python — the two bugs this file
 * was written after (the picker writing a stale abbreviation, and then writing
 * a raw id into the visible field) both shipped because nothing exercised it.
 *
 * No network and no browser: a minimal DOM shim is enough, because the logic
 * under test is string mapping, not rendering.
 *
 *     node tests/test_picker.js
 */
const fs = require('fs');
const path = require('path');

// ── DOM shim ──────────────────────────────────────────────────────────────────

function El(tag) {
  this.tag = tag; this.children = []; this.style = {}; this.listeners = {};
  this.value = ''; this.textContent = ''; this.className = '';
  this.attrs = {}; this.parentNode = null; this.nextSibling = null;
}
El.prototype.appendChild = function (c) { this.children.push(c); c.parentNode = this; return c; };
El.prototype.insertBefore = function (n) { this.children.push(n); n.parentNode = this; return n; };
El.prototype.addEventListener = function (ev, fn) { (this.listeners[ev] = this.listeners[ev] || []).push(fn); };
El.prototype.focus = function () {};
El.prototype.fire = function (ev) { (this.listeners[ev] || []).forEach(fn => fn.call(this)); };
// Real innerHTML='' drops the children. Without this the dropdown accumulates
// stale <li> across events and a test can fire a handler from an earlier one.
Object.defineProperty(El.prototype, 'innerHTML', {
  get() { return ''; },
  set(v) { if (v === '') this.children = []; },
});

const LEAGUES = ['mlb', 'nfl', 'nba', 'nhl', 'wnba', 'nwsl', 'mls', 'premier_league'];
// Hidden fields as the server renders them: saved ids.
const SAVED = { mlb: '19', nfl: '4', nba: '13', nhl: '8', wnba: '6',
                nwsl: '21422', mls: '18966', premier_league: '337' };

const visible = {}, hidden = {};
LEAGUES.forEach(function (lg) {
  const parent = new El('div');
  const v = new El('input'); v.attrs['data-league'] = lg; parent.appendChild(v);
  const h = new El('input'); h.attrs.name = lg; h.value = SAVED[lg] || '';
  visible[lg] = v; hidden[lg] = h;
});

let ready = null;
global.document = {
  createElement: t => new El(t),
  addEventListener: (ev, cb) => { if (ev === 'DOMContentLoaded') ready = cb; },
  querySelector: function (sel) {
    let m = sel.match(/data-league="([a-z_]+)"/);
    if (m) return visible[m[1]] || null;
    m = sel.match(/hidden"\]\[name="([a-z_]+)"/);
    if (m) return hidden[m[1]] || null;
    return null;
  },
};

const SOURCE = path.join(__dirname, '..', 'app', 'static', 'js', 'sports-autocomplete.js');
// `const` inside eval does not leak to this scope, so hand the table back out.
eval(fs.readFileSync(SOURCE, 'utf8') + '\nglobal.LEAGUE_TEAMS = LEAGUE_TEAMS;');
ready();

// ── Checks ────────────────────────────────────────────────────────────────────

let failures = 0;
function check(label, actual, expected) {
  const ok = actual === expected;
  if (!ok) { failures++; console.log('  FAIL %s\n       got %j want %j', label, actual, expected); }
  else console.log('  PASS %s', label);
}
function section(s) { console.log('\n' + s); }

section('saved ids render as team names in the visible field');
check('19    -> Dodgers',    visible.mlb.value,  'Dodgers');
check('8     -> Kings',      visible.nhl.value,  'Kings');
check('21422 -> Angel City', visible.nwsl.value, 'Angel City');
check('18966 -> LAFC',       visible.mls.value,  'LAFC');

section('the hidden field keeps the ids — that is what gets submitted');
check('mlb',  hidden.mlb.value,  '19');
check('nwsl', hidden.nwsl.value, '21422');

section('typing resolves to an id');
visible.nhl.value = 'Sharks'; visible.nhl.fire('input');
check('by name',         hidden.nhl.value, '18');
visible.mlb.value = 'SF'; visible.mlb.fire('input');
check('by abbreviation', hidden.mlb.value, '26');

section('several teams per league');
visible.mlb.value = 'Dodgers, Giants'; visible.mlb.fire('input');
check('two teams -> two ids', hidden.mlb.value, '19, 26');
visible.nfl.value = 'Rams, Chiefs, Bengals'; visible.nfl.fire('input');
const parts = hidden.nfl.value.split(',').map(s => s.trim());
check('three teams -> three numeric ids',
      parts.length === 3 && parts.every(p => /^\d+$/.test(p)), true);

section('picking from the dropdown appends rather than replacing');
visible.mlb.value = 'Dodgers, gia';
visible.mlb.fire('input');
const dropdown = visible.mlb.parentNode.children.find(c => c.tag === 'ul');
const option = dropdown.children.find(c => c.textContent.indexOf('Giants') >= 0);
option.listeners['mousedown'][0].call(option, { preventDefault: function () {} });
check('visible shows both names', visible.mlb.value, 'Dodgers, Giants');
check('hidden holds both ids',    hidden.mlb.value,  '19, 26');

section('an unrecognised entry passes through and is flagged');
visible.nba.value = 'Dodgers'; visible.nba.fire('input');  // right name, wrong league
check('passed through to the provider', hidden.nba.value, 'Dodgers');
const note = visible.nba.parentNode.parentNode.children
  .find(c => c.className && c.className.indexOf('text-danger') >= 0);
check('flagged in the UI', note && note.textContent, 'Not recognized: Dodgers');

section('an empty field saves nothing');
visible.wnba.value = ''; visible.wnba.fire('input');
check('empty', hidden.wnba.value, '');

section('ids -> names -> ids is stable');
const before = hidden.nfl.value;
visible.nfl.value = before.split(',').map(s => s.trim())
  .map(id => LEAGUE_TEAMS.nfl.find(t => t.id === id).name).join(', ');
visible.nfl.fire('input');
check('round-trip', hidden.nfl.value, before);

console.log(failures ? '\n' + failures + ' FAILURE(S)' : '\nall picker checks passed');
process.exit(failures ? 1 : 0);
