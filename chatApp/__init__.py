import os

from flask import Flask

def create_app(test_config = None):
    # create and configure the app

    # Crea instancia de Flask
    # __name__ es el nombre del modulo de python actual, la app lo necesita para saber
    # donde localizar ciertos paths
    # instance_relative_config = True le dice a la app que los archivos de configuración son relativos
    # a la carpeta de instancia. La carpeta de instancia se encuentra fuera de chatApp y puede contener
    # datos que no deberian ser enviados al control de versiones, como secretos de configuracion y el
    # archivo de base de datos
    app = Flask(__name__, instance_relative_config = True)

    #sets some default configuration that the app will use
    # SECRET_KEY es usada por flask y extensiones para mantener seguro los datos
    # luego debería ser cambiada a otra más seguta antes de desplegar el proyecto
    # DATABASE contiene el path donde la base de datos SQLite va a guardarse. Está bajo app.instance_path
    # que es el path que Flask ha elegido para la carpeta de instancia
    app.config.from_mapping(
        SECRET_KEY = 'dev',  
        DATABASE = os.path.join(app.instance_path, 'chatApp.sqlite')
    )


    # app.config.from_pyfile sobreescribe la configuracion default con valores tomados del archivo
    # config.py en la carpeta de instancia, si es que existe. Sirve por ejemplo para establecer una
    # SECRET_KEY real para el despliegue de la app
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent = True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    @app.route('/hello')
    def hello():
        return 'Hello world'

    return app