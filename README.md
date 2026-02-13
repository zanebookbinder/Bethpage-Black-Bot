# Bethpage Black Bot & Daily Update Lambda

An automated web scraping and notification system built with Python, Docker, and AWS Lambda. This project consists of two main components:

## Components

### 1. Bethpage Black Tee Time Bot

Scrapes the Bethpage Black golf course website for open tee times, filters them based on your preferences, and sends email notifications for newly available times.

**Features:**

- Real-time Bethpage Black tee time availability monitoring
- Filters by preferred dates, times, and number of available spots
- Email alerts for newly available tee times
- Serverless deployment via AWS Lambda
- Scheduled execution every 3 minutes using EventBridge
- DynamoDB state management to avoid duplicate notifications

### 2. Daily Update Lambda

A comprehensive daily digest service that aggregates volunteer opportunities and entertainment options from multiple NYC sources and sends a combined email.

**Monitored Opportunities:**

- Late-night show ticket waitlists (from 1iota.com)
- NYC Cares volunteering opportunities
- Central Park public volunteering events
- Central Park private volunteering opportunities (MyImpactPage/Better Impact)
- Central Park community volunteer days

**Features:**

- Parallel scraping with concurrent execution for performance
- Filters for weekend-only and holiday volunteer opportunities
- Consolidated email digest with all opportunities in table format
- Automatic daily execution via AWS Lambda

## Architecture Overview

Both services follow a similar architecture:

- **Dockerized Python App**: Core logic packaged in Docker containers
- **AWS Lambda**: Serverless compute with parallel execution support
- **Amazon EventBridge**: Scheduled triggers for automated runs
- **Amazon DynamoDB**: Persistent state management
- **Email Notification (AWS SES)**: Sends alerts and digests
- **AWS Secrets Manager**: Secure credential storage

## Quick Start

For detailed setup instructions, deployment, and infrastructure configuration, see [SETUP.md](SETUP.md).

## License

MIT License

This project is not affiliated with Bethpage State Park or its operators.
