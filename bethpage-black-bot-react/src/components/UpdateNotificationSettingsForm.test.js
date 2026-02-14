import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UpdateNotificationSettingsForm from './UpdateNotificationSettingsForm';

jest.mock('../utils', () => ({
  API_BASE_URL: 'http://test-api.com',
  convertTo12Hour: jest.fn((time) => {
    // Simple mock implementation
    const [hours, minutes] = time.split(':');
    const h = parseInt(hours, 10);
    if (h === 0) return `12:${minutes}am`;
    if (h < 12) return `${h}:${minutes}am`;
    if (h === 12) return `12:${minutes}pm`;
    return `${h - 12}:${minutes}pm`;
  }),
  convertTo24Hour: jest.fn((time) => {
    // Simple mock - just return as-is for testing
    if (!time) return '';
    if (time.includes('am') || time.includes('pm')) {
      const isPM = time.includes('pm');
      const [h, m] = time.replace('am', '').replace('pm', '').split(':');
      let hours = parseInt(h, 10);
      if (isPM && hours !== 12) hours += 12;
      if (!isPM && hours === 12) hours = 0;
      return `${hours.toString().padStart(2, '0')}:${m}`;
    }
    return time;
  }),
  isValidDate: jest.fn((date) => {
    if (!date || date.trim() === '') return false;
    const parsed = new Date(date);
    return !isNaN(parsed.getTime());
  }),
  formatDateToMD: jest.fn((date) => {
    // Convert YYYY-MM-DD to M/D
    if (!date) return '';
    const [year, month, day] = date.split('-');
    return `${parseInt(month, 10)}/${parseInt(day, 10)}`;
  }),
  formatMDToDate: jest.fn((md) => {
    // Convert M/D to YYYY-MM-DD
    if (!md) return '';
    const [month, day] = md.split('/');
    const year = new Date().getFullYear();
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  })
}));

jest.mock('./ExtraPlayableDaysInput', () => {
  return function MockExtraPlayableDaysInput() {
    return <div data-testid="extra-playable-days-input">Extra Playable Days</div>;
  };
});

jest.mock('./ToggleButtonPair', () => {
  return function MockToggleButtonPair({ leftButtonText, rightButtonText, onToggle }) {
    return (
      <div data-testid="toggle-button-pair">
        <button onClick={() => onToggle(true)}>{leftButtonText}</button>
        <button onClick={() => onToggle(false)}>{rightButtonText}</button>
      </div>
    );
  };
});

describe('UpdateNotificationSettingsForm', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    delete window.location;
    window.location = { href: '' };
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const mockUserConfig = {
    success: true,
    result: {
      playable_days_of_week: ['Saturday', 'Sunday'],
      earliest_playable_time: '8:00am',
      extra_playable_days: [],
      include_holidays: false,
      minimum_minutes_before_sunset: 120,
      min_players: 2,
      notifications_enabled: true,
      start_date: '3/1',
      end_date: '11/30'
    }
  };

  it('shows loading state initially', () => {
    global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('fetches and displays user config', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => mockUserConfig
    });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByText('Update Notification Settings')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-api.com/getUserConfig',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com' })
      })
    );
  });

  it('renders all form fields after loading', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => mockUserConfig
    });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByText('Days of the Week')).toBeInTheDocument();
    });

    expect(screen.getByText('Earliest Time')).toBeInTheDocument();
    expect(screen.getByText('Season Start Date')).toBeInTheDocument();
    expect(screen.getByText('Season End Date')).toBeInTheDocument();
    expect(screen.getByText('Include Holidays?')).toBeInTheDocument();
    expect(screen.getByText('Minimum Minutes Before Sunset')).toBeInTheDocument();
    expect(screen.getByText('Minimum Players')).toBeInTheDocument();
  });

  it('allows user to select days of the week', async () => {
    
    global.fetch.mockResolvedValueOnce({
      json: async () => mockUserConfig
    });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByLabelText('Monday')).toBeInTheDocument();
    });

    const mondayCheckbox = screen.getByLabelText('Monday');
    expect(mondayCheckbox).not.toBeChecked();

    userEvent.click(mondayCheckbox);
    expect(mondayCheckbox).toBeChecked();
  });

  it('pre-checks days that are in user config', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => mockUserConfig
    });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByLabelText('Saturday')).toBeChecked();
      expect(screen.getByLabelText('Sunday')).toBeChecked();
      expect(screen.getByLabelText('Monday')).not.toBeChecked();
    });
  });

  it('submits updated settings', async () => {
    
    global.fetch
      .mockResolvedValueOnce({
        json: async () => mockUserConfig
      })
      .mockResolvedValueOnce({
        ok: true
      })
      .mockResolvedValueOnce({
        json: async () => mockUserConfig
      });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByText('Save Settings')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Save Settings');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Settings saved!')).toBeInTheDocument();
    });
  });

  it('shows error message when config fetch fails', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch current settings')).toBeInTheDocument();
    });
  });

  it('shows error message when settings save fails', async () => {
    
    global.fetch
      .mockResolvedValueOnce({
        json: async () => mockUserConfig
      })
      .mockResolvedValueOnce({
        ok: false
      });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      expect(screen.getByText('Save Settings')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Save Settings');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to save settings')).toBeInTheDocument();
    });
  });

  it('renders go home button', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => mockUserConfig
    });

    render(<UpdateNotificationSettingsForm email="test@example.com" />);

    await waitFor(() => {
      const homeButtons = screen.getAllByText('← Go Home');
      expect(homeButtons.length).toBeGreaterThan(0);
    });
  });
});
