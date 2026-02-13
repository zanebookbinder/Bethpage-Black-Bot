import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UpdateNotificationSettingsForm from './UpdateNotificationSettingsForm';
import { API_BASE_URL } from '../utils';

global.fetch = jest.fn();

// Mock child components
jest.mock('./ExtraPlayableDaysInput', () => {
    return function ExtraPlayableDaysInput({ formData, setFormData, onErrorsChange }) {
        return (
            <div>
                <div>Extra Playable Days Mock</div>
                <button onClick={() => onErrorsChange(false)}>Clear Errors</button>
            </div>
        );
    };
});

jest.mock('./ToggleButtonPair', () => {
    const { forwardRef, useImperativeHandle } = require('react');
    return forwardRef(function ToggleButtonPair({ start, onToggle, leftButtonText, rightButtonText }, ref) {
        useImperativeHandle(ref, () => ({
            reset: () => {},
            getValue: () => start,
        }));
        return (
            <div>
                <button onClick={() => onToggle(true)}>{leftButtonText}</button>
                <button onClick={() => onToggle(false)}>{rightButtonText}</button>
            </div>
        );
    });
});

describe('UpdateNotificationSettingsForm', () => {
    beforeEach(() => {
        fetch.mockClear();
        jest.useFakeTimers();
        jest.setSystemTime(new Date('2026-02-13'));
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    const mockUserConfig = {
        playable_days_of_week: ['Monday', 'Friday'],
        earliest_playable_time: '8:00am',
        extra_playable_days: ['3/15', '4/20'],
        include_holidays: true,
        minimum_minutes_before_sunset: 120,
        min_players: 2,
        notifications_enabled: true,
        start_date: '3/1',
        end_date: '11/30',
    };

    it('should show loading state initially', () => {
        fetch.mockImplementationOnce(() => new Promise(() => {}));
        render(<UpdateNotificationSettingsForm email="test@example.com" />);
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should fetch and display user config', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Update Notification Settings/)).toBeInTheDocument();
        });
    });

    it('should render all form sections', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Days of the Week/)).toBeInTheDocument();
            expect(screen.getByText(/Earliest Time/)).toBeInTheDocument();
            expect(screen.getByText(/Season Start Date/)).toBeInTheDocument();
            expect(screen.getByText(/Season End Date/)).toBeInTheDocument();
            expect(screen.getByText(/Include Holidays?/)).toBeInTheDocument();
            expect(screen.getByText(/Minimum Minutes Before Sunset/)).toBeInTheDocument();
            expect(screen.getByText(/Minimum Players/)).toBeInTheDocument();
        });
    });

    it('should render all day checkboxes', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].forEach(day => {
                expect(screen.getByLabelText(day)).toBeInTheDocument();
            });
        });
    });

    it('should check correct days based on config', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByLabelText('Monday')).toBeChecked();
            expect(screen.getByLabelText('Friday')).toBeChecked();
            expect(screen.getByLabelText('Tuesday')).not.toBeChecked();
        });
    });

    it('should allow toggling day checkboxes', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            const tuesdayCheckbox = screen.getByLabelText('Tuesday');
            fireEvent.click(tuesdayCheckbox);
            expect(tuesdayCheckbox).toBeChecked();
        });
    });

    it('should handle form submission successfully', async () => {
        fetch
            .mockResolvedValueOnce({
                json: async () => ({ success: true, result: mockUserConfig }),
            })
            .mockResolvedValueOnce({ ok: true })
            .mockResolvedValueOnce({
                json: async () => ({ success: true, result: mockUserConfig }),
            });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            const saveButton = screen.getByText(/Save Settings/);
            fireEvent.click(saveButton);
        });

        await waitFor(() => {
            expect(screen.getByText(/Settings saved!/)).toBeInTheDocument();
        });
    });

    it('should handle form submission failure', async () => {
        fetch
            .mockResolvedValueOnce({
                json: async () => ({ success: true, result: mockUserConfig }),
            })
            .mockResolvedValueOnce({ ok: false });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            const saveButton = screen.getByText(/Save Settings/);
            fireEvent.click(saveButton);
        });

        await waitFor(() => {
            expect(screen.getByText(/Failed to save settings/)).toBeInTheDocument();
        });
    });

    it('should prevent submission when errors exist', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        // Mock ExtraPlayableDaysInput to set errors
        jest.mock('./ExtraPlayableDaysInput', () => {
            return function ExtraPlayableDaysInput({ onErrorsChange }) {
                onErrorsChange(true);
                return <div>Extra Playable Days Mock</div>;
            };
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            const saveButton = screen.getByText(/Save Settings/);
            fireEvent.click(saveButton);
        });

        await waitFor(() => {
            expect(screen.queryByText(/Settings saved!/)).not.toBeInTheDocument();
        });
    });

    it('should render Go Home buttons', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: true, result: mockUserConfig }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            const homeButtons = screen.getAllByText(/Go Home/);
            expect(homeButtons.length).toBe(2); // One at top, one at bottom
        });
    });

    it('should show pause/resume toggle for enabled notifications', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                success: true,
                result: { ...mockUserConfig, notifications_enabled: true },
            }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Keep Notifications On/)).toBeInTheDocument();
            expect(screen.getByText(/Pause Notifications/)).toBeInTheDocument();
        });
    });

    it('should show resume toggle for paused notifications', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                success: true,
                result: { ...mockUserConfig, notifications_enabled: false },
            }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Keep Notifications Paused/)).toBeInTheDocument();
            expect(screen.getByText(/Resume Notifications/)).toBeInTheDocument();
        });
    });

    it('should handle failed config fetch', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ success: false }),
        });

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch current settings/)).toBeInTheDocument();
        });
    });

    it('should handle network errors on fetch', async () => {
        fetch.mockRejectedValueOnce(new Error('Network error'));

        render(<UpdateNotificationSettingsForm email="test@example.com" />);

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch current settings/)).toBeInTheDocument();
        });
    });
});
