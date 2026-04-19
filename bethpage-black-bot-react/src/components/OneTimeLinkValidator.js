import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import {
    Alert,
    Loader,
    Link,
    Heading,
    Flex,
    Text,
    Button,
} from "@aws-amplify/ui-react";
import { API_BASE_URL } from "../utils";
import UpdateNotificationSettingsForm from "./UpdateNotificationSettingsForm";

export default function OneTimeLinkValidator() {
    const { guid } = useParams();

    const [email, setEmail] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [paused, setPaused] = useState(false);

    useEffect(() => {
        const validateAndAct = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/validateOneTimeLink`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ guid }),
                });
                const data = await res.json();

                if (!data.email) {
                    setErrorMessage(data.errorMessage || "Invalid or expired link.");
                    return;
                }

                const validatedEmail = data.email;

                if (data.pause) {
                    const configRes = await fetch(`${API_BASE_URL}/getUserConfig`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email: validatedEmail }),
                    });
                    const configData = await configRes.json();
                    const currentConfig = configData.result || {};

                    await fetch(`${API_BASE_URL}/updateUserConfig`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            ...currentConfig,
                            email: validatedEmail,
                            notifications_enabled: false,
                        }),
                    });
                    setPaused(true);
                } else {
                    setEmail(validatedEmail);
                }
            } catch {
                setErrorMessage("Error processing your request.");
            } finally {
                setLoading(false);
            }
        };

        validateAndAct();
        // eslint-disable-next-line
    }, [guid]);

    if (loading) {
        return <Loader variation="linear" padding="2rem" filledColor="#bc6c25" />;
    }

    if (errorMessage) {
        return (
            <Flex direction="column" padding="2rem" maxWidth="40rem" margin="auto" alignItems="center">
                <Alert borderRadius={10} variation="error">{errorMessage}</Alert>
                <Link href="/"><Heading level={5}>Click here to go home</Heading></Link>
            </Flex>
        );
    }

    if (paused) {
        return (
            <Flex direction="column" padding="2rem" maxWidth="40rem" margin="auto" gap="1rem">
                <Heading level={3} color="var(--dark-green-text-color)">
                    Notifications paused
                </Heading>
                <Text>
                    You won't receive any more Bethpage Black Bot emails until you turn
                    notifications back on.
                </Text>
                <Heading level={5} color="var(--dark-green-text-color)" marginTop="1rem">
                    Want to resume?
                </Heading>
                <Text>
                    1. Go to <Link href="/">bethpage-black-bot.com</Link>
                    <br />
                    2. Click <strong>Get a one-time link</strong> and enter your email
                    <br />
                    3. Open the link in your inbox
                    <br />
                    4. Turn <strong>Notifications</strong> back on and save
                </Text>
                <Button
                    variation="primary"
                    onClick={() => (window.location.href = "/")}
                >
                    Go to homepage
                </Button>
            </Flex>
        );
    }

    return <UpdateNotificationSettingsForm email={email} />;
}
