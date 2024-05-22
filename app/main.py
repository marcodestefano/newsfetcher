import uvloop
import asyncio
from fastapi import FastAPI
from newspaper import Article
import os
from dotenv import load_dotenv

load_dotenv()
REMOVAL_INTERVAL = int(os.getenv('REMOVAL_INTERVAL', 12 * 60 * 60))
app = FastAPI()
cached_web_articles = {}
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

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
