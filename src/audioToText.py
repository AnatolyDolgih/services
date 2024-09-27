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
URL = "http://localhost:8080"
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

async def transcribe(audio):
    try:
        with tempfile.NamedTemporaryFile(prefix='req_',
                                         suffix='.wav', delete=False) as temp_audio_file:
            temp_audio_file.write(audio)
            temp_audio_file_path = temp_audio_file.name
            transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(temp_audio_file_path, 'rb')
            )
        temp_audio_file.close()
        
        return transcription
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


async def speech_to_text(audio):
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            temp_audio_file.write(audio)
            temp_audio_file_path = temp_audio_file.name
            transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(temp_audio_file_path, 'rb')
            )
        temp_audio_file.close()
        
        return transcription
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


async def get_audio(request):
    if request.status == 200:
        content_type = request.headers.get('Content-Type', '').lower()
        if 'text' in content_type:
            response_text = await request.text()
            if response_text == "0":
                return None
        audio_data = await request.read()
        return await transcribe(audio_data)
    else:
        print(f"Failed to get audio. Status code: {request.status}")
        return None
    
    

async def handle_speech_to_text(request):
    print(request)
    raw_req = request.content
    audio_data = await raw_req.read()
    #audio = await get_audio(request)
    text = await speech_to_text(audio_data)
    print(text)
    return web.json_response({"text" : text.text})


async def main():
    app = web.Application()
    app.add_routes([web.post('/transcribe', handle_speech_to_text)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print("speech to text service start")
    while True:
        await asyncio.sleep(500)


if __name__ == '__main__':
    asyncio.run(main())
