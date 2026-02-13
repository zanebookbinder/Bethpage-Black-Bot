import {
    convertTo24Hour,
    convertTo12Hour,
    isValidDate,
    isValidDateWithinOneYear,
    formatDateToMD,
    formatMDToDate,
    API_BASE_URL,
} from './utils';

describe('utils', () => {
    describe('API_BASE_URL', () => {
        it('should be defined', () => {
            expect(API_BASE_URL).toBe('https://api.bethpage-black-bot.com');
        });
    });

    describe('convertTo24Hour', () => {
        it('should convert 12:00am to 00:00', () => {
            expect(convertTo24Hour('12:00am')).toBe('00:00');
        });

        it('should convert 1:00am to 01:00', () => {
            expect(convertTo24Hour('1:00am')).toBe('01:00');
        });

        it('should convert 12:00pm to 12:00', () => {
            expect(convertTo24Hour('12:00pm')).toBe('12:00');
        });

        it('should convert 1:00pm to 13:00', () => {
            expect(convertTo24Hour('1:00pm')).toBe('13:00');
        });

        it('should convert 11:59pm to 23:59', () => {
            expect(convertTo24Hour('11:59pm')).toBe('23:59');
        });

        it('should handle mixed case', () => {
            expect(convertTo24Hour('3:30PM')).toBe('15:30');
            expect(convertTo24Hour('3:30Am')).toBe('03:30');
        });

        it('should handle times with spaces', () => {
            expect(convertTo24Hour('3:30 pm')).toBe('15:30');
        });
    });

    describe('convertTo12Hour', () => {
        it('should convert 00:00 to 12:00am', () => {
            expect(convertTo12Hour('00:00')).toBe('12:00am');
        });

        it('should convert 01:00 to 1:00am', () => {
            expect(convertTo12Hour('01:00')).toBe('1:00am');
        });

        it('should convert 12:00 to 12:00pm', () => {
            expect(convertTo12Hour('12:00')).toBe('12:00pm');
        });

        it('should convert 13:00 to 1:00pm', () => {
            expect(convertTo12Hour('13:00')).toBe('1:00pm');
        });

        it('should convert 23:59 to 11:59pm', () => {
            expect(convertTo12Hour('23:59')).toBe('11:59pm');
        });

        it('should pad single-digit minutes', () => {
            expect(convertTo12Hour('14:05')).toBe('2:05pm');
        });
    });

    describe('isValidDate', () => {
        beforeEach(() => {
            // Mock today's date to 2026-02-13
            jest.useFakeTimers();
            jest.setSystemTime(new Date('2026-02-13'));
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        it('should return true for today', () => {
            expect(isValidDate('2026-02-13')).toBe(true);
        });

        it('should return true for future dates', () => {
            expect(isValidDate('2026-02-14')).toBe(true);
            expect(isValidDate('2026-12-31')).toBe(true);
            expect(isValidDate('2027-01-01')).toBe(true);
        });

        it('should return false for past dates', () => {
            expect(isValidDate('2026-02-12')).toBe(false);
            expect(isValidDate('2026-01-01')).toBe(false);
            expect(isValidDate('2025-12-31')).toBe(false);
        });

        it('should return false for invalid format', () => {
            expect(isValidDate('02/13/2026')).toBe(false);
            expect(isValidDate('2026-2-13')).toBe(false);
            expect(isValidDate('invalid')).toBe(false);
            expect(isValidDate('')).toBe(false);
        });

        it('should validate date components', () => {
            expect(isValidDate('2026-13-01')).toBe(false); // Invalid month
            expect(isValidDate('2026-02-30')).toBe(false); // Invalid day for February
        });
    });

    describe('isValidDateWithinOneYear', () => {
        beforeEach(() => {
            jest.useFakeTimers();
            jest.setSystemTime(new Date('2026-02-13'));
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        it('should be backwards compatible with isValidDate', () => {
            expect(isValidDateWithinOneYear('2026-02-13')).toBe(true);
            expect(isValidDateWithinOneYear('2026-12-31')).toBe(true);
            expect(isValidDateWithinOneYear('2026-02-12')).toBe(false);
        });
    });

    describe('formatDateToMD', () => {
        it('should convert YYYY-MM-DD to M/D', () => {
            expect(formatDateToMD('2026-03-01')).toBe('3/1');
            expect(formatDateToMD('2026-12-31')).toBe('12/31');
        });

        it('should remove leading zeros', () => {
            expect(formatDateToMD('2026-01-05')).toBe('1/5');
            expect(formatDateToMD('2026-09-09')).toBe('9/9');
        });

        it('should return original string for invalid format', () => {
            expect(formatDateToMD('invalid')).toBe('invalid');
            expect(formatDateToMD('3/1')).toBe('3/1');
        });
    });

    describe('formatMDToDate', () => {
        it('should convert M/D to YYYY-MM-DD with current year', () => {
            const currentYear = new Date().getFullYear();
            expect(formatMDToDate('3/1')).toBe(`${currentYear}-03-01`);
            expect(formatMDToDate('12/31')).toBe(`${currentYear}-12-31`);
        });

        it('should convert M/D to YYYY-MM-DD with specified year', () => {
            expect(formatMDToDate('3/1', 2026)).toBe('2026-03-01');
            expect(formatMDToDate('12/31', 2025)).toBe('2025-12-31');
        });

        it('should pad single-digit months and days', () => {
            expect(formatMDToDate('1/5', 2026)).toBe('2026-01-05');
            expect(formatMDToDate('9/9', 2026)).toBe('2026-09-09');
        });

        it('should return empty string for invalid format', () => {
            expect(formatMDToDate('invalid')).toBe('');
            expect(formatMDToDate('2026-03-01')).toBe('');
            expect(formatMDToDate('')).toBe('');
        });

        it('should handle double-digit months and days', () => {
            expect(formatMDToDate('10/15', 2026)).toBe('2026-10-15');
        });
    });
});
