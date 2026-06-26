import { filterOutPastDates, normalizeDate, isValidDate } from './utils';

// Helpers to build dates relative to "today" so the tests don't go stale.
const toYMD = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
};
const daysFromNow = (n) => {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return d;
};

describe('normalizeDate', () => {
    it('passes through YYYY-MM-DD unchanged', () => {
        expect(normalizeDate('2026-07-04')).toBe('2026-07-04');
    });

    it('converts legacy M/D/YYYY to YYYY-MM-DD with zero-padding', () => {
        expect(normalizeDate('7/4/2026')).toBe('2026-07-04');
    });

    it('returns empty string for blank or non-string input', () => {
        expect(normalizeDate('')).toBe('');
        expect(normalizeDate(null)).toBe('');
        expect(normalizeDate(undefined)).toBe('');
    });
});

describe('filterOutPastDates', () => {
    it('keeps today and future dates', () => {
        const future = toYMD(daysFromNow(10));
        const today = toYMD(daysFromNow(0));
        expect(filterOutPastDates([future, today])).toEqual([future, today]);
    });

    it('removes past dates', () => {
        const past = toYMD(daysFromNow(-5));
        const future = toYMD(daysFromNow(5));
        expect(filterOutPastDates([past, future])).toEqual([future]);
    });

    it('removes blank and invalid entries', () => {
        const future = toYMD(daysFromNow(3));
        expect(filterOutPastDates(['', '   ', 'not-a-date', future])).toEqual([future]);
    });

    it('normalizes legacy slash-format dates while filtering', () => {
        const future = daysFromNow(7);
        const slash = `${future.getMonth() + 1}/${future.getDate()}/${future.getFullYear()}`;
        expect(filterOutPastDates([slash])).toEqual([toYMD(future)]);
    });

    it('returns an empty array for non-array input', () => {
        expect(filterOutPastDates(undefined)).toEqual([]);
        expect(filterOutPastDates(null)).toEqual([]);
    });
});

describe('isValidDate', () => {
    it('accepts today and future, rejects past and malformed', () => {
        expect(isValidDate(toYMD(daysFromNow(1)))).toBe(true);
        expect(isValidDate(toYMD(daysFromNow(0)))).toBe(true);
        expect(isValidDate(toYMD(daysFromNow(-1)))).toBe(false);
        expect(isValidDate('2026/01/01')).toBe(false);
        expect(isValidDate('')).toBe(false);
    });
});
