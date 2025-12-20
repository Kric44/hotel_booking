@echo off
call venv\Scripts\activate
python -m flask --app hotel_booking:app run --debug --port 5000
pause