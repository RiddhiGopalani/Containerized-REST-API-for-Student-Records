"""Student Records REST API built with FastAPI."""

import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app import database
from app.schemas import Student, StudentIn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: make sure the table exists.
    database.init_db()
    yield


app = FastAPI(
    title="Student Records API",
    description="A simple REST API to add, view and update student records (Activity 9).",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the Student Records API",
        "docs": "/docs",
        "endpoints": ["/health", "/students", "/students/{student_id}"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/students", response_model=list[Student])
def list_students():
    return database.fetch_all_students()


@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    student = database.fetch_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return student


@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
def add_student(student: StudentIn):
    try:
        return database.insert_student(student.model_dump())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Roll number {student.roll_no} already exists")


@app.put("/students/{student_id}", response_model=Student)
def edit_student(student_id: int, student: StudentIn):
    try:
        updated = database.update_student(student_id, student.model_dump())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Roll number {student.roll_no} already exists")
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return updated
