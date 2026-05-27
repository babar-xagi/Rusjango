from rusjango import Rusjango

app = Rusjango(settings="settings.py")


@app.get("/")
async def home():
    return {"message": "Hello Rusjango Babar"}


@app.get("/students/{id}")
async def get_student(id: int):
    return {"id": id, "name": "Ali"}


app.load_installed_apps()
