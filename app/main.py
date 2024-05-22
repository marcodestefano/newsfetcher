import uvloop
import asyncio
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from newspaper import Article
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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

async def generate_summary_with_ai(article_text, model, ai, aikey):
    prompt = f"Summarize the article in a maximum of 5 paragraphs, beginning each with a relevant emoji. Ensure the summary is in the same language as the article: {article_text}"
    prompt = prompt.replace('\n', ' ').replace('\r', '')
    summary = None
    if ai == OPENAI_AI:
        openai_client = OpenAI(api_key=aikey)
        response = openai_client.chat.completions.create(
            model=model or OPENAI_DEFAULT_MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        summary = response.choices[0].message.content
    elif ai == GEMINI_AI:
        geminiai.configure(api_key=aikey)
        model=model or GEMINI_DEFAULT_MODEL
        geminimodel = geminiai.GenerativeModel(model_name=model)
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
        response = geminimodel.generate_content(prompt, safety_settings = safety_settings)
        summary = response.text
    else:
        print(f"Unsupported AI provider: {ai}")
    return summary

@app.get("/", response_class=JSONResponse)
async def default():
    return {"status": "OK"}
