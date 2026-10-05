[project]
name = "{{ project_name }}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "rusjango",
]

[tool.rusjango]
settings = "settings.py"
app = "main:app"
