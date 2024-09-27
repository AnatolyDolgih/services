import asyncio
import tempfile
from aiohttp import web
from aiologger.loggers.json import JsonLogger 
from openai import OpenAI

logger = JsonLogger.with_default_handlers(
            level='DEBUG',
            serializer_kwargs={'ensure_ascii': False},
        )

with open("./api_key.txt") as f:
    m_api = f.readline()

client = OpenAI(api_key=m_api)
MODEL = "gpt-4o-mini"
URL = "http://localhost:8081"
INTRODUCTION = '''
Your name is Kevin, 
your standing at (15.52,0.25,14.42).You  You are in a room sized Xmin = 10.7, Xmax = 19.7, Ymin = 0.25, Ymax = 6.5, Zmin = 3.15, Zmax = 15.7.
you are a helpful tutor that assists the student with any subject. Act as natural as possible (if the student isn't paying attention show certain emotions like anger, surprise and so on, if the student is paying attention
show certain emotions like anger, surprise and so on, if the student is paying attention and interested show positive emotions).
Based on the inputs: if the student is looking at the board, at the teacher, their position, their photo (emotion), and their question (can be empty), provide a response indicating:
- Where to look (return 1 if you want to look at the user's eyes, 2 if at the user's mouth, 3 if you want to look to the right, 4 if you want to look to the left)
- Which emotion to display (anger, disgust, fear, happiness, sadness, surprise) and its intensity (0 to 100)
- Answer the question if not empty. No answer if the question is empty. Only answer the last question, and only once. 
The answer should be concise. Your response should include: look_direction, emotion, intensity and answer(can be just ""). The response should be in JSON format.
'''


async def text_to_speech(input_text: str, model: str = "tts-1", voice: str = "onyx"):
    try:
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=input_text
        ) as response:
            with tempfile.NamedTemporaryFile(prefix='ans_', 
                                             suffix='.wav',
                                             dir='./audio/', 
                                             delete=False) as temp_file:
                response.stream_to_file(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"An error occurred while synthesising speech: {e}")
        return None


async def handle_text_to_speech(request):
    raw_text = await request.json()
    text = raw_text['text']
    print(text)
    audio = await text_to_speech(text)
    print(audio)
    return web.FileResponse(audio)


async def main():
    app = web.Application()
    app.add_routes([web.post('/speech', handle_text_to_speech)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8081)
    await site.start()
    print("text to speech service start")
    while True:
        await asyncio.sleep(500)


if __name__ == '__main__':
    asyncio.run(main())
