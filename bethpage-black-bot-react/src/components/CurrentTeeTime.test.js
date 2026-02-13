import { render, screen } from '@testing-library/react';
import { CurrentTeeTime } from './CurrentTeeTime';

describe('CurrentTeeTime', () => {
    it('should render tee time information', () => {
        render(
            <CurrentTeeTime
                date="Thursday June 5th"
                time="4:50pm"
                players="4"
            />
        );
        expect(screen.getByText('4')).toBeInTheDocument();
        expect(screen.getByText('June 5th')).toBeInTheDocument();
        expect(screen.getByText(/Thursday/)).toBeInTheDocument();
        expect(screen.getByText(/4:50pm/)).toBeInTheDocument();
    });

    it('should display player count correctly', () => {
        render(
            <CurrentTeeTime
                date="Monday April 1st"
                time="8:00am"
                players="2"
            />
        );
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Players')).toBeInTheDocument();
    });

    it('should split date correctly', () => {
        render(
            <CurrentTeeTime
                date="Friday July 20th"
                time="3:30pm"
                players="3"
            />
        );
        // Day of week should be separate from date
        expect(screen.getByText('July 20th')).toBeInTheDocument();
        expect(screen.getByText(/Friday/)).toBeInTheDocument();
    });

    it('should display time with day of week', () => {
        render(
            <CurrentTeeTime
                date="Saturday August 15th"
                time="10:00am"
                players="4"
            />
        );
        expect(screen.getByText(/Saturday @ 10:00am/)).toBeInTheDocument();
    });
});
