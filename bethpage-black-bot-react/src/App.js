import { Routes, Route } from "react-router-dom";
import Homepage from "./Homepage";
import OneTimeLinkValidator from "./components/OneTimeLinkValidator";
import TabWrapper from "./TabWrapper";
import { Link } from "react-router-dom";
import "./App.css";
// import UpdateNotificationSettingsForm from "./components/UpdateNotificationSettingsForm";
import AboutThisSite from "./components/AboutThisSite.js";

export default function App() {
    return (
        <div>
            <div className="header-buttons">
                <Link
                    to={"/"}
                    style={{ textDecoration: "none" }}
                >
                    <h2
                        style={{
                            fontFamily: "Montserrat, sans-serif",
                            color: "#fefae0",
                            fontWeight: "normal"
                        }}
                    >
                        <span style={{ fontWeight: "bold" }}>BethpageBlack</span>Bot
                    </h2>
                </Link>
                <Link
                    to={"/about"}
                    style={{ textDecoration: "none" }}
                >
                    <h3
                        className="about-page-link-text"
                        style={{
                            fontFamily: "Montserrat, sans-serif",
                            color: "#fefae0",
                            fontWeight: "normal"
                        }}
                    >
                        About this site
                    </h3>
                </Link>
            </div>
            <Routes>
                <Route path="/" element={<Homepage />} />
                {/* <Route
                    path="/hello"
                    element={<UpdateNotificationSettingsForm />}
                /> */}
                <Route
                    path="/updateSettings/:guid"
                    element={
                        <TabWrapper component={<OneTimeLinkValidator />} />
                    }
                />
                <Route
                    path="/about"
                    element={
                        <TabWrapper component={<AboutThisSite />} />
                    }
                />
            </Routes>
        </div>
    );
}
