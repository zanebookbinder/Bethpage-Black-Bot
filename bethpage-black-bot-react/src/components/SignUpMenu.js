import { View, Heading, Text, TextField, Button, Flex } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

export default function SignupMenu() {
  return (
    <View
      margin="auto"
    >
      <Flex direction="column" gap="1.5rem">
        <View>
          <Heading level={3}>Sign up for tee time alerts!</Heading>
          <Text color="font.tertiary">
            Have you always wanted to play Bethpage Black but haven't been 
            able to secure a tee time? Add your email and let Bethpage Black 
            Bot do the work for you!
          </Text>
        </View>

        <Flex as="form" direction="column" gap="1rem">
          <TextField
            label="Email address"
            name="email"
            type="email"
            placeholder="tiger.woods@goat.com"
            isRequired
          />
          <Button variation="primary" type="submit">
            Sign Up
          </Button>
        </Flex>
      </Flex>
    </View>
  );
}
