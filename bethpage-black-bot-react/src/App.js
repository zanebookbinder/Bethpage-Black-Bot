import { Routes, Route } from "react-router-dom";
import Homepage from "./Homepage";
import OneTimeLinkValidator from "./components/OneTimeLinkValidator";
import TabWrapper from "./TabWrapper";
import { Link } from "react-router-dom";
import "./App.css";
import UpdateNotificationSettingsForm from "./components/UpdateNotificationSettingsForm";

export default function App() {
    return (
        <div>
            <Link
                to={"/"}
                style={{ textDecoration: "none", marginTop: "1rem" }}
            >
                <h2
                    style={{
                        fontFamily: "Montserrat, sans-serif",
                        fontWeight: "normal",
                        textAlign: "center",
                        color: "#fefae0",
                        display: "flex",
                        justifyContent: "flex-start",
                    }}
                >
                    <span style={{ fontWeight: "bold" }}>BethpageBlack</span>Bot
                </h2>
            </Link>
            <Routes>
                <Route path="/" element={<Homepage />} />
                <Route
                    path="/hello"
                    element={<UpdateNotificationSettingsForm />}
                />
                <Route
                    path="/updateSettings/:guid"
                    element={
                        <TabWrapper component={<OneTimeLinkValidator />} />
                    }
                />
            </Routes>
        </div>
    );
}
