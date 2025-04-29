# api/index.py
from flask_app import app as application  # ou o nome do seu app

def handler(event, context):
    return application(event, context)
