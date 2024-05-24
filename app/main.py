import asyncio
import google.generativeai as geminiai
import json
import uvloop
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from gnews import GNews
from newspaper import Article
from openai import OpenAI
from starlette.middleware.cors import CORSMiddleware

load_dotenv()

MIN_ARTICLES = 1
OPENAI_AI = 'openai'
GEMINI_AI = 'gemini'
OPENAI_DEFAULT_MODEL = 'gpt-3.5-turbo-0125'
GEMINI_DEFAULT_MODEL = 'gemini-1.5-flash-latest'
AI = os.getenv('AI')
AI_MODEL = os.getenv('AI_MODEL')
AI_KEY = os.getenv('AI_KEY')
PROMPT = os.getenv('PROMPT', "Identify the language of the following article and summarize it in the same language, in maximum of 3 paragraphs, beginning each with a relevant emoji. Answer only with the summary. The article is the following:")
PORT = int(os.getenv('PORT', 8000))
TIMEOUT = int(os.getenv('TIMEOUT', 60 * 60 * 12))
ARTICLES = int(os.getenv('ARTICLES', 5))
MAX_ARTICLES = int(os.getenv('MAX_ARTICLES', 15))
LANGUAGE = os.getenv('LANGUAGE','it') 

cached_google_news = None
cache_expiration = datetime.now()
cached_web_articles = {}
cached_ai_articles = {}
CACHE_DURATION = timedelta(minutes=5)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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
    elif url in cached_web_articles and cached_web_articles[url]!="No content available":
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
    article_title = ""
    article_text = ""
    try:
        article = await fetch_article(url=article_url)
        article_title = article["article_title"]
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
    return {"title": article_title, "content": article_text}

async def generate_summary_with_ai(article_text, model, ai, aikey):
    prompt = f"{PROMPT} {article_text}"
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

@app.post("/news", response_class=JSONResponse)
async def fetch_news(
    request: Request
):
    try:
        data = await request.json()
        num_articles = data.get('num', ARTICLES)
    except:
        data = None
        num_articles = ARTICLES

    language = data.get('language', LANGUAGE) if data else LANGUAGE

    async def fetch_google_news():
        global cached_google_news, cache_expiration
        if cached_google_news is None or len(cached_google_news) < num_articles or datetime.now() > cache_expiration:
            print("Rebuilding GNews cache")
            google_news = GNews(language=language, max_results=num_articles)
            news = google_news.get_top_news()
            cached_google_news = [{"url": item["url"], "title": item["title"]} for item in news]
            cache_expiration = datetime.now() + CACHE_DURATION
        return cached_google_news[:num_articles]
        
    return JSONResponse(content=await fetch_google_news())

@app.post("/article", response_class=JSONResponse)
async def fetch_article_content_endpoint(
    request: Request
):
    try:
        data = await request.json()
        article_url = data.get('url')
        ai = data.get('ai', AI)
        model = data.get('model', AI_MODEL)
        aikey = data.get('aikey', AI_KEY)

        if not article_url:
            return JSONResponse({"error": "Article URL is required"}, status_code=400)

        article_content = await fetch_article_content(article_url, model, ai, aikey)
        return JSONResponse(article_content)
    except Exception as e:
        print("Error in fetch_article_content_endpoint:", e)
        return JSONResponse({"error": "An error occurred while fetching the article content"}, status_code=500)