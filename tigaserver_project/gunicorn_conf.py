#workers = 8
workers = 10
bind = '127.0.0.1:49153'
max_requests = 5000
#timeout = 1200
timeout = 420
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = 'debug'