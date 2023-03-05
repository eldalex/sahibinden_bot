broker_url = 'amqp://guest:guest@192.168.56.101//'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
result_backend = "rpc://"
enable_utc = True
imports = 'tasks_bot'