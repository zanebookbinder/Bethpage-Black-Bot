import React, { useEffect, useState } from 'react';
import {
  View,
  Heading,
  TextField,
  Button,
  Flex,
  Alert,
  CheckboxField,
  SwitchField
} from '@aws-amplify/ui-react';
import { convertTo12Hour, convertTo24Hour } from '../utils';
import ExtraPlayableDaysInput from './ExtraPlayableDaysInput';

export default function UpdateConfiguration() {

  const [formData, setFormData] = useState({
	playable_days_of_week: [],
    earliest_playable_time: convertTo24Hour('8:00am'),
    extra_playable_days: [''],
    include_holidays: false,
    minimum_minutes_before_sunset: '',
    min_players: '',
  });

  const [errors, setErrors] = useState(false);

  const [statusMessage, setStatusMessage] = useState('');
  useEffect(() => {
	if (!statusMessage) return; // no status, no timer
  
	const timer = setTimeout(() => {
		setStatusMessage("");
	}, 3000);
  
	// Cleanup on unmount or before next effect run
	return () => clearTimeout(timer);
  }, [statusMessage]);

  const apiBase = process.env.REACT_APP_API_URL;

  useEffect(() => {
      fetchConfig(apiBase);
  }, []);

  const fetchConfig = async (base) => {
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

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

	if (errors)
	{
		setStatusMessage('Errors in configuration. Updates not saved.');
		return;
	}

	const formattedExtraDates = formData.extra_playable_days
    .map(d => d.trim())
    .filter(d => d.length > 0);

    const payload = {
	  playable_days_of_week: formData.playable_days_of_week,
	  earliest_playable_time: convertTo12Hour(formData.earliest_playable_time),
      extra_playable_days: formattedExtraDates,
      include_holidays: formData.include_holidays,
      minimum_minutes_before_sunset: parseInt(formData.minimum_minutes_before_sunset, 10),
      min_players: parseInt(formData.min_players, 10),
    };

    const res = await fetch(`${apiBase}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    setStatusMessage(res.ok ? '✅ Config saved!' : '❌ Failed to save config');
  };

  const pauseNotifications = () =>
    fetch(`${apiBase}/pause`, { method: 'POST' }).then(() =>
      alert('Notifications paused')
    );

  const resumeNotifications = () =>
    fetch(`${apiBase}/resume`, { method: 'POST' }).then(() =>
      alert('Notifications resumed')
    );

  return (
    <View maxWidth="600px" margin="auto" padding="2rem" >
      <Heading level={3}>Bethpage Black Bot Config</Heading>

      <Flex gap="1rem" marginTop="1.5rem" wrap="wrap">
        <Button onClick={pauseNotifications}>Pause Notifications</Button>
        <Button onClick={resumeNotifications} variation="primary">
          Resume Notifications
        </Button>
      </Flex>

      <View as="form" onSubmit={handleSubmit} marginTop="2rem">
	  <Flex direction="column" gap="2rem">
		<View marginTop="1rem">
			<Heading level={5}>Playable Days of the Week</Heading>
			<Flex wrap="wrap" gap="1rem">
				{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
				<CheckboxField
					key={day}
					label={day}
					name="playable_days_of_week"
					value={day}
					checked={formData.playable_days_of_week.includes(day)}
					onChange={(e) => {
					const { checked, value } = e.target;
					setFormData((prev) => {
						const updatedDays = checked
						? [...prev.playable_days_of_week, value]
						: prev.playable_days_of_week.filter((d) => d !== value);
						return { ...prev, playable_days_of_week: updatedDays };
					});
					}}
				/>
				))}
			</Flex>
		</View>

		<View marginTop="1rem">
			<Heading level={5}>Earliest Playable Time</Heading>
			<TextField
				name="earliest_playable_time"
				type="time"
				value={formData.earliest_playable_time}
				onChange={handleChange}
				required
			/>
		</View>

		<ExtraPlayableDaysInput formData={formData} setFormData={setFormData}onErrorsChange={setErrors} />

		<View marginTop="1rem">
			<Heading level={5}>Include Holidays</Heading>
			<SwitchField
				isChecked={formData.include_holidays}
				onChange={(e) =>
					setFormData((prev) => ({
					...prev,
					include_holidays: e.target.checked,
					}))
				}
			/>
		</View>

		<View marginTop="1rem">
			<Heading level={5}>Minimum Minutes Before Sunset</Heading>
			<TextField
			name="minimum_minutes_before_sunset"
			type="number"
			min={0}
			value={formData.minimum_minutes_before_sunset}
			onChange={handleChange}
			required
			/>
		</View>

		<View marginTop="1rem">
			<Heading level={5}>Minimum Players</Heading>
			<TextField
			name="min_players"
			type="number"
			min={1}
			value={formData.min_players}
			onChange={handleChange}
			required
			/>
		</View>

        <Button type="submit" marginTop="1.5rem" variation="primary">
          Save Config
        </Button>
	  </Flex>
      </View>

      {statusMessage && (
        <Alert variation="info" marginTop="1rem">
          {statusMessage}
        </Alert>
      )}
    </View>
  );
}