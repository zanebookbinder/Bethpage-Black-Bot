import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import {
    Alert,
    Loader,
    Link,
    Heading,
    View,
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
            <View className="form">
                <Alert borderRadius={10} variation="error" marginBottom="1rem">{errorMessage}</Alert>
                <Button variation="primary" onClick={() => (window.location.href = "/")}>← Go Home</Button>
            </View>
        );
    }

    if (paused) {
        return (
            <View className="form">
                <Button variation="primary" padding=".5rem" marginBottom="1rem" onClick={() => (window.location.href = "/")}>← Go Home</Button>
                <Heading level={3}>Notifications paused</Heading>
                <Text marginBottom="1rem">
                    You won't receive any more Bethpage Black Bot emails until you turn
                    notifications back on.
                </Text>
                <Heading level={5} marginBottom="0.5rem">Want to resume?</Heading>
                <Text>
                    1. Go to <Link href="/" color="var(--orange-button-color)">bethpage-black-bot.com</Link>
                    <br />
                    2. Click <strong>Get a one-time link</strong> and enter your email
                    <br />
                    3. Open the link in your inbox
                    <br />
                    4. Turn <strong>Notifications</strong> back on and save
                </Text>
            </View>
        );
    }

    return <UpdateNotificationSettingsForm email={email} />;
}
