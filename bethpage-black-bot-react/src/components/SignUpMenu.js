import { useState } from 'react';
import {
  View,
  Heading,
  Alert,
  Text,
  TextField,
  Button,
  Flex,
} from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { API_BASE_URL } from "../utils";

export default function SignupMenu() {
  const [email, setEmail] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "email": email }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setStatusMessage('Failed to register user. ' + data.message)
        setStatusType('error');
      } else {
        setStatusMessage('Successfully registered! Please check your email to verify your account and update your settings.');
        setStatusType('success');
        setEmail('');
      }
    } catch (error) {
      console.error('Registration error:', error);
      setStatusMessage('Something went wrong. Please try again.');
      setStatusType('error');
    }
  };

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

        <Flex as="form" direction="column" gap="1rem" onSubmit={handleSubmit}>
          <TextField
            label="Email address"
            name="email"
            type="email"
            placeholder="tiger.woods@nike.com"
            isRequired
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button variation="primary" type="submit" width={'fit-content'}>
            Sign Up
          </Button>
        </Flex>

        {statusType && (
          <Alert variation={statusType} hasIcon={true} borderRadius={10}>
            {statusMessage}
          </Alert>
        )}

        <Flex direction="column" paddingTop="1rem" gap="1rem">
          <Alert variation="info" hasIcon={true} borderRadius={10} width={'fit-content'}>
            <Heading level={4}>How It Works</Heading>
          </Alert>
          <Text color="font.secondary">
            Bethpage Black Bot monitors tee time availability on the Bethpage
            reservation system. When a new tee time becomes available for your
            chosen days and times, you'll receive an email alert so you can
            scoop it up before anyone else!
            <br />
            <br />
            You can adjust your notification preferences or pause your
            notifications at any time by getting a secure one-time link sent to
            your email.
          </Text>
        </Flex>
      </Flex>
    </View>
  );
}
