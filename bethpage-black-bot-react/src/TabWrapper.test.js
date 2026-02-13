import { render, screen } from '@testing-library/react';
import TabWrapper from './TabWrapper';

describe('TabWrapper', () => {
    it('should render the component passed as prop', () => {
        const TestComponent = () => <div>Test Component</div>;
        render(<TabWrapper component={<TestComponent />} />);
        expect(screen.getByText('Test Component')).toBeInTheDocument();
    });

    it('should have the tab-wrapper class', () => {
        const TestComponent = () => <div>Test Component</div>;
        render(<TabWrapper component={<TestComponent />} />);
        const wrapper = document.querySelector('.tab-wrapper');
        expect(wrapper).toBeInTheDocument();
    });

    it('should render null component gracefully', () => {
        render(<TabWrapper component={null} />);
        const wrapper = document.querySelector('.tab-wrapper');
        expect(wrapper).toBeInTheDocument();
    });
});
