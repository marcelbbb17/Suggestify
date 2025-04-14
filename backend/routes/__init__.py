from routes.auth import auth_bp
from routes.movies import movies_bp
from routes.recommendations import recommendations_bp
from routes.search import search_bp
from routes.watchlist import watchlist_bp
from routes.preferences import preferences_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(preferences_bp)