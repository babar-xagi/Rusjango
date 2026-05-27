from rusjango.schema import Schema


class StudentCreate(Schema):
    name: str
    age: int


class StudentOut(Schema):
    id: int
    name: str
    age: int
