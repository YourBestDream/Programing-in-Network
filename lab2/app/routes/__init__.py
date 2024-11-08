from .crud import crud_blueprint
from .chat import chat_blueprint

def register_routes(app):
    app.register_blueprint(crud_blueprint, url_prefix='/api')
    app.register_blueprint(chat_blueprint, url_prefix='/chat')
