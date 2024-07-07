#!/usr/bin/env bash

# starts api app with enviroment varibles

JWT_SECRET_KEY="secretweynoBeSecret" DB_USER="ascii-pius" DB_PASSWORD="hng-sql" POSTGRES_DB="hng_db" DB_HOST="localhost" POSTGRES_PORT="5432" FLASK_APP="app.py" FLASK_ENV="production" flask run