import os
import base64
import json

from pypdf import PdfReader

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Task


# -----------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------------------

load_dotenv()


# -----------------------------------------
# CONNECT TO OPENAI
# -----------------------------------------

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# -----------------------------------------
# CREATE FASTAPI APP
# -----------------------------------------

app = FastAPI()


# -----------------------------------------
# CREATE DATABASE TABLES
# -----------------------------------------

Base.metadata.create_all(bind=engine)


# -----------------------------------------
# CORS
# -----------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------
# HOME ROUTE
# -----------------------------------------

@app.get("/")
def home():

    return {
        "message": "LifeAdmin AI backend is running!"
    }


# -----------------------------------------
# TEST AI
# -----------------------------------------

@app.get("/test-ai")
def test_ai():

    response = client.responses.create(
        model="gpt-6-luna",
        input="Say hello to LifeAdmin AI in one short sentence."
    )

    return {
        "message": response.output_text
    }


# -----------------------------------------
# ANALYZE IMAGE
# -----------------------------------------

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):

    # -------------------------------------
    # READ IMAGE
    # -------------------------------------

    image_bytes = await file.read()

    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    content_type = file.content_type or "image/png"


    # -------------------------------------
    # SEND IMAGE TO AI
    # -------------------------------------

    response = client.responses.create(

        model="gpt-6-luna",

        input=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "input_text",

                        "text": """
You are LifeAdmin AI.

Analyze this screenshot carefully.

Find everything that represents:

- a task
- a deadline
- an event
- a reminder
- an appointment
- an assignment
- an important date
- something the user needs to do

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
- If a date is not visible, use "Not specified".
- If a time is not visible, use "Not specified".
- Priority must be exactly High, Medium, or Low.
""",
                    },

                    {
                        "type": "input_image",

                        "image_url":
                            f"data:{content_type};base64,{base64_image}",

                        "detail": "auto",
                    },
                ],
            }
        ],
    )


    # -------------------------------------
    # GET AI RESULT
    # -------------------------------------

    ai_output = response.output_text


    # -------------------------------------
    # CONVERT AI RESULT TO JSON
    # -------------------------------------

    try:

        tasks = json.loads(ai_output)

    except json.JSONDecodeError:

        return {
            "filename": file.filename,
            "error": "AI returned invalid JSON",
            "raw_analysis": ai_output
        }


    # -------------------------------------
    # SAVE TASKS TO DATABASE
    # -------------------------------------

    db: Session = SessionLocal()

    try:

        for task in tasks["tasks"]:

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


    # -------------------------------------
    # RETURN RESULT
    # -------------------------------------

    return {

        "filename": file.filename,

        "tasks": tasks["tasks"]
    }


# -----------------------------------------
# ANALYZE PDF
# -----------------------------------------

@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):

    # -------------------------------------
    # READ PDF
    # -------------------------------------

    pdf_bytes = await file.read()

    temp_pdf = "temp_upload.pdf"

    with open(temp_pdf, "wb") as pdf_file:
        pdf_file.write(pdf_bytes)


    # -------------------------------------
    # EXTRACT TEXT FROM PDF
    # -------------------------------------

    try:

        reader = PdfReader(temp_pdf)

        extracted_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

    except Exception as error:

        return {
            "filename": file.filename,
            "error": f"Could not read PDF: {str(error)}"
        }


    # -------------------------------------
    # CHECK IF TEXT WAS FOUND
    # -------------------------------------

    if not extracted_text.strip():

        return {
            "filename": file.filename,
            "error": "Could not extract text from this PDF."
        }


    # -------------------------------------
    # SEND PDF TEXT TO AI
    # -------------------------------------

    response = client.responses.create(

        model="gpt-6-luna",

        input=f"""
You are LifeAdmin AI.

Analyze the following text extracted from a PDF.

Find everything that represents:

- a task
- a deadline
- an event
- a reminder
- an appointment
- an assignment
- an important date
- something the user needs to do

Return ONLY valid JSON.

Use exactly this structure:

{{
  "tasks": [
    {{
      "title": "Task or event name",
      "date": "Date if visible, otherwise Not specified",
      "time": "Time if visible, otherwise Not specified",
      "priority": "High, Medium, or Low",
      "reason": "Short explanation of why this matters"
    }}
  ]
}}

Rules:

- Do not add markdown.
- Do not add ```json.
- Do not add explanations outside the JSON.
- Include every important task or event you can find.
- If a date is not visible, use "Not specified".
- If a time is not visible, use "Not specified".
- Priority must be exactly High, Medium, or Low.

PDF TEXT:

{extracted_text}
"""
    )


    # -------------------------------------
    # GET AI RESULT
    # -------------------------------------

    ai_output = response.output_text


    # -------------------------------------
    # CONVERT AI RESULT TO JSON
    # -------------------------------------

    try:

        tasks = json.loads(ai_output)

    except json.JSONDecodeError:

        return {
            "filename": file.filename,
            "error": "AI returned invalid JSON",
            "raw_analysis": ai_output
        }


    # -------------------------------------
    # SAVE PDF TASKS TO DATABASE
    # -------------------------------------

    db: Session = SessionLocal()

    try:

        for task in tasks["tasks"]:

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


    # -------------------------------------
    # RETURN PDF RESULT
    # -------------------------------------

    return {

        "filename": file.filename,

        "tasks": tasks["tasks"]
    }


# -----------------------------------------
# GET ALL SAVED TASKS
# -----------------------------------------

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


# -----------------------------------------
# COMPLETE A TASK
# -----------------------------------------

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


# -----------------------------------------
# DELETE A TASK
# -----------------------------------------

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