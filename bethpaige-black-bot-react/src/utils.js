export function convertTo24Hour(timeStr) {
		const [time, modifier] = timeStr.toLowerCase().split(/(am|pm)/);
		let [hours, minutes] = time.trim().split(':').map(Number);
		
		if (modifier === 'pm' && hours !== 12) {
			hours += 12;
		}
		if (modifier === 'am' && hours === 12) {
			hours = 0;
		}
		
		return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
	}

export function convertTo12Hour(timeStr) {
	let [hours, minutes] = timeStr.split(':').map(Number);
	const ampm = hours >= 12 ? 'pm' : 'am';
	hours = hours % 12 || 12; // convert 0 to 12 for 12am
	return `${hours}:${String(minutes).padStart(2, '0')}${ampm}`;
	}

export function isValidDateWithinOneYear(dateStr) {
		// Check format with regex: M or MM / D or DD / YYYY
		const regex = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
		const match = dateStr.match(regex);
		if (!match) return false;
	  
		const month = parseInt(match[1], 10);
		const day = parseInt(match[2], 10);
		const year = parseInt(match[3], 10);
	  
		// Create Date object (months are 0-indexed)
		const date = new Date(year, month - 1, day);
	  
		// Check if date is valid
		if (
		  date.getFullYear() !== year ||
		  date.getMonth() !== month - 1 ||
		  date.getDate() !== day
		) {
		  return false;
		}
	  
		const now = new Date();
		const oneYearFromNow = new Date();
		oneYearFromNow.setFullYear(now.getFullYear() + 1);
	  
		return date <= oneYearFromNow && date >= now;
	  }
	  