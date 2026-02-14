import { render, screen, waitFor } from '@testing-library/react';
import CurrentTeeTimes from './CurrentTeeTimes';

// Mock the API_BASE_URL
jest.mock('../utils', () => ({
  API_BASE_URL: 'http://test-api.com'
}));

describe('CurrentTeeTimes', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('displays tee times when available', async () => {
    const mockTeeTimes = [
      {
        Date: 'Saturday May 27th',
        Time: '10:30am',
        Players: '4',
        Holes: '18'
      },
      {
        Date: 'Saturday May 27th',
        Time: '11:00am',
        Players: '3',
        Holes: '18'
      }
    ];

    global.fetch.mockResolvedValueOnce({
      json: async () => ({ result: mockTeeTimes })
    });

    render(<CurrentTeeTimes />);

    await waitFor(() => {
      expect(screen.getByText('There are 2 tee times available! 😄')).toBeInTheDocument();
    });

    expect(screen.getByText('Get them before it\'s too late!')).toBeInTheDocument();
    expect(screen.getByText('Book your tee time here')).toBeInTheDocument();
    expect(screen.getAllByText('May 27th').length).toBeGreaterThan(0);
    expect(screen.getByText('Saturday @ 10:30am')).toBeInTheDocument();
  });

  it('displays singular message for one tee time', async () => {
    const mockTeeTimes = [
      {
        Date: 'Monday June 5th',
        Time: '2:15pm',
        Players: '2',
        Holes: '18'
      }
    ];

    global.fetch.mockResolvedValueOnce({
      json: async () => ({ result: mockTeeTimes })
    });

    render(<CurrentTeeTimes />);

    await waitFor(() => {
      expect(screen.getByText('There is 1 tee time available! 😄')).toBeInTheDocument();
    });

    expect(screen.getByText('Get it before it\'s too late!')).toBeInTheDocument();
  });

  it('displays no tee times message when array is empty', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => ({ result: [] })
    });

    render(<CurrentTeeTimes />);

    await waitFor(() => {
      expect(screen.getByText('There are no tee times available 😔')).toBeInTheDocument();
    });

    expect(screen.getByText('Check back later or sign up for alerts!')).toBeInTheDocument();
    expect(screen.queryByText('Book your tee time here')).not.toBeInTheDocument();
  });

  it('displays tee times in a grid layout', async () => {
    const mockTeeTimes = [
      {
        Date: 'Saturday May 27th',
        Time: '10:30am',
        Players: '4',
        Holes: '18'
      },
      {
        Date: 'Saturday May 27th',
        Time: '11:00am',
        Players: '3',
        Holes: '18'
      }
    ];

    global.fetch.mockResolvedValueOnce({
      json: async () => ({ result: mockTeeTimes })
    });

    const { container } = render(<CurrentTeeTimes />);

    await waitFor(() => {
      const gridDiv = container.querySelector('div[style*="grid"]');
      expect(gridDiv).toBeInTheDocument();
      expect(gridDiv).toHaveStyle({
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)'
      });
    });
  });

  it('calls the correct API endpoint', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => ({ result: [] })
    });

    render(<CurrentTeeTimes />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://test-api.com/getRecentTimes');
    });
  });
});
