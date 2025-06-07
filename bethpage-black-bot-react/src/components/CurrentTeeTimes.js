

export default function CurrentTeeTimes() {
  
  const fetchCurrentTeeTimes = async (base) => {
      try {
        const res = await fetch(`${base}/config`);
        const data = await res.json();
        setFormData({
      playable_days_of_week: data.playable_days_of_week || [],
          earliest_playable_time: convertTo24Hour(data.earliest_playable_time) || '',
          extra_playable_days: data.extra_playable_days,
          include_holidays: data.include_holidays,
          minimum_minutes_before_sunset: String(data.minimum_minutes_before_sunset || ''),
          min_players: String(data.min_players || ''),
        });
      } catch (err) {
        setStatusMessage('Failed to fetch configuration');
      }
    };

  return <div>Current Tee Times content goes here.</div>;
}
