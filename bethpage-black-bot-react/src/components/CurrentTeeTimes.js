import { useEffect, useState } from 'react';
import { CurrentTeeTime } from './CurrentTeeTime';
import { View, Heading, Text } from '@aws-amplify/ui-react';

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
    // fetchCurrentTeeTimes(apiBase);

    // eslint-disable-next-line
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
    <View >
      {recentTeeTimes && recentTeeTimes.length > 0 ? (
        <View>
          {recentTeeTimes.length === 1 ? (
            <View>
              <Heading level={3}>There is 1 tee time available! 😄</Heading>
              <Text>Get it before it's too late!</Text>
            </View>
          ) : (
            <View>
              <Heading level={3}>There are {recentTeeTimes.length} times available! 😄</Heading>
              <Text>Get them before it's too late!</Text>
            </View>
          )}

          <View marginTop="1.5rem">
            {recentTeeTimes.map((teeTime, index) => (
              <View key={index} marginBottom="1rem">
                <CurrentTeeTime
                  date={teeTime.Date}
                  time={teeTime.Time}
                  players={teeTime.Players}
                />
              </View>
            ))}
          </View>
        </View>
      ) : (
        <View>
          <Heading level={3}>There are no tee times available 😔</Heading>
          <Text>Check back later or sign up for alerts!</Text>
        </View>
      )}
    </View>
  );
}