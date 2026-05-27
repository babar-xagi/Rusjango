from rusjango import Router

from .models import Student
from .schemas import StudentCreate, StudentOut

router = Router()


@router.get("/students")
async def list_students():
    students = await Student.all()
    return [StudentOut.from_dict(s.to_dict()).dict() for s in students]


@router.post("/students")
async def create_student(data: StudentCreate):
    student = await Student.create(name=data.name, age=data.age)
    return StudentOut.from_dict(student.to_dict()).dict()
