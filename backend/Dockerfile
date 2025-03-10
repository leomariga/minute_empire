FROM python:3.12-slim

WORKDIR /minute_empire

# Install Poetry
RUN pip install poetry==1.7.1

# Copy poetry configuration files
COPY pyproject.toml ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "minute_empire.main:app", "--host", "0.0.0.0", "--port", "8000"] 