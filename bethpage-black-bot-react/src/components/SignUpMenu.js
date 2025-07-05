import { View, Heading, Alert, Text, TextField, Button, Flex } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

export default function SignupMenu() {
  return (
    <View margin="auto">
      <Flex direction="column" gap="2rem">
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
            placeholder="tiger.woods@nike.com"
            isRequired
          />
          <Button variation="primary" type="submit">
            Sign Up
          </Button>
        </Flex>

        <Flex direction="column" paddingTop="2rem" gap="1rem">
          <Alert variation="info" hasIcon={true} borderRadius={10}>
              <Heading level={4}>How It Works</Heading>
          </Alert>
          <Text color="font.secondary">
            Bethpage Black Bot monitors tee time availability on the Bethpage
            reservation system. When a new tee time becomes available for your
            chosen days and times, you'll receive an email alert so you can
            scoop it up before anyone else!
            <br /><br />
            You can adjust your notification preferences or pause your notifications
            anytime by getting a secure one-time link sent to your email.
          </Text>
        </Flex>
      </Flex>
    </View>
  );
}