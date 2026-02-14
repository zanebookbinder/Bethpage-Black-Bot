import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GetOneTimeLink from './GetOneTimeLink';

jest.mock('../utils', () => ({
  API_BASE_URL: 'http://test-api.com'
}));

describe('GetOneTimeLink', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders the form', () => {
    render(<GetOneTimeLink />);

    expect(screen.getByText('Get a One-Time Link')).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Link' })).toBeInTheDocument();
  });

  it('allows user to type in email field', async () => {
    
    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    userEvent.type(emailInput, 'test@example.com');

    expect(emailInput).toHaveValue('test@example.com');
  });

  it('validates email format before submitting', async () => {
    
    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Send Link' });

    userEvent.type(emailInput, 'invalid-email');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address.')).toBeInTheDocument();
    });

    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('shows success message on successful link creation', async () => {
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Send Link' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Check your email for the link/)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://test-api.com/createOneTimeLink',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' })
      })
    );
  });

  it('shows error message on failed link creation', async () => {
    
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ success: false, message: 'Email not found' })
    });

    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Send Link' });

    userEvent.type(emailInput, 'notfound@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to send link/)).toBeInTheDocument();
      expect(screen.getByText(/Email not found/)).toBeInTheDocument();
    });
  });

  it('shows error message on network failure', async () => {
    
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Send Link' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/An error occurred/)).toBeInTheDocument();
    });
  });

  it('clears email field after successful submission', async () => {
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    render(<GetOneTimeLink />);

    const emailInput = screen.getByLabelText('Email address');
    const submitButton = screen.getByRole('button', { name: 'Send Link' });

    userEvent.type(emailInput, 'test@example.com');
    userEvent.click(submitButton);

    await waitFor(() => {
      expect(emailInput).toHaveValue('');
    });
  });

  it('accepts various valid email formats', async () => {
    
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    });

    const validEmails = [
      'test@example.com',
      'user.name@example.co.uk',
      'user+tag@example.org',
      'test123@test-domain.com'
    ];

    for (const email of validEmails) {
      const { unmount } = render(<GetOneTimeLink />);
      const emailInput = screen.getByLabelText('Email address');
      const submitButton = screen.getByRole('button', { name: 'Send Link' });

      userEvent.type(emailInput, email);
      userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Check your email for the link/)).toBeInTheDocument();
      });

      unmount();
    }
  });
});
