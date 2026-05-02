from flask import Flask, render_template, jsonify,request, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'reparto_gastos'
app.config['MYSQL_PORT'] = 3306

conexion = MySQL(app)


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/main')
def main():
    data = {}

    try:
        cursor = conexion.connection.cursor()
        cursor.execute("SELECT ID,NAME FROM `groups`")
        groups = cursor.fetchall()
        cursor.close()

        return render_template("main.html", groups=groups)

    except Exception as ex:
        data["mensaje"] = "Error"
        data["error"] = str(ex)
        return jsonify(data)

@app.route('/group/<int:ID>')
def group_detail(ID):
    data = {}

    try:
        cursor = conexion.connection.cursor()

        # Datos del grupo
        cursor.execute(
            "SELECT ID, NAME, CREATOR_USER FROM `groups` WHERE ID = %s",
            (ID,)
        )
        group = cursor.fetchone()

        if group is None:
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "Grupo no encontrado"
            }), 404

        # Gastos del grupo
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
            WHERE e.GROUP_ID = %s
            ORDER BY e.EXPENSE_DATE DESC
            """,
            (ID,)
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

@app.route('/group/<int:ID>/expense/create', methods=['POST'])
def create_expense(ID):
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
    try:
        cursor = conexion.connection.cursor()
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