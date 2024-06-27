from flask import Flask, send_from_directory,render_template
from pathlib import Path



def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=Path(app.instance_path) / 'db.sqlite3',
        SECRET_KEY='dev',
        UPLOAD_DIR=Path('.') / 'app/uploads'
    )
    
    try:
        Path(app.instance_path).mkdir()
    except OSError:
        pass 
    
    from . blog.views import bp as blog_bp
    app.register_blueprint(blog_bp)

    from . page.views import bp as page_bp
    app.register_blueprint(page_bp)

    from . users.views import bp as users_bp
    app.register_blueprint(users_bp)
    
    from . import db
    db.init_app(app)

    @app.route('/uploads/<filename>')
    def uploads(filename):
        return send_from_directory(app.config['UPLOAD_DIR'].absolute(), filename)
    

    return app