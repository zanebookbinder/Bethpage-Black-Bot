import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import {
    Alert,
    Loader,
    Link,
    Heading,
    Flex,
} from "@aws-amplify/ui-react";
import UpdateConfiguration from "./UpdateNotificationSettingsForm";
import { API_BASE_URL } from "../utils";

export default function OneTimeLinkValidator() {
    const { guid } = useParams();
    const [email, setEmail] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const validateGuid = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/validateOneTimeLink`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ guid: guid }),
                });
                const data = await res.json();

                if (data.email) {
                    setEmail(data.email);
                } else {
                    setErrorMessage(
                        data.errorMessage || "Invalid or expired link."
                    );
                }
            } catch (err) {
                setErrorMessage("Error validating the link.");
            } finally {
                setLoading(false);
            }
        };

        validateGuid();

        // eslint-disable-next-line
    }, [guid]);

    if (loading) {
        return (
            <Loader variation="linear" padding="2rem" filledColor={"#bc6c25"} />
        );
    }

    if (errorMessage) {
        return (
            <Flex
                direction="column"
                padding="2rem"
                maxWidth="40rem"
                margin="auto"
                alignItems="center"
            >
                <Alert borderRadius={10} variation="error">
                    {errorMessage}
                </Alert>
                <Link href="/">
                    <Heading level={5}>Click here to go home</Heading>
                </Link>
            </Flex>
        );
    }

    return <UpdateConfiguration email={email} />;
}
