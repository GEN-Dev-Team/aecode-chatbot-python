from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse  
from dotenv import load_dotenv
import os
from openai import OpenAI
import re
load_dotenv()


# Cargar claves
CHAT_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_DEV_2")

client = OpenAI(api_key=CHAT_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

async def create_thread():
    thread = client.beta.threads.create()

    return thread.id

async def stream_assistant_response(user_message, thread_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    try:
        stream = client.beta.threads.runs.stream(
            assistant_id=ASSISTANT_ID,
            thread_id=thread_id,
        )

        yield "event: start\ndata: Iniciando respuesta...\n\n"  # ✅ ENVÍA PRIMERA LÍNEA

        with stream as run_stream:
            for text in run_stream.text_deltas:
                texto = re.sub(r'【.*?】', '', text)
                texto = texto.replace("\n", "<br>")
                yield f"data: {texto}\n\n"

        yield "event: end\ndata: [[END]]\n\n"

    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"

    finally:
            yield "event: end\ndata: [[END]]\n\n"  

@app.get("/message")
async def add_message(message, thread_id):
    return StreamingResponse(stream_assistant_response(message, thread_id), media_type="text/event-stream")

# create endpoint to generate a thread
@app.get("/thread")
async def create_thread_endpoint():
    thread_id = await create_thread()
    return {"thread_id": thread_id}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # Render establece PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)
