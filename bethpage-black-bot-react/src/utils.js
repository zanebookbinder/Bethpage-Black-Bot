export const API_BASE_URL = "https://api.bethpage-black-bot.com";

export function convertTo24Hour(timeStr) {
    const [time, modifier] = timeStr.toLowerCase().split(/(am|pm)/);
    let [hours, minutes] = time.trim().split(":").map(Number);

    if (modifier === "pm" && hours !== 12) {
        hours += 12;
    }
    if (modifier === "am" && hours === 12) {
        hours = 0;
    }

    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(
        2,
        "0"
    )}`;
}

export function convertTo12Hour(timeStr) {
    let [hours, minutes] = timeStr.split(":").map(Number);
    const ampm = hours >= 12 ? "pm" : "am";
    hours = hours % 12 || 12; // convert 0 to 12 for 12am
    return `${hours}:${String(minutes).padStart(2, "0")}${ampm}`;
}

export function isValidDate(dateStr) {
    // Expecting format: YYYY-MM-DD
    const regex = /^(\d{4})-(\d{2})-(\d{2})$/;
    const match = dateStr.match(regex);
    if (!match) return false;

    const year = parseInt(match[1], 10);
    const month = parseInt(match[2], 10);
    const day = parseInt(match[3], 10);

    // Construct the date
    const date = new Date(year, month - 1, day);

    const now = new Date();
    now.setHours(0, 0, 0, 0); // Normalize to midnight for comparison

    // Only check that it's not in the past
    return date >= now;
}

// Kept for backwards compatibility - now just checks if date is valid and not in the past
export function isValidDateWithinOneYear(dateStr) {
    return isValidDate(dateStr);
}

// Normalize a date string to YYYY-MM-DD, accepting legacy M/D/YYYY ("/"-style) input.
export function normalizeDate(dateStr) {
    if (!dateStr || typeof dateStr !== "string") return "";
    const trimmed = dateStr.trim();
    if (trimmed.includes("/")) {
        const [month, day, year] = trimmed.split("/");
        if (!month || !day || !year) return trimmed;
        return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
    }
    return trimmed;
}

// Remove past (and invalid/blank) dates from a list, returning normalized YYYY-MM-DD strings.
// Used to keep saved-but-now-past dates out of the settings menus when editing.
export function filterOutPastDates(dates) {
    if (!Array.isArray(dates)) return [];
    return dates
        .map(normalizeDate)
        .filter((d) => d.length > 0 && isValidDate(d));
}

export function formatDateToMD(dateStr) {
    // Convert YYYY-MM-DD to M/D format
    const regex = /^(\d{4})-(\d{2})-(\d{2})$/;
    const match = dateStr.match(regex);
    if (!match) return dateStr;

    const month = parseInt(match[2], 10);
    const day = parseInt(match[3], 10);
    return `${month}/${day}`;
}

export function formatMDToDate(mdStr, year = new Date().getFullYear()) {
    // Convert M/D to YYYY-MM-DD for date input
    const parts = mdStr.split('/');
    if (parts.length !== 2) return '';

    const month = parseInt(parts[0], 10);
    const day = parseInt(parts[1], 10);
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}