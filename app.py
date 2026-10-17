from flask import Flask
from config import Config
from routes.posts import posts_bp
from routes.tags import tags_bp
from routes.favorites import favorites_bp
from routes.users import users_bp
from routes.proxy import proxy_bp
from routes.admin import admin_bp
from routes.votes import votes_bp
from routes.comments import comments_bp
from routes.notes import notes_bp
from routes.pools import pools_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(posts_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(votes_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(pools_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=9000) 