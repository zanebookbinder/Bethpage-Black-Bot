import { render, screen } from '@testing-library/react';
import { CurrentTeeTime } from './CurrentTeeTime';

describe('CurrentTeeTime', () => {
  it('renders with provided props', () => {
    render(
      <CurrentTeeTime
        date="Saturday May 27th"
        time="10:30am"
        players="4"
      />
    );

    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Players')).toBeInTheDocument();
    expect(screen.getByText('May 27th')).toBeInTheDocument();
    expect(screen.getByText('Saturday @ 10:30am')).toBeInTheDocument();
  });

  it('correctly splits date string with day of week', () => {
    render(
      <CurrentTeeTime
        date="Monday June 12th"
        time="2:15pm"
        players="2"
      />
    );

    expect(screen.getByText('June 12th')).toBeInTheDocument();
    expect(screen.getByText('Monday @ 2:15pm')).toBeInTheDocument();
  });

  it('handles different player counts', () => {
    const { rerender } = render(
      <CurrentTeeTime
        date="Tuesday July 4th"
        time="8:00am"
        players="1"
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument();

    rerender(
      <CurrentTeeTime
        date="Tuesday July 4th"
        time="8:00am"
        players="3"
      />
    );

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('displays time correctly', () => {
    render(
      <CurrentTeeTime
        date="Friday August 18th"
        time="4:45pm"
        players="4"
      />
    );

    expect(screen.getByText('Friday @ 4:45pm')).toBeInTheDocument();
  });
});
