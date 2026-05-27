from rusjango import Rusjango

app = Rusjango(settings="settings.py")


@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}


app.load_installed_apps()
