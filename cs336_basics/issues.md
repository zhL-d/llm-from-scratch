1. current Dockerfile creates .venv inside /app, but you bind-mount /app, which hides that venv. Pick one (both are fine):

2. there are too many config layer, github action, start script, yml file, code