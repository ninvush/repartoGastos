from flask import Flask, render_template, jsonify,request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash,check_password_hash
import os
import secrets
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from dotenv import load_dotenv

app = Flask(__name__)


load_dotenv()

app.secret_key = os.environ.get("SECRET_KEY", "clave_temporal_para_desarrollo")

app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST", "127.0.0.1")
app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER", "root")
app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD", "")
app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB", "reparto_gastos")
app.config['MYSQL_PORT'] = int(os.environ.get("MYSQL_PORT", 3306))

app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_DEFAULT_SENDER")

app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get("GOOGLE_MAPS_API_KEY", "")

mail = Mail(app)

conexion = MySQL(app)

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
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
            return redirect(url_for('login_page'))

        user_id = user[0]
        user_name = user[1]
        user_email = user[2]
        user_password = user[3]

        if not check_password_hash(user_password, password):
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for('login_page'))

        session['user_id'] = user_id
        session['user_name'] = user_name
        session['user_email'] = user_email

        return redirect(url_for('main'))

    except Exception as ex:
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not name or not email or not password or not confirm_password:
        flash("Todos los campos son obligatorios")
        return redirect(url_for('login_page'))

    if password != confirm_password:
        flash("Las contraseñas no coinciden")
        return redirect(url_for('login_page'))

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
            return redirect(url_for('login_page'))

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
        return redirect(url_for('login_page'))

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente")
    return redirect(url_for('login_page'))

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    data = {}

    try:
        user_id = session['user_id']

        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT g.ID, g.NAME
            FROM `groups` g
            WHERE g.CREATOR_USER = %s
               OR EXISTS (
                    SELECT 1
                    FROM `group_users` gu
                    WHERE gu.GROUP_ID = g.ID
                      AND gu.USER_INVITED = %s
               )
            ORDER BY g.CREATION DESC
            """,
            (user_id, user_id)
        )

        groups = cursor.fetchall()

        cursor.execute(
            """
            SELECT ID, NAME, EMAIL
            FROM `users`
            WHERE ID != %s
            ORDER BY NAME
            """,
            (user_id,)
        )

        users = cursor.fetchall()

        cursor.close()

        return render_template(
            "main.html",
            groups=groups,
            users=users
        )

    except Exception as ex:
        data["mensaje"] = "Error"
        data["error"] = str(ex)
        return jsonify(data), 500
    
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')

    if not email:
        flash("Introduce un correo electrónico", "danger")
        return redirect(url_for('login_page'))

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

        # Mensaje genérico por seguridad
        if user is None:
            cursor.close()
            flash("Si el correo existe, recibirás un enlace para restablecer la contraseña", "success")
            return redirect(url_for('login_page'))

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

        base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
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
        return redirect(url_for('login_page'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500
    
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
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
            return redirect(url_for('login_page'))

        reset_id = reset_request[0]
        user_id = reset_request[1]
        expiration_time = reset_request[2]
        used = reset_request[3]

        if used:
            cursor.close()
            flash("Este enlace ya fue utilizado", "danger")
            return redirect(url_for('login_page'))

        if datetime.now() > expiration_time:
            cursor.close()
            flash("El enlace ha caducado", "danger")
            return redirect(url_for('login_page'))

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
        return redirect(url_for('login_page'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/group/<int:ID>')
def group_detail(ID):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    data = {}

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

        # Datos del grupo, pero solo si el usuario pertenece
        cursor.execute(
            """
            SELECT g.ID, g.NAME, g.CREATOR_USER
            FROM `groups` g
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE g.ID = %s
              AND (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                  )
            LIMIT 1
            """,
            (ID, user_id, user_id)
        )

        group = cursor.fetchone()

        if group is None:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "No tienes permiso para ver este grupo o el grupo no existe"
            }), 403

        cursor.execute(
            """
            SELECT 
                e.ID,
                e.NAME,
                e.AMOUNT,
                e.EXPENSE_DATE,
                u.NAME AS PAID_BY,
                e.USER_ID,
                e.GOOGLE_API
            FROM `expenses` e
            INNER JOIN `users` u ON e.USER_ID = u.ID
            INNER JOIN `groups` g ON e.GROUP_ID = g.ID
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE e.GROUP_ID = %s
            AND (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                )
            GROUP BY e.ID, e.NAME, e.AMOUNT, e.EXPENSE_DATE, u.NAME, e.USER_ID, e.GOOGLE_API
            ORDER BY e.EXPENSE_DATE DESC
            """,
            (ID, user_id, user_id)
        )
        expenses = cursor.fetchall()

        # Integrantes del grupo:
        # 1. Creador del grupo
        # 2. Usuarios invitados en group_users
        cursor.execute(
            """
            SELECT DISTINCT u.ID, u.NAME, u.EMAIL
            FROM `users` u
            WHERE u.ID = (
                SELECT CREATOR_USER 
                FROM `groups` 
                WHERE ID = %s
            )

            UNION

            SELECT DISTINCT u.ID, u.NAME, u.EMAIL
            FROM `group_users` gu
            INNER JOIN `users` u ON gu.USER_INVITED = u.ID
            WHERE gu.GROUP_ID = %s

            ORDER BY NAME
            """,
            (ID, ID)
        )
        members = cursor.fetchall()

        cursor.close()

        return render_template(
            "group_detail.html",
            group=group,
            expenses=expenses,
            members=members,
            current_user_id=int(user_id),
            google_maps_api_key=app.config['GOOGLE_MAPS_API_KEY']
        )

    except Exception as ex:
        data["mensaje"] = "Error"
        data["error"] = str(ex)
        return jsonify(data), 500

@app.route('/group/create', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    try:
        creator_user = session['user_id']
        group_name = request.form.get('group_name')
        invited_users = request.form.getlist('invited_users')

        if not group_name:
            flash("El nombre del grupo es obligatorio")
            return redirect(url_for('main'))

        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            INSERT INTO `groups`
            (`NAME`, `CREATOR_USER`, `CREATION`)
            VALUES (%s, %s, NOW())
            """,
            (group_name, creator_user)
        )

        group_id = cursor.lastrowid

        for invited_user in invited_users:
            invited_user = int(invited_user)

            if invited_user == creator_user:
                continue

            cursor.execute(
                """
                INSERT INTO `group_users`
                (`USER_INVITED`, `INVITE_USER`, `GROUP_ID`, `INVITE_TIME`)
                VALUES (%s, %s, %s, NOW())
                """,
                (invited_user, creator_user, group_id)
            )

        conexion.connection.commit()
        cursor.close()

        return redirect(url_for('group_detail', ID=group_id))

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

