import multiprocessing

bind = "0.0.0.0:8592"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
loglevel = "info"
accesslog = "-"
errorlog = "-"