import { render, screen, fireEvent } from '@testing-library/react';
import { useRef } from 'react';
import ToggleButtonPair from './ToggleButtonPair';

describe('ToggleButtonPair', () => {
    it('should render both buttons with correct text', () => {
        render(
            <ToggleButtonPair
                start={true}
                onToggle={() => {}}
                leftButtonText="Option A"
                rightButtonText="Option B"
            />
        );
        expect(screen.getByText('Option A')).toBeInTheDocument();
        expect(screen.getByText('Option B')).toBeInTheDocument();
    });

    it('should select left button initially when start is true', () => {
        render(
            <ToggleButtonPair
                start={true}
                onToggle={() => {}}
                leftButtonText="Left"
                rightButtonText="Right"
            />
        );
        const leftButton = screen.getByText('Left');
        expect(leftButton).toHaveAttribute('data-variation', 'primary');
    });

    it('should select right button initially when start is false', () => {
        render(
            <ToggleButtonPair
                start={false}
                onToggle={() => {}}
                leftButtonText="Left"
                rightButtonText="Right"
            />
        );
        const rightButton = screen.getByText('Right');
        expect(rightButton).toHaveAttribute('data-variation', 'primary');
    });

    it('should call onToggle when buttons are clicked', () => {
        const mockToggle = jest.fn();
        render(
            <ToggleButtonPair
                start={true}
                onToggle={mockToggle}
                leftButtonText="Left"
                rightButtonText="Right"
            />
        );

        fireEvent.click(screen.getByText('Right'));
        expect(mockToggle).toHaveBeenCalledWith(false);

        fireEvent.click(screen.getByText('Left'));
        expect(mockToggle).toHaveBeenCalledWith(true);
    });

    it('should toggle button styles when clicked', () => {
        render(
            <ToggleButtonPair
                start={true}
                onToggle={() => {}}
                leftButtonText="Left"
                rightButtonText="Right"
            />
        );

        const leftButton = screen.getByText('Left');
        const rightButton = screen.getByText('Right');

        expect(leftButton).toHaveAttribute('data-variation', 'primary');
        expect(rightButton).toHaveAttribute('data-variation', 'outline');

        fireEvent.click(rightButton);

        expect(leftButton).toHaveAttribute('data-variation', 'outline');
        expect(rightButton).toHaveAttribute('data-variation', 'primary');
    });

    it('should expose reset method via ref', () => {
        const TestComponent = () => {
            const ref = useRef();
            return (
                <div>
                    <ToggleButtonPair
                        ref={ref}
                        start={false}
                        onToggle={() => {}}
                        leftButtonText="Left"
                        rightButtonText="Right"
                    />
                    <button onClick={() => ref.current?.reset()}>Reset</button>
                </div>
            );
        };

        render(<TestComponent />);

        // Initially right is selected (start=false)
        expect(screen.getByText('Right')).toHaveAttribute('data-variation', 'primary');

        // Click reset button
        fireEvent.click(screen.getByText('Reset'));

        // After reset, left should be selected
        expect(screen.getByText('Left')).toHaveAttribute('data-variation', 'primary');
    });

    it('should expose getValue method via ref', () => {
        const TestComponent = () => {
            const ref = useRef();
            const [value, setValue] = useState(null);
            return (
                <div>
                    <ToggleButtonPair
                        ref={ref}
                        start={true}
                        onToggle={() => {}}
                        leftButtonText="Left"
                        rightButtonText="Right"
                    />
                    <button onClick={() => setValue(ref.current?.getValue())}>
                        Get Value
                    </button>
                    {value !== null && <div>Value: {String(value)}</div>}
                </div>
            );
        };

        const { useState } = require('react');
        render(<TestComponent />);

        fireEvent.click(screen.getByText('Get Value'));
        expect(screen.getByText(/Value: true/)).toBeInTheDocument();
    });
});