def recalculate_group_debts(cursor, group_id):
    """
    Recalcula las deudas de un grupo compensando deudas cruzadas por pareja.

    Ejemplo:
    - Sergio debe a Claudia 500
    - Claudia debe a Sergio 320

    Resultado:
    - Sergio debe a Claudia 180

    Solo compensa dentro del mismo grupo.
    """

    cursor.execute(
        """
        SELECT NAME
        FROM `groups`
        WHERE ID = %s
        """,
        (group_id,)
    )

    group = cursor.fetchone()

    if group is None:
        raise Exception("Grupo no encontrado al recalcular deudas")

    group_name = group[0]

    cursor.execute(
        """
        DELETE FROM `debts`
        WHERE GROUP_ID = %s
        """,
        (group_id,)
    )

    cursor.execute(
        """
        SELECT
            es.USER_ID AS FROM_USER,
            e.USER_ID AS TO_USER,
            ROUND(SUM(es.AMOUNT), 2) AS AMOUNT
        FROM `expense_shared` es
        INNER JOIN `expenses` e ON es.EXPENSE_ID = e.ID
        WHERE e.GROUP_ID = %s
          AND es.USER_ID != e.USER_ID
        GROUP BY es.USER_ID, e.USER_ID
        HAVING ROUND(SUM(es.AMOUNT), 2) > 0
        """,
        (group_id,)
    )

    raw_debts = cursor.fetchall()

    pair_balances = {}

    for from_user, to_user, amount in raw_debts:
        from_user = int(from_user)
        to_user = int(to_user)
        amount = round(float(amount), 2)

        # Creamos una clave común para la pareja, sin importar dirección.
        # Ejemplo: Sergio-Claudia y Claudia-Sergio usan la misma clave.
        user_a = min(from_user, to_user)
        user_b = max(from_user, to_user)
        pair_key = (user_a, user_b)

        if pair_key not in pair_balances:
            pair_balances[pair_key] = 0.0

        # Si la deuda va del menor ID al mayor ID, suma.
        # Si va del mayor ID al menor ID, resta.
        if from_user == user_a and to_user == user_b:
            pair_balances[pair_key] += amount
        else:
            pair_balances[pair_key] -= amount

    for (user_a, user_b), balance in pair_balances.items():
        balance = round(balance, 2)

        if balance == 0:
            continue

        if balance > 0:
            from_user = user_a
            to_user = user_b
            final_amount = balance
        else:
            from_user = user_b
            to_user = user_a
            final_amount = abs(balance)

        cursor.execute(
            """
            INSERT INTO `debts`
            (`FROM_USER`, `TO_USER`, `AMOUNT`, `GROUP_ID`, `GROUP_NAME`, `CREATION_TIME`, `MODIFICATION_TIME`)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                from_user,
                to_user,
                round(final_amount, 2),
                group_id,
                group_name
            )
        )

@app.route('/debts/settle', methods=['POST'])
def settle_debt():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    try:
        user_id = session['user_id']

        group_id = request.form.get('group_id')
        to_user_id = request.form.get('to_user_id')

        if not group_id or not to_user_id:
            return jsonify({
                "mensaje": "Error",
                "error": "Faltan datos para saldar la deuda"
            }), 400

        group_id = int(group_id)
        to_user_id = int(to_user_id)

        cursor = conexion.connection.cursor()

        # Seguridad: comprobar que el usuario pertenece al grupo
        cursor.execute(
            """
            SELECT g.ID
            FROM `groups` g
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE g.ID = %s
              AND (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                  )
            LIMIT 1
            """,
            (group_id, user_id, user_id)
        )

        has_access = cursor.fetchone()

        if has_access is None:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "No tienes permiso para saldar deudas en este grupo"
            }), 403

        # Borra solo la deuda donde el usuario logueado debe a esa persona
        cursor.execute(
            """
            DELETE FROM `debts`
            WHERE GROUP_ID = %s
              AND FROM_USER = %s
              AND TO_USER = %s
            """,
            (group_id, user_id, to_user_id)
        )

        conexion.connection.commit()
        cursor.close()

        flash("Deuda saldada correctamente")
        return redirect(url_for('debts'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/group/<int:ID>/expense/create', methods=['POST'])
def create_expense(ID):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    data = {}

    try:
        expense_id = request.form.get('expense_id')

        if expense_id:
            expense_id = int(expense_id)

        name = request.form.get('name')
        amount = request.form.get('amount')
        paid_by = request.form.get('paid_by')
        expense_date = request.form.get('expense_date')
        google_api = request.form.get('google_api') or ''
        shared_users = request.form.getlist('shared_users')

        cursor = conexion.connection.cursor()

        logged_user_id = session['user_id']

        cursor.execute(
            """
            SELECT g.ID
            FROM `groups` g
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE g.ID = %s
              AND (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                  )
            LIMIT 1
            """,
            (ID, logged_user_id, logged_user_id)
        )

        has_access = cursor.fetchone()

        if has_access is None:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "No tienes permiso para modificar este grupo"
            }), 403

        if not name or not amount or not paid_by or not expense_date:
            return jsonify({
                "mensaje": "Error",
                "error": "Faltan campos obligatorios"
            }), 400

        if not shared_users:
            return jsonify({
                "mensaje": "Error",
                "error": "Debes seleccionar al menos un integrante para repartir el gasto"
            }), 400

        amount = float(amount)
        paid_by = int(paid_by)
        shared_users = [int(user_id) for user_id in shared_users]

        cursor.execute(
            """
            SELECT DISTINCT USER_ID FROM (
                SELECT CREATOR_USER AS USER_ID
                FROM `groups`
                WHERE ID = %s

                UNION

                SELECT USER_INVITED AS USER_ID
                FROM `group_users`
                WHERE GROUP_ID = %s
            ) AS members
            """,
            (ID, ID)
        )

        valid_members = [row[0] for row in cursor.fetchall()]

        if paid_by not in valid_members:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "El usuario que pagó no pertenece al grupo"
            }), 400

        for user_id in shared_users:
            if user_id not in valid_members:
                cursor.close()
                return jsonify({
                    "mensaje": "Error",
                    "error": f"El usuario {user_id} no pertenece al grupo"
                }), 400

        if expense_id:
            cursor.execute(
                """
                UPDATE `expenses`
                SET 
                    USER_ID = %s,
                    NAME = %s,
                    AMOUNT = %s,
                    GOOGLE_API = %s,
                    EXPENSE_DATE = %s,
                    MODIFICATION_TIME = NOW()
                WHERE ID = %s AND GROUP_ID = %s
                """,
                (paid_by, name, amount, google_api, expense_date, expense_id, ID)
            )

            cursor.execute(
                "DELETE FROM `expense_shared` WHERE EXPENSE_ID = %s",
                (expense_id,)
            )

        else:
            cursor.execute(
                """
                INSERT INTO `expenses`
                (`GROUP_ID`, `USER_ID`, `NAME`, `AMOUNT`, `GOOGLE_API`, `EXPENSE_DATE`, `MODIFICATION_TIME`)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (ID, paid_by, name, amount, google_api, expense_date)
            )

            expense_id = cursor.lastrowid

        base_amount = round(amount / len(shared_users), 2)
        amounts = [base_amount] * len(shared_users)

        difference = round(amount - sum(amounts), 2)

        if difference != 0:
            amounts[0] = round(amounts[0] + difference, 2)

        for user_id, user_share in zip(shared_users, amounts):
            cursor.execute(
                """
                INSERT INTO `expense_shared`
                (`EXPENSE_ID`, `USER_ID`, `AMOUNT`)
                VALUES (%s, %s, %s)
                """,
                (expense_id, user_id, user_share)
            )

        # Recalcular deudas del grupo después de crear/editar el gasto
        recalculate_group_debts(cursor, ID)

        conexion.connection.commit()
        cursor.close()

        return redirect(url_for('group_detail', ID=ID))

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/group/<int:ID>/delete', methods=['POST'])
def delete_group(ID):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

        # Comprobar que el grupo existe y que el usuario logueado es el creador
        cursor.execute(
            """
            SELECT ID, NAME, CREATOR_USER
            FROM `groups`
            WHERE ID = %s
            """,
            (ID,)
        )

        group = cursor.fetchone()

        if group is None:
            cursor.close()
            flash("El grupo no existe")
            return redirect(url_for('main'))

        group_creator = group[2]

        if group_creator != user_id:
            cursor.close()
            flash("Solo el creador del grupo puede borrarlo")
            return redirect(url_for('group_detail', ID=ID))

        # Comprobar si hay deudas pendientes del grupo
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM `debts`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        pending_debts = cursor.fetchone()[0]

        if pending_debts > 0:
            cursor.close()
            flash("No puedes borrar este grupo porque todavía tiene deudas pendientes")
            return redirect(url_for('group_detail', ID=ID))

        # Borrar repartos de gastos del grupo
        cursor.execute(
            """
            DELETE es
            FROM `expense_shared` es
            INNER JOIN `expenses` e ON es.EXPENSE_ID = e.ID
            WHERE e.GROUP_ID = %s
            """,
            (ID,)
        )

        # Borrar gastos del grupo
        cursor.execute(
            """
            DELETE FROM `expenses`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        # Borrar usuarios invitados al grupo
        cursor.execute(
            """
            DELETE FROM `group_users`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        # Por seguridad, borrar debts si no hubiera ninguna pendiente.
        # Normalmente no borrará nada porque ya comprobamos que COUNT = 0.
        cursor.execute(
            """
            DELETE FROM `debts`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        # Borrar grupo
        cursor.execute(
            """
            DELETE FROM `groups`
            WHERE ID = %s
            """,
            (ID,)
        )

        conexion.connection.commit()
        cursor.close()

        flash("Grupo eliminado correctamente")
        return redirect(url_for('main'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

@app.route('/expense/<int:ID>/shared-users')
def get_expense_shared_users(ID):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

        # Comprobar que el usuario tiene acceso al grupo del gasto
        cursor.execute(
            """
            SELECT e.ID
            FROM `expenses` e
            INNER JOIN `groups` g ON e.GROUP_ID = g.ID
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE e.ID = %s
              AND (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                  )
            LIMIT 1
            """,
            (ID, user_id, user_id)
        )

        allowed_expense = cursor.fetchone()

        if allowed_expense is None:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "No tienes permiso para ver este gasto"
            }), 403

        cursor.execute(
            """
            SELECT USER_ID
            FROM `expense_shared`
            WHERE EXPENSE_ID = %s
            """,
            (ID,)
        )

        users = [row[0] for row in cursor.fetchall()]
        cursor.close()

        return jsonify({
            "users": users
        })

    except Exception as ex:
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500
    
@app.route('/debts')
def debts():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    print("USUARIO LOGUEADO:", session['user_id'], session.get('user_name'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

        cursor.execute(
            """
            SELECT 
                d.GROUP_ID,
                d.GROUP_NAME,
                d.FROM_USER,
                from_user.NAME AS FROM_USER_NAME,
                d.TO_USER,
                to_user.NAME AS TO_USER_NAME,
                d.AMOUNT
            FROM `debts` d
            INNER JOIN `users` from_user ON d.FROM_USER = from_user.ID
            INNER JOIN `users` to_user ON d.TO_USER = to_user.ID
            INNER JOIN `groups` g ON d.GROUP_ID = g.ID
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE (
                    g.CREATOR_USER = %s
                    OR gu.USER_INVITED = %s
                  )
              AND (
                    d.FROM_USER = %s
                    OR d.TO_USER = %s
                  )
            GROUP BY 
                d.ID,
                d.GROUP_ID,
                d.GROUP_NAME,
                d.FROM_USER,
                from_user.NAME,
                d.TO_USER,
                to_user.NAME,
                d.AMOUNT
            ORDER BY d.GROUP_NAME, d.AMOUNT DESC
            """,
            (user_id, user_id, user_id, user_id)
        )

        debts_rows = cursor.fetchall()
        cursor.close()

        groups_debts = {}

        for row in debts_rows:
            group_id = row[0]
            group_name = row[1]
            from_user_id = row[2]
            from_user_name = row[3]
            to_user_id = row[4]
            to_user_name = row[5]
            amount = float(row[6])

            if group_id not in groups_debts:
                groups_debts[group_id] = {
                    "id": group_id,
                    "name": group_name,
                    "items": []
                }

            groups_debts[group_id]["items"].append({
                "from_user_id": from_user_id,
                "from_user_name": from_user_name,
                "to_user_id": to_user_id,
                "to_user_name": to_user_name,
                "amount": amount,
                "is_debtor": from_user_id == user_id,
                "is_creditor": to_user_id == user_id
            })

        return render_template(
            "debts.html",
            groups_debts=list(groups_debts.values()),
            current_user_id=int(user_id)
        )

    except Exception as ex:
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500

if __name__ == '__main__':
    app.run()