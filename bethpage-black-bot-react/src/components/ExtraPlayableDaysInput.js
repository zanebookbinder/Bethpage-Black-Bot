import { Button, TextField, View, Heading } from '@aws-amplify/ui-react';
import { useState } from 'react';
import { isValidDateWithinOneYear } from '../utils';

export default function ExtraPlayableDaysInput({ formData, setFormData, onErrorsChange }) {
  const dates = (formData?.extra_playable_days || ['']).map(d => {
    if (d.includes('/')) {
      const [month, day, year] = d.split('/');
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    return d;
  });
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
    <TextField
        width="fit-content"
        descriptiveText="What additional days could you play?"
        inputStyles={{ display: 'none' }}
        gap={"0.25rem"}
    />
      {dates.map((date, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: "1rem" }}>
          <input
            type="date"
            value={date}
            onChange={(e) => updateDate(i, e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #89949f',
              marginRight: '8px',
              fontSize: '1rem',
              minWidth: '180px',
            }}
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
      <Button type="button" onClick={addDate} variation="primary" isDisabled={dates[dates.length - 1] === ""}>
        Add New Date
      </Button>
    </View>
  );
}