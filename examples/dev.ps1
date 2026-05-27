# Run the hello example dev server (use from examples/ or repo root)
Set-Location $PSScriptRoot\hello
uv run python -m rusjango._dev @args
