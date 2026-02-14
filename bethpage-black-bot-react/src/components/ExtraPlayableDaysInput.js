import { Button, TextField, View, Heading } from '@aws-amplify/ui-react';
import { useState } from 'react';
import { isValidDateWithinOneYear } from '../utils';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import dayjs from 'dayjs';

// Custom MUI theme matching site colors
const customTheme = createTheme({
    palette: {
        primary: {
            main: '#283618', // dark green
        },
        secondary: {
            main: '#bc6c25', // orange
        },
    },
    components: {
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        backgroundColor: '#fefae0',
                        color: '#283618',
                        fontFamily: 'Montserrat, sans-serif',
                        '& fieldset': {
                            borderColor: '#283618',
                            borderWidth: '2px',
                        },
                        '&:hover fieldset': {
                            borderColor: '#283618',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: '#283618',
                            borderWidth: '2px',
                        },
                    },
                    '& .MuiInputLabel-root': {
                        color: '#283618',
                        fontFamily: 'Montserrat, sans-serif',
                        '&.Mui-focused': {
                            color: '#283618',
                        },
                    },
                },
            },
        },
        MuiIconButton: {
            styleOverrides: {
                root: {
                    color: '#283618',
                    '&:hover': {
                        backgroundColor: 'rgba(40, 54, 24, 0.08)',
                    },
                },
            },
        },
        MuiPickersDay: {
            styleOverrides: {
                root: {
                    color: '#283618',
                    '&.Mui-selected': {
                        backgroundColor: '#bc6c25 !important',
                        color: '#fefae0',
                        '&:hover': {
                            backgroundColor: '#8d480b !important',
                        },
                    },
                    '&:hover': {
                        backgroundColor: 'rgba(188, 108, 37, 0.2)',
                    },
                },
            },
        },
        MuiPickersCalendarHeader: {
            styleOverrides: {
                label: {
                    color: '#283618',
                    fontFamily: 'Montserrat, sans-serif',
                    fontWeight: 600,
                },
            },
        },
        MuiDayCalendar: {
            styleOverrides: {
                weekDayLabel: {
                    color: '#283618',
                    fontFamily: 'Montserrat, sans-serif',
                },
            },
        },
    },
});

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
        descriptiveText="What additional days could you play? (past dates will be automatically removed when you save)"
        inputStyles={{ display: 'none' }}
        gap={"0.25rem"}
    />
      {dates.map((date, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: "1rem" }}>
          <ThemeProvider theme={customTheme}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                value={date ? dayjs(date) : null}
                onChange={(newValue) => {
                  if (newValue && newValue.isValid()) {
                    updateDate(i, newValue.format('YYYY-MM-DD'));
                  } else if (!newValue) {
                    updateDate(i, '');
                  }
                }}
                slotProps={{
                  textField: {
                    size: 'small',
                  },
                }}
                sx={{ marginRight: '8px' }}
              />
            </LocalizationProvider>
          </ThemeProvider>
          <Button
            variation="link"
            onClick={() => removeDate(i)}
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