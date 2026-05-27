from rusjango.orm import Integer, Model, String


class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
