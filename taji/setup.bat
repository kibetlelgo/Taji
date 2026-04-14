@echo off
echo === Taji Setup ===
python -m pip install -r requirements.txt
python manage.py makemigrations core
python manage.py makemigrations loans
python manage.py migrate
python manage.py init_cycle
echo.
echo Create your admin account:
python manage.py createsuperuser
echo.
echo === Setup complete. Run: python manage.py runserver ===
