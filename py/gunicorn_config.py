# gunicorn_config.py
bind = '127.0.0.1:8000'  # localhost の 8000番ポートでリッスン
workers = 2
timeout = 120
errorlog = '/home/rhzcitfl/public_html/history_flow_quiz/error.log'
loglevel = 'debug'
forwarded_allow_ips = '*'