# Podcast RSS Feed Processor – Project Requirements Document (PRD)

## 1. Project Overview

The Podcast RSS Feed Processor is built to automate the process of ingesting, cleaning, and tagging podcast RSS feed data. It retrieves RSS feeds from remote URLs, parses the content for each episode, and then cleans the episode descriptions by removing promotional material and formatting issues using both regex and AI (OpenAI’s API). The system then categorizes each episode using a predefined static taxonomy for Format, Theme, and Track, and stores the processed data in a local SQLite database. A comprehensive command-line interface (CLI) serves as the user control panel for these operations.

This project is being built to solve the common challenge faced by podcasters and feed curators: manual curation is time-consuming and error-prone. The solution aims for reliability, high performance, and extensibility while ensuring that data integrity is maintained, especially when dealing with duplicate entries. Key success criteria include robust feed ingestion, effective two-stage content cleaning, consistent automated tagging, fast data retrieval from the database, and comprehensive logging for both real-time feedback and persistent error recording.

## 2. In-Scope vs. Out-of-Scope

**In-Scope:**

*   Securely ingesting podcast RSS feeds from remote HTTP URLs.
*   Parsing RSS feeds using the lxml library to extract essential fields (title, description, link, publication date, duration, audio URL, etc.).
*   Cleaning episode descriptions via a two-stage process: first using regex-based filtering and then using OpenAI’s API for context-sensitive cleanup.
*   Automatically tagging episodes based on a predefined static taxonomy covering Format, Theme, and Track.
*   Storing processed data in a local SQLite database with proper indexing and duplicate detection.
*   Providing a robust command-line interface with commands for ingestion, cleaning, tagging, exporting (JSON/CSV), and tag validation.
*   Detailed logging to both the console and log files and error reporting to trace processing steps.

**Out-of-Scope:**

*   Ingestion from local file sources or handling varying security constraints; the system supports only remote RSS feeds.
*   Scaling strategies for high-volume API usage given that the cost per use via OpenAI is minimal and the application is designed as a low-scale tool.
*   Complex data merging or overwriting of duplicate episodes; duplicates should be logged without modifying the production database.
*   Multi-user permission levels or role-based access, as the application is intended for personal use.
*   Interactive or advanced configuration options beyond switching between test and production modes.

## 3. User Flow

When the user launches the application from the command line, the system starts in a default test mode. In this mode, all operations use a test database to ensure no accidental modifications occur in the production environment. The user is greeted with real-time console messages and file logs detailing the startup mode and any preliminary system diagnostics.

After startup, the user invokes specific CLI commands to perform the full processing pipeline. First, the user uses the “ingest” command to fetch and parse the RSS feed from the provided URL. The application processes each episode’s metadata and detects duplicates (logging them rather than updating records). Next, the cleaning command is executed to process and update episode descriptions using regex filters followed by the OpenAI API. Finally, tagging is performed using the predefined taxonomy, and the user can export or validate data as needed. At every step, detailed logs are available to provide clear, step-by-step feedback on what the system is doing.

## 4. Core Features

*   **Feed Ingestion:**

    *   Securely fetch podcast RSS feeds via HTTP.
    *   Parse the RSS XML using lxml and extract essential fields such as title, description, link, publication date, duration, and audio URL.
    *   Log duplicate entries (based on unique episode titles) without overwriting existing data.

*   **Content Cleaning:**

    *   Two-stage cleaning: first applying regex-based filtering to remove known promotional content and formatting issues.
    *   Follow it with an AI-driven cleaning process via OpenAI’s API to contextually refine the episode descriptions.
    *   Store both original and cleaned descriptions, along with cleaning metadata (status and timestamp).

*   **Episode Tagging:**

    *   Automatically assign taxonomy-based tags to episodes, classifying them into Format, Theme, and Track.
    *   Extract episode numbers from titles where applicable.
    *   Enforce static tagging rules to ensure consistency across episodes.

*   **Database Storage:**

    *   Use a local SQLite database (default location: data/episodes.db) for storing processed episode data.
    *   Implement indexing on key fields (e.g., guid, published_date, cleaning_status, tags, and episode_number) for fast retrieval.
    *   Handle duplicate detection by logging events rather than updating records.

*   **Command-Line Interface Operations:**

    *   Provide CLI commands for ingesting, cleaning, tagging, exporting (to JSON/CSV), and validating tags.
    *   Offer clear real-time console feedback and detailed file logging.
    *   Default to test mode for safety, requiring an explicit production flag to update live data.

## 5. Tech Stack & Tools

*   **Frontend/CLI User Interface:**

    *   The CLI is built using Python’s built-in argparse library to create clear, command-driven interactions.
    *   Real-time suggestions and advanced IDE integration provided via Cursor for AI-powered coding support.

*   **Backend:**

    *   Language: Python 3.13+

    *   RSS Ingestion: requests (for HTTP operations)

    *   XML Parsing: lxml library to robustly process RSS feeds

    *   Data Storage: sqlite3 module for SQLite database operations

    *   AI Integration:

        *   OpenAI’s API using GPT-4O Mini for content cleaning.
        *   OpenAI’s GPT-3.5-turbo for tagging operations.

    *   Testing: pytest for a comprehensive test suite including unit, integration, and performance tests.

    *   Environment Configuration: python-dotenv to manage .env variables for secure configuration (e.g., RSS_FEED_URL, OPENAI_API_KEY).

## 6. Non-Functional Requirements

