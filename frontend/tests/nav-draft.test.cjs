const {test, after} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {mkdtempSync, rmSync} = require('node:fs');
const {tmpdir} = require('node:os');
const path = require('node:path');

// Compile the actual utility with the project's TypeScript; no new test dependency.
const output = mkdtempSync(path.join(tmpdir(), 'vertige-nav-tests-'));
after(() => rmSync(output, {recursive:true, force:true}));
execFileSync(process.execPath, [require.resolve('typescript/lib/tsc.js'),
    path.resolve(__dirname, '../utils/navDraft.ts'), '--outDir', output,
    '--module', 'commonjs', '--target', 'es2017', '--skipLibCheck'], {stdio:'pipe'});
const {initialNAVDraft, saveNAVDraft, restoreNAVDraft, NAV_STORAGE_KEY} = require(path.join(output, 'navDraft.js'));

function memoryStorage() {
    const records = new Map();
    return {setItem:(key,value)=>records.set(key,value), getItem:key=>records.get(key) ?? null};
}

test('a saved draft preserves separate model inputs, mode, blanks and legitimate zeros', () => {
    const draft = initialNAVDraft();
    Object.assign(draft.real, {noi:.6, cap_rate:.05, total_debt:7, other_assets:0, shares_outstanding:1});
    Object.assign(draft.resource, {reserves:2, value_per_unit:null, liabilities:0});
    draft.mode = 'resource';
    const storage = memoryStorage();
    saveNAVDraft(storage, draft);
    const restored = restoreNAVDraft(storage);
    assert.deepEqual(restored, draft);
    assert.equal(restored.resource.value_per_unit, null);
    assert.equal(restored.resource.liabilities, 0);
    draft.real.noi = 10;
    assert.equal(restoreNAVDraft(storage).real.noi, .6);
});

test('missing, malformed and incompatible storage never supplies replacement defaults', () => {
    const storage = memoryStorage();
    assert.throws(()=>restoreNAVDraft(storage), /No saved NAV draft/);
    const valid = {version:1, draft:initialNAVDraft()};
    const invalid = ['{', '{}', 'null', JSON.stringify({...valid, version:2}),
        JSON.stringify({...valid, draft:{...valid.draft, mode:['real-estate']}}),
        JSON.stringify({...valid, draft:{...valid.draft, real:{noi:.6}}}),
        JSON.stringify({...valid, draft:{...valid.draft, resource:{...valid.draft.resource, reserves:'2'}}}),
        JSON.stringify(valid).replace('1200', '1e400')];
    for (const raw of invalid) {
        storage.setItem(NAV_STORAGE_KEY, raw);
        assert.throws(()=>restoreNAVDraft(storage), /invalid or uses an unsupported version/);
        assert.equal(storage.getItem(NAV_STORAGE_KEY), raw);
    }
});

test('storage read and write failures propagate without claiming success or changing inputs', () => {
    const draft = initialNAVDraft();
    const before = JSON.stringify(draft);
    const storage = {getItem(){throw new Error('blocked read');}, setItem(){throw new Error('quota exceeded');}};
    assert.throws(()=>saveNAVDraft(storage, draft), /quota exceeded/);
    assert.throws(()=>restoreNAVDraft(storage), /blocked read/);
    assert.equal(JSON.stringify(draft), before);
});

test('new page drafts do not share mutable example input objects', () => {
    const first = initialNAVDraft();
    const second = initialNAVDraft();
    first.real.noi = null;
    first.resource.shares_outstanding = 42;
    assert.equal(second.real.noi, 1200);
    assert.equal(second.resource.shares_outstanding, 100);
});
