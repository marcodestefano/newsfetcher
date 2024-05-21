import uvloop
import asyncio
from fastapi import FastAPI
from newspaper import Article
import logging

INTERVAL = 12 * 60 * 60
app = FastAPI()
cached_articles = {}
logging.basicConfig(level=logging.INFO)

async def remove_article(article_url):
    del cached_articles[article_url]
    logging.info(f"Article removed from cache: {article_url}")

async def schedule_removal(article_url):
    await asyncio.sleep(INTERVAL)
    await remove_article(article_url)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

@app.get("/")
async def default():
    return {"message": "Use /article?url= endpoint"}

@app.get("/article")
async def fetch_article(url:str = None):
    result = {}
    try:
        if url in cached_articles:
            result = cached_articles[url]
            logging.info(f"Article retrieved from cache: {url}")
        else:
            article = Article(url)
            article.download()
            article.parse()
            result = {"article_title": article.title, "article_text": article.text}
            cached_articles[url] = result
            asyncio.create_task(schedule_removal(url))
    except Exception:
        logging.error("Error fetching or parsing article:", exc_info=True)
    finally:
        return result
