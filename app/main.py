import asyncio
import uvloop
import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from gnews import GNews
from newspaper import Article
from dotenv import load_dotenv
from ai_utils import generate_summary_with_ai

load_dotenv()

PORT = int(os.getenv('PORT', 8000))
TIMEOUT = int(os.getenv('TIMEOUT', 60 * 60 * 12))
ARTICLES = int(os.getenv('ARTICLES', 5))
MAX_ARTICLES = int(os.getenv('MAX_ARTICLES', 15))
MIN_ARTICLES = 1
LANGUAGE = os.getenv('LANGUAGE','it') 

cached_google_news = None
cache_expiration = datetime.now()
cached_web_articles = {}
cached_ai_articles = {}
CACHE_DURATION = timedelta(minutes=5)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = FastAPI()

async def remove_article(articles, article_url):
    del articles[article_url]
    print(f"Article removed from cache: {article_url}")

async def schedule_removal(articles, article_url):
    await asyncio.sleep(TIMEOUT)
    await remove_article(articles, article_url)

async def fetch_article(url: str = None):
    result = ""
    if not url:
        print("Error fetching article: URL parameter missing")
    elif url in cached_web_articles:
        print(f"Article retrieved from cache: {url}")
        result = cached_web_articles[url]
    else :
        try:
            article = Article(url)
            article.download()
            article.parse()
            result = {"article_title": article.title, "article_text": article.text}
            cached_web_articles[url] = result
            asyncio.create_task(schedule_removal(cached_web_articles, url))
        except Exception:
            print("Error fetching or parsing article: ", exc_info=True)
    return result

async def fetch_article_content(article_url, model, ai, aikey):
    article_text = ""
    try:
        article = await fetch_article(url=article_url)
        article_text = article["article_text"]
        if article_url in cached_ai_articles:
            print(f"Article retrieved from AI cache: {article_url}")
            article_text = cached_ai_articles[article_url]
        elif ai and aikey:
            summary = await generate_summary_with_ai(article_text, model, ai, aikey)
            if summary:
                article_text = summary
                cached_ai_articles[article_url] = article_text
                asyncio.create_task(schedule_removal(cached_ai_articles, article_url))
    except Exception as e:
        print("Error generating summary with AI:", e)
    return article_text

@app.get("/", response_class=JSONResponse)
async def default():
    return {"status": "OK"}

@app.post("/news", response_class=StreamingResponse)
async def fetch_news(
    request: Request
):
    data = await request.json()
    num = data.get('num', ARTICLES)
    language = data.get('language', LANGUAGE)
    ai = data.get('ai', None)
    model = data.get('model', None)
    aikey = data.get('aikey', None)

    if num < MIN_ARTICLES or num > MAX_ARTICLES:
        return {"Error": f"Invalid number of articles. The number of articles has to be between {MIN_ARTICLES} and {MAX_ARTICLES}"}
    
    async def article_generator():
        global cached_google_news, cache_expiration
        if cached_google_news is None or datetime.now() > cache_expiration:
            print("Rebuilding GNews cache")
            google_news = GNews(language=language)
            cached_google_news = google_news.get_top_news()
            cache_expiration = datetime.now() + CACHE_DURATION
        json_resp = cached_google_news
        first_article = True
        yield '['  # Inizio dell'array JSON
        for i in range(num):
            if not first_article:
                yield ','  # Aggiungi una virgola prima di ogni articolo tranne il primo
            article_url = json_resp[i]['url']
            article_content = await fetch_article_content(article_url, model, ai, aikey)
            article = {
                "title": json_resp[i]['title'],
                "content": article_content
            }
            yield json.dumps(article)
            first_article = False
        yield ']'  # Fine dell'array JSON
    
    return StreamingResponse(article_generator(), media_type="application/json")