*   **Performance:**

    *   High processing speed for feeds containing hundreds of episodes.
    *   Efficient database queries enabled by the use of indexes.

*   **Security:**

    *   Ensure that production and test modes are kept separate to prevent accidental data modifications.
    *   Use environment configurations to safely handle private feed tokens included in the RSS feed URLs.

*   **Usability:**

    *   Provide clear, concise CLI feedback with extensive logging to both console and local files.
    *   Design the CLI commands for simplicity and clarity in operation.

*   **Reliability:**

    *   Robust error handling in feed parsing, cleaning, and tagging phases.
    *   Comprehensive logging for monitoring operations and debugging purposes.

*   **Compliance:**

    *   Use standard libraries and approaches to maintain compatibility within a local development environment.

## 7. Constraints & Assumptions

*   The system only ingests RSS feeds from remote URLs; local file ingestion is not supported.
*   Duplicate episode detection is based solely on unique episode titles; duplicates are logged and not overwritten.
*   OpenAI API usage is negligible in cost, and rate limits are not of primary concern given the low volume of requests.
*   The tagging taxonomy is static but stored as constants to allow easy updates in the future if necessary.
*   The application is designed for deployment on a local machine within a Python environment; there are no cloud or container deployment requirements at this time.
*   The CLI always defaults to test mode; the production database is only updated when explicitly flagged.
*   Extensive logging will be provided to both the console and local log files, ensuring transparency in both testing and production environments.

## 8. Known Issues & Potential Pitfalls

*   **Duplicate Detection:**

    *   There is a risk of false negatives if unique episode identification solely relies on titles. To mitigate this, ensure the uniqueness of additional fields (like GUID) is logged appropriately.

*   **OpenAI API Integration:**

    *   Even though API rate limits are not a major concern, potential connectivity issues or unexpected API responses should still be handled gracefully with error logging.

*   **Data Integrity in Test vs. Production:**

    *   Ensure there is a clear switch between test and production modes to prevent accidental modification of live data. A robust flag system in the CLI must enforce this separation.

*   **Error Handling in Parsing:**

    *   RSS feeds may sometimes have unexpected XML structures. Using lxml’s robust error handling and logging detailed errors can help mitigate these issues.

*   **Performance Bottlenecks:**

    *   Large RSS feeds might affect parsing and cleaning time. Ensure that logging and indexing are optimized to maintain high processing speeds.

## 9. Database Schema

The SQLite database with fields such as:

- **id:** INTEGER PRIMARY KEY AUTOINCREMENT  
- **guid:** TEXT UNIQUE – a unique identifier for each episode  
- **title:** TEXT – episode title  
- **description:** TEXT – original episode description  
- **cleaned_description:** TEXT – cleaned version of the description  
- **link:** TEXT – episode web link  
- **published_date:** TIMESTAMP – publication date (timezone-aware)  
- **duration:** TEXT – episode duration  
- **audio_url:** TEXT – URL to the audio file  
- **cleaning_timestamp:** TIMESTAMP – when cleaning was performed  
- **cleaning_status:** TEXT – status of the cleaning process (e.g., “pending”, “cleaned”)  
- **tags:** TEXT – JSON string storing taxonomy tags  
- **tagging_timestamp:** TIMESTAMP – when tagging was applied  
- **episode_number:** INTEGER – extracted episode number (if applicable)  
- **created_at / updated_at:** TIMESTAMP – record creation and update timestamps  

Indexes are defined on fields such as `guid`, `published_date`, `cleaning_status`, `tags`, and `episode_number` to ensure fast lookups.

## 10. Tagging Taxonomy

The system uses a strict taxonomy to standardize tagging. The taxonomy is divided into three main categories:

### Format Tags
- **Series Episodes**
- **Standalone Episodes**
- **RIHC Series**

### Theme Tags
- **Ancient & Classical Civilizations**
- **Medieval & Renaissance Europe**
- **Empire, Colonialism & Exploration**
- **Modern Political History & Leadership**
- **Military History & Battles**
- **Cultural, Social & Intellectual History**
- **Science, Technology & Economic History**
- **Religious, Ideological & Philosophical History**
- **Historical Mysteries, Conspiracies & Scandals**
- **Regional & National Histories**

### Track Tags
- **Roman Track**
- **Medieval & Renaissance Track**
- **Colonialism & Exploration Track**
- **American History Track**
- **Military & Battles Track**
- **Modern Political History Track**
- **Cultural & Social History Track**
- **Science, Technology & Economic History Track**
- **Religious & Ideological History Track**
- **Historical Mysteries & Conspiracies Track**
- **British History Track**
- **Global Empires Track**
- **World Wars Track**
- **Ancient Civilizations Track**
- **Regional Spotlight: Latin America Track**
- **Regional Spotlight: Asia & the Middle East Track**
- **Regional Spotlight: Europe Track**
- **Regional Spotlight: Africa Track**
- **Historical Figures Track**
- **The RIHC Bonus Track**
- **Archive Editions Track**
- **Contemporary Issues Through History Track**

*Note:* Specific rules (e.g., if an episode is tagged as "RIHC Series" it must also have "Series Episodes") ensure consistency across the dataset.

This PRD is intended to be the single point of reference for the Podcast RSS Feed Processor and will serve as the foundational guide for all subsequent technical documents. Every aspect—from core functionality to technical stack and potential pitfalls—has been detailed to eliminate ambiguity and ensure that future implementations can be carried out smoothly.
