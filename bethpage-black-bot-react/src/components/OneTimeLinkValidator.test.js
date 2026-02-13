import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import OneTimeLinkValidator from './OneTimeLinkValidator';
import { API_BASE_URL } from '../utils';

global.fetch = jest.fn();

// Mock the UpdateNotificationSettingsForm component
jest.mock('./UpdateNotificationSettingsForm', () => {
    return function UpdateNotificationSettingsForm({ email }) {
        return <div>Update Settings Form for {email}</div>;
    };
});

describe('OneTimeLinkValidator', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    const renderWithRouter = (guid = 'test-guid-123') => {
        return render(
            <BrowserRouter>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );
    };

    it('should show loading state initially', () => {
        fetch.mockImplementationOnce(() => new Promise(() => {})); // Never resolves
        renderWithRouter();
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should validate guid and show update form on success', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ email: 'test@example.com' }),
        });

        render(
            <BrowserRouter initialEntries={['/updateSettings/valid-guid']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/Update Settings Form for test@example.com/)).toBeInTheDocument();
        });
    });

    it('should show error message for invalid guid', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ errorMessage: 'Invalid or expired link.' }),
        });

        render(
            <BrowserRouter initialEntries={['/updateSettings/invalid-guid']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/Invalid or expired link/)).toBeInTheDocument();
        });
    });

    it('should show home link on error', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ errorMessage: 'Invalid link' }),
        });

        render(
            <BrowserRouter initialEntries={['/updateSettings/invalid-guid']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            const homeLink = screen.getByText(/Click here to go home/).closest('a');
            expect(homeLink).toHaveAttribute('href', '/');
        });
    });

    it('should call API with correct guid', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({ email: 'test@example.com' }),
        });

        render(
            <BrowserRouter initialEntries={['/updateSettings/my-guid-123']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                `${API_BASE_URL}/validateOneTimeLink`,
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ guid: 'my-guid-123' }),
                })
            );
        });
    });

    it('should handle network errors', async () => {
        fetch.mockRejectedValueOnce(new Error('Network error'));

        render(
            <BrowserRouter initialEntries={['/updateSettings/test-guid']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/Error validating the link/)).toBeInTheDocument();
        });
    });

    it('should show default error message when none provided', async () => {
        fetch.mockResolvedValueOnce({
            json: async () => ({}),
        });

        render(
            <BrowserRouter initialEntries={['/updateSettings/test-guid']}>
                <Routes>
                    <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
                </Routes>
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/Invalid or expired link/)).toBeInTheDocument();
        });
    });
});
