import { useEffect, useState } from 'react';
import { CurrentTeeTime } from './CurrentTeeTime';
import { View, Heading, Text, Link, Flex } from '@aws-amplify/ui-react';
import { API_BASE_URL } from '../utils';

export default function CurrentTeeTimes() {
  const [recentTeeTimes, setRecentTeeTimes] = useState([
    // {
    //   "Date": "Thursday June 5th",
    //   "Holes": "18",
    //   "Players": "4",
    //   "Time": "4:50pm"
    // },
    // {
    //   "Date": "Thursday June 5th",
    //   "Holes": "18",
    //   "Players": "4",
    //   "Time": "5:20pm"
    // }
  ] );

  useEffect(() => {
    fetchCurrentTeeTimes();

    // eslint-disable-next-line
  }, []);

  const fetchCurrentTeeTimes = async () => {
    const res = await fetch(`${API_BASE_URL}/getRecentTimes`);
    const data = await res.json();
    setRecentTeeTimes(data['result']);
  };

  return (
    <View>
      {recentTeeTimes && recentTeeTimes.length > 0 ? (
        <View>
          <View>
            {recentTeeTimes.length === 1 ? (
              <Heading color='#283618' level={3}>There is 1 tee time available! 😄</Heading>
            ) : (
              <Heading color='#283618' level={3}>There are {recentTeeTimes.length} times available! 😄</Heading>
            )}
            <Flex gap={4}>
              <Text color="#283618">Get it before it's too late!</Text>
              <Link color='#283618' href="https://foreupsoftware.com/index.php/booking/19765/2432#/teetimes">Book your tee time here</Link>
            </Flex>
          </View>

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
          <Text color='#283618'>Check back later or sign up for alerts!</Text>
        </View>
      )}
    </View>
  );
}