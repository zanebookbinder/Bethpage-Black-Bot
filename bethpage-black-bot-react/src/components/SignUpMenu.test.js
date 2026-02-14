import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SignUpMenu from './SignUpMenu';

jest.mock('../utils', () => ({
  API_BASE_URL: 'http://test-api.com'
}));

describe('SignUpMenu', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders the signup form', () => {
    render(<SignUpMenu />);

    expect(screen.getByText('Sign up for tee time alerts!')).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
  });

  it('allows user to type in email field', async () => {
    render(<SignUpMenu />);

    const emailInput = screen.getByLabelText('Email address');
    userEvent.type(emailInput, 'test@example.com');

    await waitFor(() => {
      expect(emailInput).toHaveValue('test@example.com');
    });
  });

  it('shows success message on successful registration', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<SignUpMenu />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Sign Up' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Successfully registered/)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-api.com/register',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' })
      })
    );
  });

  it('shows error message on failed registration', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ success: false, message: 'Email already exists' })
    });

    render(<SignUpMenu />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Sign Up' });

    userEvent.type(emailInput, 'duplicate@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to register user/)).toBeInTheDocument();
      expect(screen.getByText(/Email already exists/)).toBeInTheDocument();
    });
  });

  it('shows error message on network failure', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<SignUpMenu />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Sign Up' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    });
  });

  it('clears email field after successful registration', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<SignUpMenu />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Sign Up' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(emailInput).toHaveValue('');
    });
  });
});
