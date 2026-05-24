from flask import Flask, render_template, jsonify,request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash,check_password_hash

app = Flask(__name__)
app.secret_key = "clave_temporal_para_desarrollo"

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'reparto_gastos'
app.config['MYSQL_PORT'] = 3306

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
    hashed_password = generate_password_hash(password)

    if not name or not email or not password or not confirm_password:
        flash("Todos los campos son obligatorios")
        return redirect(url_for('login_page'))

    if password != confirm_password:
        flash("Las contraseñas no coinciden")
        return redirect(url_for('login_page'))

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
            SELECT DISTINCT g.ID, g.NAME
            FROM `groups` g
            LEFT JOIN `group_users` gu ON gu.GROUP_ID = g.ID
            WHERE g.CREATOR_USER = %s
               OR gu.USER_INVITED = %s
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
            members=members
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

        cursor = conexion.connection.cursor()

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

        shared_amount = round(amount / len(shared_users), 2)

        for user_id in shared_users:
            cursor.execute(
                """
                INSERT INTO `expense_shared`
                (`EXPENSE_ID`, `USER_ID`, `AMOUNT`)
                VALUES (%s, %s, %s)
                """,
                (expense_id, user_id, shared_amount)
            )

        conexion.connection.commit()
        cursor.close()

        return redirect(url_for('group_detail', ID=ID))

    except Exception as ex:
        conexion.connection.rollback()
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

if __name__ == '__main__':
    app.run(debug=True)