import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GetOneTimeLink from './GetOneTimeLink';
import { API_BASE_URL } from '../utils';

global.fetch = jest.fn();

describe('GetOneTimeLink', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    it('should render form with title and description', () => {
        render(<GetOneTimeLink />);
        expect(screen.getByText(/Get a One-Time Link/)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/tiger.woods@nike.com/)).toBeInTheDocument();
    });

    it('should validate email before sending request', async () => {
        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        const submitButton = screen.getByText(/Send Link/);

        fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(/Please enter a valid email address/)).toBeInTheDocument();
        });

        expect(fetch).not.toHaveBeenCalled();
    });

    it('should handle successful link creation', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        await waitFor(() => {
            expect(screen.getByText(/Check your email for the link/)).toBeInTheDocument();
        });
    });

    it('should handle API failure', async () => {
        fetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ success: false, message: 'User not found' }),
        });

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        await waitFor(() => {
            expect(screen.getByText(/Failed to send link/)).toBeInTheDocument();
        });
    });

    it('should show loading state while submitting', async () => {
        fetch.mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 100)));

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        const button = screen.getByRole('button', { name: /Send Link/ });
        expect(button).toHaveAttribute('data-loading', 'true');
    });

    it('should clear email after successful submission', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        await waitFor(() => {
            expect(emailInput.value).toBe('');
        });
    });

    it('should call API with correct payload', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                `${API_BASE_URL}/createOneTimeLink`,
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'test@example.com' }),
                })
            );
        });
    });

    it('should handle network errors', async () => {
        fetch.mockRejectedValueOnce(new Error('Network error'));

        render(<GetOneTimeLink />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Send Link/));

        await waitFor(() => {
            expect(screen.getByText(/An error occurred/)).toBeInTheDocument();
        });
    });
});
