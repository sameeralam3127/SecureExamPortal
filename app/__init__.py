from .auth.routes import auth_bp
app.register_blueprint(auth_bp)
from flask_talisman import Talisman
Talisman(app)
