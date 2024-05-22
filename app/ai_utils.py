import google.generativeai as geminiai
from openai import OpenAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold

OPENAI_AI = 'openai'
GEMINI_AI = 'gemini'
OPENAI_DEFAULT_MODEL = 'gpt-3.5-turbo-0125'
GEMINI_DEFAULT_MODEL = 'gemini-1.5-flash-latest'

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
