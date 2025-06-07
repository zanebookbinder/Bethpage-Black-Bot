import { Button, TextField, View, Heading } from '@aws-amplify/ui-react';
import { useState } from 'react';
import { isValidDateWithinOneYear } from '../utils';

export default function ExtraPlayableDaysInput({ formData, setFormData, onErrorsChange }) {
  const dates = formData?.extra_playable_days || [''];

  const [dateErrors, setDateErrors] = useState(dates.map(() => false))

  const updateDate = (index, value) => {
    const newDates = [...dates];
    newDates[index] = value;
    setFormData(prev => ({ ...prev, extra_playable_days: newDates }));

	const newErrors = [...dateErrors];
    newErrors[index] = !isValidDateWithinOneYear(value);
    setDateErrors(newErrors);
	onErrorsChange(newErrors.some(Boolean));
  };

  const addDate = () => {
    setFormData(prev => ({
      ...prev,
      extra_playable_days: [...prev.extra_playable_days, ''],
    }));
	setDateErrors(prev => [...prev, false]);
  };

  const removeDate = (index) => {
    if (dates.length === 1) return;
    const newDates = dates.filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, extra_playable_days: newDates }));

	const newErrors = dateErrors.filter((_, i) => i !== index);
    setDateErrors(newErrors);
	onErrorsChange(newErrors.some(Boolean));
  };

  return (
    <View marginTop="1rem">
		<Heading level={5}>Extra Playable Days</Heading>
      {dates.map((date, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
          <TextField
            placeholder="e.g. 6/9/2025"
            value={date}
            onChange={(e) => updateDate(i, e.target.value)}
            width="100%"
			errorMessage={dateErrors[i] ? "Invalid date (format M/D/YYYY and within 1 year)" : undefined}
            hasError={dateErrors[i]}
          />
          <Button
            variation="link"
            onClick={() => removeDate(i)}
            isDisabled={dates.length === 1}
            aria-label={`Remove date ${i + 1}`}
          >
            Remove
          </Button>
        </div>
      ))}

      <Button type="button" onClick={addDate} variation="primary" style={{ marginBottom: 12 }} 
	  	isDisabled={dates[dates.length - 1] === ""}>
        Add New Date
      </Button>
    </View>
  );
}