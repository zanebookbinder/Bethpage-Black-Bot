import { View, Tabs } from "@aws-amplify/ui-react";
import CurrentTeeTimes from "./components/CurrentTeeTimes";
import SignUpMenu from "./components/SignUpMenu";
import TabWrapper from "./TabWrapper";
import GetOneTimeLink from "./components/GetOneTimeLink";
import "./App.css";

export default function Homepage() {
    return (
        <div
            className="homepage"
            style={{
                maxWidth: 900,
                minHeight: "75vh",
                margin: "auto",
                padding: 20,
                backgroundColor: "#fefae0",
                boxShadow: "0px 4px 12px rgba(0,0,0,0.1)",
                borderRadius: "1rem",
                color: "var(--dark-green-text-color)",
            }}
        >
            <View display="flex" justifyContent="center">
                <View>
                    <Tabs
                        defaultValue={"tee-times"}
                        items={[
                            {
                                label: (
                                    <span
                                        style={{
                                            fontSize: "1.25rem",
                                            fontWeight: "bold",
                                            color: "var(--dark-green-text-color)",
                                        }}
                                    >
                                        Current Tee Times
                                    </span>
                                ),
                                value: "tee-times",
                                content: (
                                    <TabWrapper
                                        component={<CurrentTeeTimes />}
                                    />
                                ),
                            },
                            {
                                label: (
                                    <span
                                        style={{
                                            fontSize: "1.25rem",
                                            fontWeight: "bold",
                                            color: "var(--dark-green-text-color)",
                                        }}
                                    >
                                        Sign Up
                                    </span>
                                ),
                                value: "sign-up",
                                content: (
                                    <TabWrapper component={<SignUpMenu />} />
                                ),
                            },
                            {
                                label: (
                                    <span
                                        style={{
                                            fontSize: "1.25rem",
                                            fontWeight: "bold",
                                            color: "var(--dark-green-text-color)",
                                        }}
                                    >
                                        Update Your Notification Settings
                                    </span>
                                ),
                                value: "update-notification-settings",
                                content: (
                                    <TabWrapper
                                        component={<GetOneTimeLink />}
                                    />
                                ),
                            },
                        ]}
                    />
                </View>
            </View>
        </div>
    );
}
