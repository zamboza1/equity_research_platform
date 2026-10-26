export type NAVMode = 'real-estate' | 'resource';
type DraftFields<T> = {[K in keyof T]: number | null};

const realDefaults = {noi:1200, cap_rate:.045, other_assets:500, total_debt:8000, minority_interest:0, preferred_equity:0, shares_outstanding:150};
const resourceDefaults = {reserves:500, value_per_unit:80, production_cost_per_unit:30, exploration_upside:500, liabilities:2000, shares_outstanding:100};

export type NAVDraft = {
    mode: NAVMode;
    real: DraftFields<typeof realDefaults>;
    resource: DraftFields<typeof resourceDefaults>;
};

export const NAV_STORAGE_KEY = 'vertige-nav-v1';
export function initialNAVDraft(): NAVDraft {
    return {mode:'real-estate', real:{...realDefaults}, resource:{...resourceDefaults}};
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// Incomplete drafts are valid saved work. Null means blank, never a zero input.
function hasFields(value: unknown, defaults: Record<string, number>): boolean {
    return isRecord(value) && Object.keys(value).length === Object.keys(defaults).length
        && Object.keys(defaults).every(key => value[key] === null
            || (typeof value[key] === 'number' && Number.isFinite(value[key])));
}

export function parseNAVDraft(text: string): NAVDraft {
    const saved: unknown = JSON.parse(text);
    if (!isRecord(saved) || saved.version !== 1 || !isRecord(saved.draft)
        || (saved.draft.mode !== 'real-estate' && saved.draft.mode !== 'resource')
        || !hasFields(saved.draft.real, realDefaults)
        || !hasFields(saved.draft.resource, resourceDefaults)) {
        throw new Error('The saved NAV draft is invalid or uses an unsupported version. Your current inputs are unchanged.');
    }
    return saved.draft as NAVDraft;
}

export function saveNAVDraft(storage: Pick<Storage, 'setItem'>, draft: NAVDraft): void {
    storage.setItem(NAV_STORAGE_KEY, JSON.stringify({version:1, saved_at:new Date().toISOString(), draft}));
}

export function restoreNAVDraft(storage: Pick<Storage, 'getItem'>): NAVDraft {
    const saved = storage.getItem(NAV_STORAGE_KEY);
    if (saved === null) throw new Error('No saved NAV draft in this browser.');
    try {
        return parseNAVDraft(saved);
    } catch {
        throw new Error('The saved NAV draft is invalid or uses an unsupported version. Your current inputs are unchanged.');
    }
}
