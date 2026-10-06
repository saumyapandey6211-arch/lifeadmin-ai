import os
import base64
import json
from io import BytesIO

from pypdf import PdfReader
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Task

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://lifeadmin-ai-17ei.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "LifeAdmin AI backend is running!"
    }

@app.get("/test-ai")
def test_ai():
    response = client.responses.create(
        model="gpt-6-luna",
        input="Say hello to LifeAdmin AI in one short sentence."
    )
    return {
        "message": response.output_text
    }

def save_tasks(task_list):
    db: Session = SessionLocal()

    try:
        for task in task_list:
            new_task = Task(
                title=task["title"],
                date=task["date"],
                time=task["time"],
                priority=task["priority"],
                reason=task["reason"]
            )
            db.add(new_task)

        db.commit()
    finally:
        db.close()

@app.post("/analyze-files")
async def analyze_files(files: list[UploadFile] = File(...)):
    if not files:
        return {
            "error": "Please upload at least one file."
        }

    if len(files) > 5:
        return {
            "error": "You can upload a maximum of 5 files at a time."
        }

    content = [
        {
            "type": "input_text",
            "text": """
You are LifeAdmin AI.

Analyze ALL uploaded files together.

The files may contain screenshots, images, PDFs, messages, schedules, assignments, notices, forms, or other everyday information.

Find everything that represents:

- a task
- a deadline
- an event
- a reminder
- an appointment
- an assignment
- an important date
- something the user needs to do

Combine information from all files.

If the same task appears in multiple files, include it only once.

Return ONLY valid JSON.

Use exactly this structure:

{
  "tasks": [
    {
      "title": "Task or event name",
      "date": "Date if visible, otherwise Not specified",
      "time": "Time if visible, otherwise Not specified",
      "priority": "High, Medium, or Low",
      "reason": "Short explanation of why this matters"
    }
  ]
}

Rules:

- Do not add markdown.
- Do not add ```json.
- Do not add explanations outside the JSON.
- Include every important task or event you can find.
- Do not create information that is not present in the files.
- If a date is not visible, use "Not specified".
- If a time is not visible, use "Not specified".
- Priority must be exactly High, Medium, or Low.
- Avoid duplicate tasks across files.
"""
        }
    ]

    filenames = []

    for file in files:
        filenames.append(file.filename or "unknown file")

        file_bytes = await file.read()
        content_type = file.content_type or ""

        if content_type.startswith("image/"):
            base64_image = base64.b64encode(
                file_bytes
            ).decode("utf-8")

            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{content_type};base64,{base64_image}",
                    "detail": "auto"
                }
            )

        elif content_type == "application/pdf" or (file.filename or "").lower().endswith(".pdf"):
            try:
                reader = PdfReader(BytesIO(file_bytes))
                extracted_text = ""

                for page in reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        extracted_text += page_text + "\n"

                if extracted_text.strip():
                    content.append(
                        {
                            "type": "input_text",
                            "text": f"""
PDF FILE: {file.filename}

{extracted_text}
"""
                        }
                    )
                else:
                    content.append(
                        {
                            "type": "input_text",
                            "text": f"""
PDF FILE: {file.filename}

This PDF did not contain extractable text.
"""
                        }
                    )

            except Exception:
                content.append(
                    {
                        "type": "input_text",
                        "text": f"""
PDF FILE: {file.filename}

This PDF could not be read.
"""
                    }
                )

        else:
            return {
                "error": f"Unsupported file type: {file.filename}"
            }

    try:
        response = client.responses.create(
            model="gpt-6-luna",
            input=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        ai_output = response.output_text
        tasks = json.loads(ai_output)

    except json.JSONDecodeError:
        return {
            "error": "AI returned invalid JSON.",
            "raw_analysis": ai_output
        }

    except Exception as error:
        return {
            "error": f"AI analysis failed: {str(error)}"
        }

    task_list = tasks.get("tasks", [])

    save_tasks(task_list)

    return {
        "filenames": filenames,
        "file_count": len(files),
        "tasks": task_list
    }

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    return await analyze_files([file])

@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    return await analyze_files([file])

@app.get("/tasks")
def get_tasks():
    db: Session = SessionLocal()

    try:
        tasks = db.query(Task).order_by(Task.id.desc()).all()

        return {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "date": task.date,
                    "time": task.time,
                    "priority": task.priority,
                    "reason": task.reason,
                    "status": task.status
                }
                for task in tasks
            ]
        }

    finally:
        db.close()

@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    db: Session = SessionLocal()

    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            return {
                "error": "Task not found"
            }

        task.status = "completed"
        db.commit()

        return {
            "message": "Task completed successfully",
            "task_id": task.id
        }

    finally:
        db.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db: Session = SessionLocal()

    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            return {
                "error": "Task not found"
            }

        db.delete(task)
        db.commit()

        return {
            "message": "Task deleted successfully",
            "task_id": task_id
        }

    finally:
        db.close()