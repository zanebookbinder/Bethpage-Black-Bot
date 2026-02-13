import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Homepage from './Homepage';

// Mock child components
jest.mock('./components/CurrentTeeTimes', () => {
    return function CurrentTeeTimes() {
        return <div>CurrentTeeTimes Component</div>;
    };
});

jest.mock('./components/SignUpMenu', () => {
    return function SignUpMenu() {
        return <div>SignUpMenu Component</div>;
    };
});

jest.mock('./components/GetOneTimeLink', () => {
    return function GetOneTimeLink() {
        return <div>GetOneTimeLink Component</div>;
    };
});

describe('Homepage', () => {
    it('should render without crashing', () => {
        render(
            <BrowserRouter>
                <Homepage />
            </BrowserRouter>
        );
        expect(screen.getByText(/Current Tee Times/)).toBeInTheDocument();
    });

    it('should render all three tabs', () => {
        render(
            <BrowserRouter>
                <Homepage />
            </BrowserRouter>
        );
        expect(screen.getByText(/Current Tee Times/)).toBeInTheDocument();
        expect(screen.getByText(/Sign Up/)).toBeInTheDocument();
        expect(screen.getByText(/Update Your Notification Settings/)).toBeInTheDocument();
    });

    it('should have correct styling classes', () => {
        render(
            <BrowserRouter>
                <Homepage />
            </BrowserRouter>
        );
        const homepage = document.querySelector('.homepage');
        expect(homepage).toBeInTheDocument();
    });

    it('should render default tab (Current Tee Times)', () => {
        render(
            <BrowserRouter>
                <Homepage />
            </BrowserRouter>
        );
        // The default tab content should be visible
        expect(screen.getByText(/CurrentTeeTimes Component/)).toBeInTheDocument();
    });

    it('should apply correct max-width styling', () => {
        render(
            <BrowserRouter>
                <Homepage />
            </BrowserRouter>
        );
        const homepage = document.querySelector('.homepage');
        expect(homepage).toHaveStyle({ maxWidth: '900px' });
    });
});
