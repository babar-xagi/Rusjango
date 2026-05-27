[project]
name = "{{ project_name }}"
version = "0.1.0"
dependencies = [
    "rusjango",
]

[tool.rusjango]
settings = "settings.py"
app = "main:app"
