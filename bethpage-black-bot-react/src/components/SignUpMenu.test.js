import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SignUpMenu from './SignUpMenu';
import { API_BASE_URL } from '../utils';

global.fetch = jest.fn();

describe('SignUpMenu', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    it('should render signup form', () => {
        render(<SignUpMenu />);
        expect(screen.getByText(/Sign up for tee time alerts!/)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/tiger.woods@nike.com/)).toBeInTheDocument();
    });

    it('should render How It Works section', () => {
        render(<SignUpMenu />);
        expect(screen.getByText(/How It Works/)).toBeInTheDocument();
    });

    it('should handle successful registration', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<SignUpMenu />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        const submitButton = screen.getByText(/Sign Up/);

        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(/Successfully registered!/)).toBeInTheDocument();
        });
    });

    it('should handle registration failure', async () => {
        fetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ success: false, message: 'Email already exists' }),
        });

        render(<SignUpMenu />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        const submitButton = screen.getByText(/Sign Up/);

        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(/Failed to register user/)).toBeInTheDocument();
        });
    });

    it('should clear email field after successful registration', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<SignUpMenu />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Sign Up/));

        await waitFor(() => {
            expect(emailInput.value).toBe('');
        });
    });

    it('should call API with correct payload', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        render(<SignUpMenu />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Sign Up/));

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                `${API_BASE_URL}/register`,
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

        render(<SignUpMenu />);

        const emailInput = screen.getByPlaceholderText(/tiger.woods@nike.com/);
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.click(screen.getByText(/Sign Up/));

        await waitFor(() => {
            expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
        });
    });
});
