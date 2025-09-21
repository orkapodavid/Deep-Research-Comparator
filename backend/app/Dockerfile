FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding .env files via .dockerignore)
COPY . .

# Create a script to wait for postgres and run the app
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for postgres\n\
until pg_isready -h postgres -p 5432 -U deepresearch_user; do\n\
  echo "Waiting for postgres..."\n\
  sleep 2\n\
done\n\
\n\
echo "PostgreSQL is ready!"\n\
\n\
# Create tables if they don'\''t exist\n\
python create_tables.py || echo "Tables creation completed or already exist"\n\
\n\
# Insert initial data if needed\n\
python insert_databases.py || echo "Database seeding completed or already done"\n\
\n\
# Start the application\n\
exec python app.py' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 5001

ENTRYPOINT ["/app/entrypoint.sh"]