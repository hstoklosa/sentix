FROM python:3.12-slim

# The output streams are sent straight to terminal.
# REF: https://stackoverflow.com/a/59812588/13910414
ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/

# The correct way to use venv in a Docker container
# REF: https://pythonspeed.com/articles/activate-virtualenv-dockerfile
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /app

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /app/app

CMD ["fastapi", "dev", "app/main.py"]