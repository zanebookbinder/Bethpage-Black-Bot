import { Button, Flex } from "@aws-amplify/ui-react";
import { useState, forwardRef, useImperativeHandle, useEffect } from "react";

const ToggleButtonPair = forwardRef(
    ({ start, onToggle, leftButtonText, rightButtonText }, ref) => {
        const [isLeftSelected, setIsLeftSelected] = useState(true);

        useEffect(() => {
            if (start != null) {
                setIsLeftSelected(start);
            }
            // eslint-disable-next-line
        }, [start]);

        useImperativeHandle(ref, () => ({
            reset: () => setIsLeftSelected(true),
            getValue: () => isLeftSelected,
        }));

        const handleToggle = (value) => {
            setIsLeftSelected(value);
            onToggle?.(value);
        };

        return (
            <Flex gap="1rem" marginTop="0.5rem" width="auto">
                <Button
                    variation={isLeftSelected ? "primary" : "outline"}
                    onClick={() => handleToggle(true)}
                >
                    {leftButtonText}
                </Button>
                <Button
                    variation={!isLeftSelected ? "primary" : "outline"}
                    onClick={() => handleToggle(false)}
                >
                    {rightButtonText}
                </Button>
            </Flex>
        );
    }
);

export default ToggleButtonPair;
