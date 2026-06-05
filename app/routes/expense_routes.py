from flask import Blueprint, jsonify, request, redirect, url_for, session

from extensions import conexion
from services.debt_service import recalculate_group_debts


expense_bp = Blueprint("expense", __name__)


@expense_bp.route('/group/<int:ID>/expense/create', methods=['POST'])
def create_expense(ID):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

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
            cursor.close()
            return jsonify({
                "mensaje": "Error",
                "error": "Faltan campos obligatorios"
            }), 400

        if not shared_users:
            cursor.close()
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

        recalculate_group_debts(cursor, ID)

        conexion.connection.commit()
        cursor.close()

        return redirect(url_for('group.group_detail', ID=ID))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@expense_bp.route('/expense/<int:ID>/shared-users')
def get_expense_shared_users(ID):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

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