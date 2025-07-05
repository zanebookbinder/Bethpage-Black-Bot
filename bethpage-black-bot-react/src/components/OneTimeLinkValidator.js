import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { View, Alert, Loader } from "@aws-amplify/ui-react";
import UpdateConfiguration from "./UpdateConfiguration";

export default function OneTimeLinkValidator() {
  const { guid } = useParams();
  const [email, setEmail] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const apiBase = process.env.REACT_APP_API_URL;

  useEffect(() => {
    const validateGuid = async () => {
      try {
        const res = await fetch(`${apiBase}/validateOneTimeLink?guid=${guid}`);
        const data = await res.json();

        if (data.email) {
          setEmail(data.email);
        } else {
          setErrorMessage(data.errorMessage || "Invalid or expired link.");
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
      <View padding="2rem">
        <Loader variation="linear" />
      </View>
    );
  }

  if (errorMessage) {
    return (
      <View padding="2rem" maxWidth="40rem" margin="auto">
        <Alert variation="error">{errorMessage}</Alert>
      </View>
    );
  }

  return <UpdateConfiguration email={email} />;
}
