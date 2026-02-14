import { useEffect, useState, useRef } from "react";
import {
    View,
    Heading,
    TextField,
    Text,
    Button,
    Flex,
    Alert,
    CheckboxField,
    Loader,
} from "@aws-amplify/ui-react";
import { convertTo12Hour, convertTo24Hour, isValidDate, formatDateToMD, formatMDToDate } from "../utils";
import ExtraPlayableDaysInput from "./ExtraPlayableDaysInput";
import ToggleButtonPair from "./ToggleButtonPair";
import { API_BASE_URL } from "../utils";
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
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
        MuiClock: {
            styleOverrides: {
                pin: {
                    backgroundColor: '#bc6c25',
                },
            },
        },
        MuiClockPointer: {
            styleOverrides: {
                root: {
                    backgroundColor: '#bc6c25',
                },
                thumb: {
                    backgroundColor: '#bc6c25',
                    borderColor: '#bc6c25',
                },
            },
        },
        MuiClockNumber: {
            styleOverrides: {
                root: {
                    color: '#283618',
                    '&.Mui-selected': {
                        backgroundColor: '#bc6c25',
                        color: '#fefae0',
                    },
                },
            },
        },
        MuiMultiSectionDigitalClock: {
            styleOverrides: {
                root: {
                    '& .MuiMenuItem-root': {
                        '&.Mui-selected': {
                            backgroundColor: '#bc6c25 !important',
                            color: '#fefae0',
                            '&:hover': {
                                backgroundColor: '#8d480b !important',
                            },
                        },
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

export default function UpdateNotificationSettingsForm({ email }) {
    const [loading, setLoading] = useState(true);
    const [userSettings, setUserSettings] = useState({
        playable_days_of_week: [],
        earliest_playable_time: convertTo24Hour("8:00am"),
        extra_playable_days: [""],
        include_holidays: false,
        minimum_minutes_before_sunset: "",
        min_players: "",
        notifications_enabled: false,
        start_date: formatMDToDate("3/1"),  // Default: March 1
        end_date: formatMDToDate("11/30"),  // Default: November 30
    });
    const [notificationsCurrentlyEnabled, setNotificationsCurrentlyEnabled] =
        useState(null);

    const [errors, setErrors] = useState(false);

    const [statusMessage, setStatusMessage] = useState("");
    const [statusLevel, setStatusLevel] = useState("info");

    useEffect(() => {
        fetchConfig();
        // eslint-disable-next-line
    }, []);

    const fetchConfig = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/getUserConfig`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email }),
            });

            const response = await res.json();

            if (response.success) {
                let data = response.result;
                setUserSettings({
                    playable_days_of_week: data.playable_days_of_week || [],
                    earliest_playable_time:
                        convertTo24Hour(data.earliest_playable_time) || "",
                    extra_playable_days: data.extra_playable_days,
                    include_holidays: data.include_holidays,
                    minimum_minutes_before_sunset: String(
                        data.minimum_minutes_before_sunset || ""
                    ),
                    min_players: String(data.min_players || ""),
                    notifications_enabled: data.notifications_enabled,
                    start_date: formatMDToDate(data.start_date || "3/1"),
                    end_date: formatMDToDate(data.end_date || "11/30"),
                });
                setNotificationsCurrentlyEnabled(data.notifications_enabled);
            } else {
                setStatusMessage("Failed to fetch current settings");
                setStatusLevel("warning");
            }
        } catch (err) {
            setStatusMessage("Failed to fetch current settings");
            setStatusLevel("warning");
        } finally {
            setLoading(false);
        }
    };

    const toggleRef = useRef();
    const resetToggleButtons = () => {
        toggleRef.current?.reset();
    };

    const handleChange = (e) => {
        setUserSettings((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (errors) {
            setStatusMessage("Errors found in form. Updates not saved.");
            setStatusLevel("warning");
            return;
        }

        // Filter out past dates automatically instead of showing an error
        const formattedExtraDates = userSettings.extra_playable_days
            .map((d) => d.trim())
            .filter((d) => d.length > 0 && isValidDate(d));

        const payload = {
            playable_days_of_week: userSettings.playable_days_of_week,
            earliest_playable_time: convertTo12Hour(
                userSettings.earliest_playable_time
            ),
            extra_playable_days: formattedExtraDates,
            include_holidays: userSettings.include_holidays,
            minimum_minutes_before_sunset: parseInt(
                userSettings.minimum_minutes_before_sunset,
                10
            ),
            min_players: parseInt(userSettings.min_players, 10),
            notifications_enabled: userSettings.notifications_enabled,
            start_date: formatDateToMD(userSettings.start_date),
            end_date: formatDateToMD(userSettings.end_date),
            email: email,
        };

        const res = await fetch(`${API_BASE_URL}/updateUserConfig`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            setStatusMessage("Settings saved!");
            setStatusLevel("success");
            fetchConfig();
            resetToggleButtons();
        } else {
            setStatusMessage("Failed to save settings");
            setStatusLevel("error");
        }
    };

    const handlePauseOrResume = (shouldNotify) => {
        setUserSettings((prev) => ({
            ...prev,
            notifications_enabled: shouldNotify,
        }));
    };

    const setIncludeHolidays = (includeHolidays) => {
        setUserSettings((prev) => ({
            ...prev,
            include_holidays: includeHolidays,
        }));
    };

    if (loading) {
        return (
            <Loader variation="linear" padding="2rem" filledColor={"#bc6c25"} />
        );
    }

    return (
        <View className="form">
            <Button onClick={() => (window.location.href = '/')} variation="primary" padding=".5rem" marginBottom="1rem">← Go Home</Button>
            <Heading level={3}>Update Notification Settings</Heading>
            <Text fontSize="0.875rem" color="var(--dark-green-text-color)" marginBottom="0.5rem">for {email}</Text>
            <Text marginBottom="2rem">Select the days and times you're able to play!</Text>

            {notificationsCurrentlyEnabled != null &&
            notificationsCurrentlyEnabled ? (
                <ToggleButtonPair
                    ref={toggleRef}
                    start={true}
                    onToggle={(value) => handlePauseOrResume(value)}
                    leftButtonText="Keep Notifications On"
                    rightButtonText="Pause Notifications"
                />
            ) : (
                <ToggleButtonPair
                    ref={toggleRef}
                    start={true}
                    onToggle={(value) => handlePauseOrResume(!value)}
                    leftButtonText="Keep Notifications Paused"
                    rightButtonText="Resume Notifications"
                />
            )}

            <View as="form" onSubmit={handleSubmit} marginTop="2rem">
                <Flex direction="column" gap="1.5rem">
                    <View marginTop="1rem" width="fit-content">
                        <Heading level={5}>Days of the Week</Heading>
                        <TextField
                            width="fit-content"
                            descriptiveText="Which days are you able to play?"
                            inputStyles={{ display: 'none' }}
                            gap={"0.25rem"}
                        />
                        <Flex wrap="wrap" gap="1rem">
                            {[
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                                "Saturday",
                                "Sunday",
                            ].map((day) => (
                                <CheckboxField
                                    key={day}
                                    label={day}
                                    name="playable_days_of_week"
                                    value={day}
                                    checked={userSettings.playable_days_of_week.includes(
                                        day
                                    )}
                                    onChange={(e) => {
                                        const { checked, value } = e.target;
                                        setUserSettings((prev) => {
                                            const updatedDays = checked
                                                ? [
                                                      ...prev.playable_days_of_week,
                                                      value,
                                                  ]
                                                : prev.playable_days_of_week.filter(
                                                      (d) => d !== value
                                                  );
                                            return {
                                                ...prev,
                                                playable_days_of_week:
                                                    updatedDays,
                                            };
                                        });
                                    }}
                                />
                            ))}
                        </Flex>
                    </View>

                    <View marginTop="1rem">
                        <Heading level={5}>Earliest Time</Heading>
                        <Text fontSize="0.875rem" color="var(--dark-green-text-color)" marginBottom="0.5rem">
                            What's the earliest time you'd want to play?
                        </Text>
                        <div style={{ maxWidth: '200px' }}>
                            <ThemeProvider theme={customTheme}>
                                <LocalizationProvider dateAdapter={AdapterDayjs}>
                                    <TimePicker
                                        value={userSettings.earliest_playable_time && userSettings.earliest_playable_time.includes(':')
                                            ? dayjs(`2000-01-01 ${userSettings.earliest_playable_time}`)
                                            : null}
                                        onChange={(newValue) => {
                                            if (newValue && newValue.isValid()) {
                                                setUserSettings(prev => ({
                                                    ...prev,
                                                    earliest_playable_time: newValue.format('HH:mm')
                                                }));
                                            }
                                        }}
                                        slotProps={{
                                            textField: {
                                                size: 'small',
                                                required: true,
                                            },
                                        }}
                                    />
                                </LocalizationProvider>
                            </ThemeProvider>
                        </div>
                    </View>

                    <View marginTop="1rem">
                        <Heading level={5}>Season Start Date</Heading>
                        <Text fontSize="0.875rem" color="var(--dark-green-text-color)" marginBottom="0.5rem">
                            First day of the year you want to receive notifications (e.g., March 1)
                        </Text>
                        <div style={{ maxWidth: '200px' }}>
                            <ThemeProvider theme={customTheme}>
                                <LocalizationProvider dateAdapter={AdapterDayjs}>
                                    <DatePicker
                                        value={userSettings.start_date ? dayjs(userSettings.start_date) : null}
                                        onChange={(newValue) => {
                                            if (newValue) {
                                                setUserSettings(prev => ({
                                                    ...prev,
                                                    start_date: newValue.format('YYYY-MM-DD')
                                                }));
                                            }
                                        }}
                                        slotProps={{
                                            textField: {
                                                size: 'small',
                                                required: true,
                                            },
                                        }}
                                    />
                                </LocalizationProvider>
                            </ThemeProvider>
                        </div>
                    </View>

                    <View marginTop="1rem">
                        <Heading level={5}>Season End Date</Heading>
                        <Text fontSize="0.875rem" color="var(--dark-green-text-color)" marginBottom="0.5rem">
                            Last day of the year you want to receive notifications (e.g., November 30)
                        </Text>
                        <div style={{ maxWidth: '200px' }}>
                            <ThemeProvider theme={customTheme}>
                                <LocalizationProvider dateAdapter={AdapterDayjs}>
                                    <DatePicker
                                        value={userSettings.end_date ? dayjs(userSettings.end_date) : null}
                                        onChange={(newValue) => {
                                            if (newValue) {
                                                setUserSettings(prev => ({
                                                    ...prev,
                                                    end_date: newValue.format('YYYY-MM-DD')
                                                }));
                                            }
                                        }}
                                        slotProps={{
                                            textField: {
                                                size: 'small',
                                                required: true,
                                            },
                                        }}
                                    />
                                </LocalizationProvider>
                            </ThemeProvider>
                        </div>
                    </View>

                    <View marginTop="1rem">
                        <Heading level={5}>
                            Include Holidays?
                        </Heading>
                        <TextField
                            width="fit-content"
                            descriptiveText="Can you play on US Public Holidays?"
                            inputStyles={{ display: 'none' }}
                            gap={"0.25rem"}
                        />
                        <ToggleButtonPair
                            start={userSettings.include_holidays}
                            onToggle={(value) => setIncludeHolidays(value)}
                            leftButtonText="Yup!"
                            rightButtonText="Nope"
                        />
                    </View>

                    <ExtraPlayableDaysInput
                        formData={userSettings}
                        setFormData={setUserSettings}
                        onErrorsChange={setErrors}
                    />

                    <View marginTop="1rem">
                        <Heading level={5} marginBottom={0}>
                            Minimum Minutes Before Sunset
                        </Heading>
                        <TextField
                            name="minimum_minutes_before_sunset"
                            type="number"
                            width="fit-content"
                            min={0}
                            max={300}
                            value={userSettings.minimum_minutes_before_sunset}
                            onChange={handleChange}
                            required
                            descriptiveText="How long before sunset do you want to tee off?"
                            gap={"0.25rem"}
                        />
                    </View>

                    <View marginTop="1rem">
                        <Heading level={5}>Minimum Players</Heading>
                        <TextField
                            name="min_players"
                            type="number"
                            width="fit-content"
                            min={1}
                            max={4}
                            value={userSettings.min_players}
                            onChange={handleChange}
                            required
                            descriptiveText="What's the minimum number of players you'd like to be notified about?"
                            gap={"0.25rem"}
                        />
                    </View>

                    <Button
                        type="submit"
                        marginTop="1.5rem"
                        variation="primary"
                    >
                        Save Settings
                    </Button>
                </Flex>
            </View>

            {statusMessage && (
                <Alert variation={statusLevel} marginTop="1rem">
                    {statusMessage}
                </Alert>
            )}
            <Button onClick={() => (window.location.href = '/')} variation="primary" padding=".5rem" marginTop="1rem">← Go Home</Button>
        </View>
    );
}
