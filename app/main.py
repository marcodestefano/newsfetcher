import uvloop
import asyncio
import os
from fastapi import FastAPI
from newspaper import Article
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv('PORT', 8000))
TIMEOUT = int(os.getenv('TIMEOUT', 60 * 60 * 12))
ARTICLES = int(os.getenv('ARTICLES', 5))
MAX_ARTICLES = int(os.getenv('MAX_ARTICLES', 15))
LANGUAGE = os.getenv('LANGUAGE','it') 
MIN_ARTICLES = 1
OPENAI_AI = 'openai'
GEMINI_AI = 'gemini'
OPENAI_DEFAULT_MODEL = 'gpt-3.5-turbo-0125'
GEMINI_DEFAULT_MODEL = 'gemini-1.5-flash-latest'

cached_google_news = None
cache_expiration = datetime.now()
cached_web_articles = {}
cached_ai_articles = {}
CACHE_DURATION = timedelta(minutes=5)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = FastAPI()

async def remove_article(article_url):
    del cached_web_articles[article_url]
    print(f"Article removed from cache: {article_url}")

async def schedule_removal(article_url):
    await asyncio.sleep(REMOVAL_INTERVAL)
    await remove_article(article_url)

@app.get("/")
async def default():
    return {"status": "OK"}

@app.get("/article")
async def fetch_article(url:str = None):
    result = {}
    try:
        if url in cached_web_articles:
            result = cached_web_articles[url]
            print(f"Article retrieved from cache: {url}")
        else:
            article = Article(url)
            article.download()
            article.parse()
            result = {"article_title": article.title, "article_text": article.text}
            cached_web_articles[url] = result
            asyncio.create_task(schedule_removal(url))
    except Exception:
        print("Error fetching or parsing article:", exc_info=True)
    finally:
        return result
