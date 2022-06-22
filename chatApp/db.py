import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types = sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

        return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

# g es un objeto especial que es unico para cada request, es usado para guardar datos que pueden ser
# accedidos por multiples funciones durante un request. La conexion es guardada y reusada en vez de
# crear una nueva conexión si get_db es llamada una segunda vez durante el mismo request

# current_app es otro objeto especial que apunta a la aplicación de Flask que maneja el request. Dado que
# se usa una application factory(en __init__.py), no hay un objeto aplicación cuando se está escribiendo
# el resto del código. get_db se va a llamar cuando se haya creado una aplicación y esté manejando un
# request

# sqlite3.connect establece una conexión con el archivo apuntado por DATABASE
# sqlite3.Row le dice a la conexión que devuelva filas que se comporten como diccionarios, esto permite
# acceder a las columnas por nombre

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """"Clear the existing data and create new tables."""
    init_db()
    click.echo('Database initialized.')

# open_resource() abre un archivo relativo al paquete chatApp
# click.command() define un comando de linea llamado init-db que llama la función init_db y muestra
# mensaje al usuario

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

# app.teardown_appcontext() le dice a Flask que llame esa funcion para limpiar despues de devolver la
# respuesta

# app.cli.add_command() añade un nuevo comando que puede ser llamado con un comando de Flask

