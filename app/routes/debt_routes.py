from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, flash

from extensions import conexion


debt_bp = Blueprint("debt", __name__)


@debt_bp.route('/debts')
def debts():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

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


@debt_bp.route('/debts/settle', methods=['POST'])
def settle_debt():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

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
        return redirect(url_for('debt.debts'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500