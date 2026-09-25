#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "from tracker.public_user import get_public_user; get_public_user(); print('public_api user ready')"
