from fastapi import FastAPI
#from gnews import GNews
from newspaper import Article

app = FastAPI()

""" @app.get("/")
async def fetch_articles():
    google_news = GNews(language='it')
    json_resp = google_news.get_top_news()
    article = google_news.get_full_article(json_resp[0]['url'])  # newspaper3k instance, you can access newspaper3k all attributes
    return {len(json_resp)}
"""
@app.get("/")
def default():
    return {"Use /article?url= endpoint"}

@app.get("/article")
def fetch_article(url:str = None):
    result = {}
    try:
        # google_news = GNews(language='it')
        # json_resp = google_news.get_top_news()
        article = Article(url)
        article.download()
        article.parse()
        result = {"article_title": article.title, "article_text": article.text}
    except Exception:
        print("Wrong URL: " + url)
    finally:
        return result