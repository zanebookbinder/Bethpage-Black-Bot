import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

describe('App', () => {
    it('should render the header with BethpageBlackBot title', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        const titleElement = screen.getByText(/BethpageBlack/);
        expect(titleElement).toBeInTheDocument();
    });

    it('should render About this site link', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        const aboutLink = screen.getByText(/About this site/);
        expect(aboutLink).toBeInTheDocument();
    });

    it('should render homepage by default', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        // Homepage contains tabs, so check for one of the tab labels
        expect(screen.getByText(/Current Tee Times/)).toBeInTheDocument();
    });

    it('should have correct link to homepage', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        const homeLink = screen.getByText(/BethpageBlack/).closest('a');
        expect(homeLink).toHaveAttribute('href', '/');
    });

    it('should have correct link to about page', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        const aboutLink = screen.getByText(/About this site/).closest('a');
        expect(aboutLink).toHaveAttribute('href', '/about');
    });

    it('should apply correct styles to header', () => {
        render(
            <BrowserRouter>
                <App />
            </BrowserRouter>
        );
        const headerButtons = document.querySelector('.header-buttons');
        expect(headerButtons).toBeInTheDocument();
    });
});
