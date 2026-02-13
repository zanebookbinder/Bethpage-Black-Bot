import { render, screen, waitFor } from '@testing-library/react';
import CurrentTeeTimes from './CurrentTeeTimes';
import { API_BASE_URL } from '../utils';

// Mock fetch
global.fetch = jest.fn();

describe('CurrentTeeTimes', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    it('should display message when no tee times are available', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ result: [] }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(screen.getByText(/There are no tee times available/)).toBeInTheDocument();
        });
    });

    it('should display tee times when available', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                result: [
                    {
                        Date: 'Thursday June 5th',
                        Time: '4:50pm',
                        Players: '4',
                        Holes: '18',
                    },
                ],
            }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(screen.getByText(/There is 1 tee time available/)).toBeInTheDocument();
        });
    });

    it('should display multiple tee times', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                result: [
                    {
                        Date: 'Thursday June 5th',
                        Time: '4:50pm',
                        Players: '4',
                        Holes: '18',
                    },
                    {
                        Date: 'Friday June 6th',
                        Time: '5:00pm',
                        Players: '3',
                        Holes: '18',
                    },
                ],
            }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(screen.getByText(/There are 2 tee times available/)).toBeInTheDocument();
        });
    });

    it('should call API with correct URL', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ result: [] }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/getRecentTimes`);
        });
    });

    it('should render book tee time button when times are available', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                result: [
                    {
                        Date: 'Thursday June 5th',
                        Time: '4:50pm',
                        Players: '4',
                        Holes: '18',
                    },
                ],
            }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(screen.getByText(/Book your tee time here/)).toBeInTheDocument();
        });
    });

    it('should display correct singular/plural text', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                result: [
                    {
                        Date: 'Thursday June 5th',
                        Time: '4:50pm',
                        Players: '4',
                        Holes: '18',
                    },
                ],
            }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            expect(screen.getByText(/Get it before it's too late!/)).toBeInTheDocument();
        });
    });

    it('should use correct link for booking', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({
                result: [
                    {
                        Date: 'Thursday June 5th',
                        Time: '4:50pm',
                        Players: '4',
                        Holes: '18',
                    },
                ],
            }),
        });

        render(<CurrentTeeTimes />);

        await waitFor(() => {
            const link = screen.getByText(/Book your tee time here/).closest('a');
            expect(link).toHaveAttribute('href', 'https://foreupsoftware.com/index.php/booking/19765/2432#/teetimes');
        });
    });
});
