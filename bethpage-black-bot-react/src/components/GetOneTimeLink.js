import { useState } from 'react';
import {
  View,
  Heading,
  Text,
  TextField,
  Button,
  Flex,
  Alert,
} from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { API_BASE_URL } from '../utils';

export default function GetOneTimeLink() {
  
  const [email, setEmail] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState('info');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isValidEmail = (email) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isValidEmail(email)) {
      setStatusMessage('Please enter a valid email address.');
      setStatusType('error');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await fetch(`${API_BASE_URL}/createOneTimeLink?email=${encodeURIComponent(email)}`);
      const data = await res.json();

      if (res.ok && data.success) {
        setStatusMessage('Check your email for the link to update your settings!');
        setStatusType('success');
        setEmail('');
      } else {
        setStatusMessage('Failed to send link. ' + data.message);
        setStatusType('error');
      }
    } catch (error) {
      setStatusMessage('An error occurred. Please try again.');
      setStatusType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View margin="auto">
      <Flex direction="column" gap="1.5rem">
        <View>
          <Heading level={3}>Get a One-Time Link</Heading>
          <Text color="font.tertiary">
            Enter your email and we’ll send you a one-time link to manage your tee time alerts.
          </Text>
        </View>

        <Flex as="form" direction="column" gap="1rem" onSubmit={handleSubmit}>
          <TextField
            label="Email address"
            name="email"
            type="email"
            placeholder="tiger.woods@nike.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            isRequired
          />
          <Button variation="primary" type="submit" isLoading={isSubmitting}>
            Send Link
          </Button>
        </Flex>

        {statusMessage && (
          <Alert variation={statusType} hasIcon={true}>
            {statusMessage}
          </Alert>
        )}
      </Flex>
    </View>
  );
}