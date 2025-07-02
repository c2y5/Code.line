PORT="$1"

kill -9 $(lsof -ti:$PORT) 2>/dev/null
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

gunicorn -b ":$PORT" app:app \
  --timeout 120 \
  --access-logfile - \
  --access-logformat '%(h)s - - [%(t)s] "%(r)s" %(s)s -' \
  --error-logfile - \
  --capture-output 2>&1 | tee -a app.log
