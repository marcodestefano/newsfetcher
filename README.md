# News Fetcher API

This is a FastAPI backend for fetching and summarizing news articles using Google News and AI models like OpenAI's GPT and GeminiAI.

## Features

- Fetch top news articles using Google News.
- Summarize articles using OpenAI GPT-3 or GeminiAI.
- Caching of fetched articles and summaries to improve performance.
- Asynchronous operations to handle multiple requests efficiently.

## Requirements

- Defined in requirements.txt

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/marcodestefano/newsfetcher.git
    cd newsfetcher
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your configuration:

    ```plaintext
    PORT=8000
    TIMEOUT=43200  # 12 hours in seconds
    ARTICLES=5
    MAX_ARTICLES=15
    LANGUAGE=it
    OPENAI_API_KEY=your_openai_api_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

## Usage

Run the FastAPI server:

```bash
fastapi dev main.py
```

### Endpoints

#### Default Status Check

- **URL:** `/`
- **Method:** `GET`
- **Response:** JSON object with status "OK".

#### Fetch News URLs

- **URL:** `/news`
- **Method:** `POST`
- **Parameters:**
  - `num` (int): Number of articles to fetch. Default is 5.
  - `language` (str): Language of the news. Default is 'it'.
- **Response:** JSON array of articles with "url" and "title".

#### Fetch Article content

- **URL:** `/article`
- **Method:** `POST`
- **Parameters:**
  - `url` (str): URL of the article to fetch.
  - `ai` (str): AI service to use ('openai' or 'gemini'). Default is `None`. If ai is not defined, the article is not summarized.
  - `model` (str): Model to use with the AI service. Default models are used if not specified: gpt-3.5-turbo-0125 for openai and gemini-1.5-flash-latest for gemini
  - `aikey` (str): API key for the AI service. Default is `None`.
- **Response:** JSON object with "title" and "content".

### Example Request

Using Postman or any HTTP client, send a POST request to `/news`:

```json
{
  "num": 1,
  "language": "en"
}
```

And to `/article`:

```json
{
  "url": "https://example.com/article",
  "ai": "openai",
  "model": "gpt-3.5-turbo",
  "aikey": "your_openai_api_key"
}
```

### Deployment

The app is ready for deploy on Vercel.

### Contributing

Contributions are welcome, please create a pull request with a description of your changes.

### License

This project is licensed under the Apache 2.0 License.