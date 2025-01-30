# YouTube Video Summarizer

This project is a Flask-based web application that allows users to summarize YouTube videos. It extracts the transcript of a video, generates a summary using the MBart model, and saves the summary to a local SQLite database.

## Features
- Fetch video information (title, duration, thumbnail) from YouTube.
- Extract video transcripts.
- Generate summaries in multiple languages using the MBart model.
- Save and view summary history.

## Technologies
- Flask: Web framework for Python.
- yt-dlp: Library for downloading and extracting YouTube video information.
- youtube-transcript-api: Library for fetching YouTube video transcripts.
- Transformers: Library for natural language processing (MBart model).
- SQLite: Lightweight database for storing summary history.
