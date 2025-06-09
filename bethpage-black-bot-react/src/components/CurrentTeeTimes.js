import { useState } from 'react';

export default function CurrentTeeTimes() {
  const [recentTeeTimes, setRecentTeeTimes] = useState([
    {
      "Date": "Thursday June 5th",
      "Holes": "18",
      "Players": "4",
      "Time": "4:50pm"
    },
    {
      "Date": "Thursday June 5th",
      "Holes": "18",
      "Players": "4",
      "Time": "5:20pm"
    }
  ] );
  const [statusMessage, setStatusMessage] = useState('Current Tee Times content goes here.');

  const apiBase = process.env.REACT_APP_API_URL;

  useEffect(() => {
    fetchCurrentTeeTimes(apiBase);
  }, []);

  const fetchCurrentTeeTimes = async (base) => {
    try {
      const res = await fetch(`${base}/getRecentTimes`);
      const data = await res.json();
      setRecentTeeTimes(data['result']);

      if (!data['result'].length) {
        setStatusMessage('No tee times available within the next week, try again later!')
      }
    } catch (err) {
      setStatusMessage('Failed to fetch tee times.');
    }
  };

  return (
    <div>
      {recentTeeTimes && recentTeeTimes.length > 0 ? (
        <div>
          {recentTeeTimes.map((teeTime, index) => (
            <div key={index}>{teeTime.Date}, {teeTime.Holes}, {teeTime.Time}, {teeTime.Players}</div>
          ))}
        </div>
      ) : (
        <p>{statusMessage}</p>
      )}
    </div>
  );
}