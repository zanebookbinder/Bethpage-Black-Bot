import { Flex, Text, View } from '@aws-amplify/ui-react';

export function CurrentTeeTime({ date, time, players }) {
  const [dayOfWeek, ...rest] = date.split(' ');
  const shortDate = rest.join(' '); // e.g., "June 4th"

  return (
    <Flex
      direction="row"
      borderRadius="1rem"
      backgroundColor="#f3f4f6"
      padding="1rem"
      alignItems="center"
      justifyContent="space-between"
      boxShadow="0 4px 10px rgba(0,0,0,0.1)"
      maxWidth="300px"
    >
      {/* Left: Players */}
      <View textAlign="center" marginRight="1rem">
        <Text fontSize="xl" fontWeight="bold" lineHeight="1">
          {players}
        </Text>
        <Text fontSize="small" color="gray">
          Players
        </Text>
      </View>

      {/* Right: Date and Time */}
      <View >
        <Text fontSize="medium" fontWeight="medium">
          {shortDate}
        </Text>
        <Text fontSize="large" color="gray">
          {dayOfWeek} @ {time}
        </Text>
      </View>
    </Flex>
  );
};