import { Heading, View, Text } from "@aws-amplify/ui-react";
import { Link } from "react-router-dom";

export default function AboutThisSite() {
    return (
        <View className="about-this-site">
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginRight: "2rem",
                    marginBottom: "1rem",
                }}
            >
                <Heading level={3}>About this site</Heading>
                <Link height={"fit-content"} to='https://github.com/zanebookbinder/Bethpage-Black-Bot'>Source Github repo</Link>
            </div>
            <Text>
                Hi, I'm Zane 👋  and I created Bethpage Black Bot!
                Check out my {' '}
                <Link to='https://www.linkedin.com/in/zane-bookbinder/'>LinkedIn</Link>,
                {' '}
                <Link to='https://github.com/zanebookbinder'>Github</Link>,
                {' and '}
                <Link to='https://www.zanebookbinder.com/'>personal website</Link> {' '}
                if you want to connect.
                <br />
                <br />
                Since you're on this site, odds are you're an NYC or Long-Island
                based golfer struggling to snag a tee time on the Black course.
                A few months ago, I was too.
                <br />
                <br />I got my 7-day resident access and refreshed the tee sheet
                at 7pm every weekend, but kept missing out. I figured that even
                if I couldn't get a slot when the batch dropped, there still
                must be people cancelling their times minutes, hours, or days
                after claiming them.
                <br />
                <br />
                I obviously couldn't spend every second checking the website,
                which is where the Bot comes in. I built a web scraping tool
                using Selenium that navigates to the tee times page and scans
                the available times, filtering them according to my criteria.
                After hooking the code up to AWS Lambda, using AWS EventBridge
                to schedule the function every 5 minutes, and adding AWS SES
                functionality to send myself emails if the bot found anything
                new, I had a working service. I also added a DynamoDB database
                that records the bot's results from every run so that I can do
                some analysis on when during the day/week/month/year tee times
                are most available.
                <br />
                <br />
                Long story short, one Tuesday in June I got an email that two
                spots were available at 12:30pm on the following Saturday! I
                snatched it up thanks to the bot and was able to play the course
                with a friend just before the Ryder Cup, which made it extra
                cool (I played terribly, but what can you do 🤷‍♂️).
                People rarely drop their times once secured, but when they do,
                I'm now there to grab them.
                <br />
                <br />
                This frontend site is a quick addition that gives a face to the
                otherwise-backend project. It lets users sign up, adjust their
                filter preferences (ex. which days of the week they are free to
                play golf), and view the bot's most recent tee time finds. I 
                hope it helps you get to play the Black Course like it did for me!
                <br />
                <br />
                If you have any questions, comments, or suggestions, you can
                contact me at{" "}
                <span style={{ fontWeight: "bold" }}>
                    zane.bookbinder [at] gmail.com
                </span>
                . Thanks for reading and I hope you enjoy the site!
            </Text>
        </View>
    );
}
