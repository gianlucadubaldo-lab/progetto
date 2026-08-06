from flask import Flask
from database import users_collection
from blueprints.auth import auth_bp, bcrypt, User
from blueprints.home import home_bp
from blueprints.inventario import inventario_bp
from blueprints.cassa import cassa_bp
from blueprints.cameriere import cameriere_bp
from blueprints.moduli import moduli_bp
from blueprints.admin import admin_bp
from blueprints.stats import stats_bp
from flask_login import LoginManager
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Inizializzazione bcrypt
bcrypt.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None

# Registrazione Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(cassa_bp)
app.register_blueprint(cameriere_bp)
app.register_blueprint(moduli_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(stats_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
