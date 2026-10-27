"""Pydantic models used to validate request and response data."""

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class StudentIn(BaseModel):
    """Data the client sends when adding or updating a student."""

    name: str = Field(..., min_length=2, max_length=100, examples=["Priya Deshmukh"])
    roll_no: str = Field(..., min_length=1, max_length=20, examples=["CS104"])
    department: str = Field(..., min_length=2, max_length=100, examples=["Computer Engineering"])
    email: str = Field(..., pattern=EMAIL_PATTERN, max_length=100, examples=["priya.deshmukh@example.com"])


class Student(StudentIn):
    """A student record as stored in the database."""

    id: int
