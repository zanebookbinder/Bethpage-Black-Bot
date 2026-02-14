import { useEffect, useState } from "react";
import { CurrentTeeTime } from "./CurrentTeeTime";
import { View, Heading, Text, Link, Flex, Button } from "@aws-amplify/ui-react";
import { API_BASE_URL } from "../utils";

export default function CurrentTeeTimes() {
    const useDummyData = false;
    const [recentTeeTimes, setRecentTeeTimes] = useState([]);

    useEffect(() => {
        if (useDummyData) {
            setRecentTeeTimes(
                {
                    Date: "Thursday June 5th",
                    Holes: "18",
                    Players: "4",
                    Time: "4:50pm",
                },
                {
                    Date: "Thursday June 5th",
                    Holes: "18",
                    Players: "4",
                    Time: "5:20pm",
                }
            );
        } else {
            fetchCurrentTeeTimes();
        }

        // eslint-disable-next-line
    }, []);

    const fetchCurrentTeeTimes = async () => {
        const res = await fetch(`${API_BASE_URL}/getRecentTimes`);
        const data = await res.json();
        setRecentTeeTimes(data["result"]);
    };

    return (
        <View>
            {recentTeeTimes && recentTeeTimes.length > 0 ? (
                <View>
                    <View>
                        <Heading color="var(--dark-green-text-color)" level={3}>
                            There{" "}
                            {recentTeeTimes.length === 1
                                ? "is 1 tee time"
                                : "are " +
                                  recentTeeTimes.length +
                                  " tee times"}{" "}
                            available! 😄
                        </Heading>
                        <Flex gap={4} direction={"column"}>
                            <Text color="var(--dark-green-text-color)">
                                Get{" "}
                                {recentTeeTimes.length === 1 ? "it" : "them"}{" "}
                                before it's too late!
                            </Text>
                            <Button
                                variation="primary"
                                className="primary-button"
                            >
                                <Link
                                    color="var(--white-button-text-color)"
                                    href="https://foreupsoftware.com/index.php/booking/19765/2432#/teetimes"
                                >
                                    Book your tee time here
                                </Link>
                            </Button>
                        </Flex>
                    </View>

                    <div
                        style={{
                            marginTop: '1.5rem',
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '1rem',
                        }}
                    >
                        {recentTeeTimes.map((teeTime, index) => (
                            <CurrentTeeTime
                                key={index}
                                date={teeTime.Date}
                                time={teeTime.Time}
                                players={teeTime.Players}
                            />
                        ))}
                    </div>
                </View>
            ) : (
                <View>
                    <Heading level={3}>
                        There are no tee times available 😔
                    </Heading>
                    <Text color="var(--dark-green-text-color)">
                        Check back later or sign up for alerts!
                    </Text>
                </View>
            )}
        </View>
    );
}
