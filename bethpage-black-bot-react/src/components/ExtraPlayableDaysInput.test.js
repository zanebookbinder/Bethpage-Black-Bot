import { render, screen, fireEvent } from '@testing-library/react';
import ExtraPlayableDaysInput from './ExtraPlayableDaysInput';

describe('ExtraPlayableDaysInput', () => {
    beforeEach(() => {
        jest.useFakeTimers();
        jest.setSystemTime(new Date('2026-02-13'));
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('should render with initial empty date field', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: [''] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        expect(screen.getByText(/Extra Playable Days/)).toBeInTheDocument();
        const dateInputs = screen.getAllByDisplayValue('');
        expect(dateInputs.length).toBeGreaterThan(0);
    });

    it('should render existing dates', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15', '2026-04-20'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        expect(screen.getByDisplayValue('2026-03-15')).toBeInTheDocument();
        expect(screen.getByDisplayValue('2026-04-20')).toBeInTheDocument();
    });

    it('should allow adding new date fields', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        const addButton = screen.getByText(/Add New Date/);
        fireEvent.click(addButton);

        expect(mockSetFormData).toHaveBeenCalledWith(
            expect.any(Function)
        );
    });

    it('should disable add button when last date is empty', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15', ''] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        const addButton = screen.getByText(/Add New Date/);
        expect(addButton).toBeDisabled();
    });

    it('should allow removing date fields', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15', '2026-04-20'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        const removeButtons = screen.getAllByText(/Remove/);
        fireEvent.click(removeButtons[0]);

        expect(mockSetFormData).toHaveBeenCalledWith(expect.any(Function));
    });

    it('should update form data when date is changed', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        const dateInput = screen.getByDisplayValue('2026-03-15');
        fireEvent.change(dateInput, { target: { value: '2026-04-01' } });

        expect(mockSetFormData).toHaveBeenCalled();
    });

    it('should validate dates and report errors', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['2026-03-15'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        const dateInput = screen.getByDisplayValue('2026-03-15');
        // Set a past date
        fireEvent.change(dateInput, { target: { value: '2026-02-01' } });

        expect(mockOnErrorsChange).toHaveBeenCalled();
    });

    it('should handle M/D/YYYY format conversion', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: ['3/15/2026'] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        expect(screen.getByDisplayValue('2026-03-15')).toBeInTheDocument();
    });

    it('should render descriptive text', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{ extra_playable_days: [''] }}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        expect(screen.getByText(/past dates will be automatically removed when you save/)).toBeInTheDocument();
    });

    it('should handle empty formData gracefully', () => {
        const mockSetFormData = jest.fn();
        const mockOnErrorsChange = jest.fn();

        render(
            <ExtraPlayableDaysInput
                formData={{}}
                setFormData={mockSetFormData}
                onErrorsChange={mockOnErrorsChange}
            />
        );

        expect(screen.getByText(/Extra Playable Days/)).toBeInTheDocument();
    });
});
