#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    # Initialize the migration repository
    flask db init
    flask db migrate
fi

echo "Running database migrations..."
flask db upgrade

# Start the application using Gunicorn, binding it to port 80
# Set the logging level to info and the timeout to 3600 seconds
exec gunicorn --bind 0.0.0.0:80 app:app --log-level info --timeout 3600
