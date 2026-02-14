import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Homepage from './Homepage';

jest.mock('./components/CurrentTeeTimes', () => {
  return function MockCurrentTeeTimes() {
    return <div data-testid="current-tee-times">Current Tee Times Component</div>;
  };
});

jest.mock('./components/SignUpMenu', () => {
  return function MockSignUpMenu() {
    return <div data-testid="sign-up-menu">Sign Up Menu Component</div>;
  };
});

jest.mock('./components/GetOneTimeLink', () => {
  return function MockGetOneTimeLink() {
    return <div data-testid="get-one-time-link">Get One Time Link Component</div>;
  };
});

describe('Homepage', () => {
  it('renders the homepage with tabs', () => {
    render(<Homepage />);

    expect(screen.getByText('Current Tee Times')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();
    expect(screen.getByText('Update Your Notification Settings')).toBeInTheDocument();
  });

  it('displays Current Tee Times tab content by default', () => {
    render(<Homepage />);

    expect(screen.getByTestId('current-tee-times')).toBeInTheDocument();
  });

  it('switches to Sign Up tab when clicked', async () => {
    
    render(<Homepage />);

    const signUpTab = screen.getByText('Sign Up');
    userEvent.click(signUpTab);

    expect(screen.getByTestId('sign-up-menu')).toBeInTheDocument();
  });

  it('switches to Update Your Notification Settings tab when clicked', async () => {
    
    render(<Homepage />);

    const updateSettingsTab = screen.getByText('Update Your Notification Settings');
    userEvent.click(updateSettingsTab);

    expect(screen.getByTestId('get-one-time-link')).toBeInTheDocument();
  });

  it('applies correct styling to homepage container', () => {
    const { container } = render(<Homepage />);

    const homepage = container.querySelector('.homepage');
    expect(homepage).toBeInTheDocument();
    expect(homepage).toHaveStyle({
      backgroundColor: '#fefae0',
      borderRadius: '1rem'
    });
  });
});
