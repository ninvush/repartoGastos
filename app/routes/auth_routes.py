import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

from extensions import conexion, mail


auth_bp = Blueprint("auth", __name__)


@auth_bp.route('/')
def login_page():
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT ID, NAME, EMAIL, PASSWORD
            FROM `users`
            WHERE EMAIL = %s OR NAME = %s
            """,
            (username, username)
        )

        user = cursor.fetchone()
        cursor.close()

        if user is None:
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for('auth.login_page'))

        user_id = user[0]
        user_name = user[1]
        user_email = user[2]
        user_password = user[3]

        if not check_password_hash(user_password, password):
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for('auth.login_page'))

        session['user_id'] = user_id
        session['user_name'] = user_name
        session['user_email'] = user_email

        return redirect(url_for('group.main'))

    except Exception as ex:
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not name or not email or not password or not confirm_password:
        flash("Todos los campos son obligatorios")
        return redirect(url_for('auth.login_page'))

    if password != confirm_password:
        flash("Las contraseñas no coinciden")
        return redirect(url_for('auth.login_page'))

    hashed_password = generate_password_hash(password)

    try:
        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT ID
            FROM `users`
            WHERE EMAIL = %s OR NAME = %s
            """,
            (email, name)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            flash("Ese usuario o correo ya existe")
            return redirect(url_for('auth.login_page'))

        cursor.execute(
            """
            INSERT INTO `users`
            (`NAME`, `EMAIL`, `PASSWORD`)
            VALUES (%s, %s, %s)
            """,
            (name, email, hashed_password)
        )

        conexion.connection.commit()
        cursor.close()

        flash("Cuenta creada correctamente. Ya puedes iniciar sesión")
        return redirect(url_for('auth.login_page'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente")
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')

    if not email:
        flash("Introduce un correo electrónico", "danger")
        return redirect(url_for('auth.login_page'))

    try:
        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT ID, NAME, EMAIL
            FROM `users`
            WHERE EMAIL = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if user is None:
            cursor.close()
            flash("Si el correo existe, recibirás un enlace para restablecer la contraseña", "success")
            return redirect(url_for('auth.login_page'))

        user_id = user[0]
        user_name = user[1]
        user_email = user[2]

        token = secrets.token_urlsafe(48)
        expiration_time = datetime.now() + timedelta(minutes=30)

        cursor.execute(
            """
            INSERT INTO password_resets
            (USER_ID, TOKEN, EXPIRATION_TIME)
            VALUES (%s, %s, %s)
            """,
            (user_id, token, expiration_time)
        )

        conexion.connection.commit()
        cursor.close()

        base_url = current_app.config.get("APP_BASE_URL", "http://127.0.0.1:5000")
        reset_link = f"{base_url}/reset-password/{token}"

        msg = Message(
            subject="Restablecer contraseña",
            recipients=[user_email]
        )

        msg.body = f"""
Buenas {user_name},

Has solicitado restablecer tu contraseña.

Pulsa en este enlace para crear una nueva contraseña:

{reset_link}

Este enlace caduca en 30 minutos.

Si no has solicitado este cambio, puedes ignorar este correo o notificar al creador de la aplicación.
"""

        mail.send(msg)

        flash("Si el correo existe, recibirás un enlace para restablecer la contraseña", "success")
        return redirect(url_for('auth.login_page'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT ID, USER_ID, EXPIRATION_TIME, USED
            FROM password_resets
            WHERE TOKEN = %s
            """,
            (token,)
        )

        reset_request = cursor.fetchone()

        if reset_request is None:
            cursor.close()
            flash("El enlace no es válido", "danger")
            return redirect(url_for('auth.login_page'))

        reset_id = reset_request[0]
        user_id = reset_request[1]
        expiration_time = reset_request[2]
        used = reset_request[3]

        if used:
            cursor.close()
            flash("Este enlace ya fue utilizado", "danger")
            return redirect(url_for('auth.login_page'))

        if datetime.now() > expiration_time:
            cursor.close()
            flash("El enlace ha caducado", "danger")
            return redirect(url_for('auth.login_page'))

        if request.method == 'GET':
            cursor.close()
            return render_template("reset_password.html", token=token)

        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            cursor.close()
            flash("Todos los campos son obligatorios", "danger")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            cursor.close()
            flash("Las contraseñas no coinciden", "danger")
            return render_template("reset_password.html", token=token)

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            UPDATE `users`
            SET PASSWORD = %s
            WHERE ID = %s
            """,
            (hashed_password, user_id)
        )

        cursor.execute(
            """
            UPDATE password_resets
            SET USED = 1
            WHERE ID = %s
            """,
            (reset_id,)
        )

        conexion.connection.commit()
        cursor.close()

        flash("Contraseña actualizada correctamente. Ya puedes iniciar sesión", "success")
        return redirect(url_for('auth.login_page'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500