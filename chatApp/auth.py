import functools

from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from chatApp.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Esto crea un blueprint llamado auth. Como el objeto aplicación, blueprint necesita saber donde
# está definido, entonces __name__ es pasado como segundo argumento. El url_prefix se antepondrá
# a todas las URLs asociadas con el blueprint

###         REGISTER       ###

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (? , ?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered"
            else:
                return redirect(url_for("auth.login"))
        
        flash(error)

    return render_template('auth/register.html')

# Lo que está haciendo la view function register es:

# 1- @bp.route asocia la URL /register con la view function register. Cuando Flask recibe un request a
# /auth/register, esto llamará a la view register y usará el valor de retorno como respuesta
# 2- Si el usuario envía el formulario, request.method será POST. En este caso, se validará el input
# 3- request.form es un tipo especial de diccionario que mapea las claves y valores enviados. El usuario
# va a ingresar su usuario y contraseña
# 4- Se valida que el usuario y contraseña no estén vacios
# 5- Si la validación es exitosa, inserta los datos en la base de datos
#   db.execute toma una consulta SQL con placeholders '?' para cualquier ingreso de usuario, y una
#   tupla de valores para reemplazar los placeholders '?'
#   Por seguridad, las contraseñas no deben ser guardadas en la base de datos directamente, en cambio
#   generate_password_hash() se usa para 'hashear' las contraseñas, y guardar el hash. db.commit() guarda
#   los cambios
#   sqlite3.IntegrityError va a ocurrir si el usuario ya existe en la base de datos, que será mostrado al
#   usuario como error de validación
# 6- Despues de guardar el usuario, será redirigido a la pagina de login. url_for() genera la URL para
# la view de login basado en el nombre. Redirect() genera una respuesta de redirección a la URL generada
# 7- Si la validación falla, el error será mostrado al usuario. flash() guarda un mensaje que puede ser
# recuperado cuando se renderiza la plantilla(html)
# 8- Cuando el usuario inicialmente navega a /auth/register, o hubo un error de validación, una pagina
# HTML con el formulario de registro será mostrado. render_template() rederizará la plantilla que contiene
# HTML

###       LOGIN       ###

@bp.route('/login', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username)
        ).fetchone

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)

    return render_template('auth/login.html')

# 1- Primero se consulta el usuario, fetchone() devuelve una fila de la consulta. Si no hay resultados
# devuelve None
# 2- check_password_hash() 'hashea' la contraseña ingresada y las compara de manera segura con la contraseña
# guardada en la base de datos. Si son iguales, la contraseña es valida
# 3- session es un diccionario que guarda datos durante el request. Cuando la validación es exitosa, el id
# del usuario se guarda en una nueva sesión.Los datos son guardados en una cookie que se envía al navegador
# y el navegador la manda de vuelta con las siguientes request(peticiones). Flask firma de forma segura los
# datos para que no puedan ser manipulados

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id)
        ).fetchone()

# bp.before_app_request() registra una función que corre antes de la view funciton, sin importar que
# URL fue pedida. load_logged_in_user chequea si hay guardado un id de usuario en la sesión y trae los
# datos del usuario de la base de daots, guardandolos en g.user, que duran lo que dure la petición.
# Si no habia id de usuario, o el id no existe, g.user va ser None

###       LOGOUT       ###

@bp.route('/logout')
def loggout():
    session.clear()
    return redirect(url_for('index'))

# Para cerrar sesión es necesario quitar el id del usuario de la sesión. Luego load_logged_in_user no
# cargará un usuario en las siguientes peticiones

### EN CASO DE NECESITAR AUTENTICACIÓN EN OTRAS VIEWS ###

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view

# Este decorador devuelve una nueva view function que envuelve a la view original que se le aplicó. La
# nueva función chequea si el usuario está cargado y redirige a la pagina de inicio de sesión en caso
# contrario. Si el usuario está cargado, la view original es llamada y continua normalmente
