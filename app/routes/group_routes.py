from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, flash

from extensions import conexion


group_bp = Blueprint("group", __name__)


@group_bp.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

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
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@group_bp.route('/group/<int:ID>')
def group_detail(ID):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

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
            current_user_id=int(user_id)
        )

    except Exception as ex:
        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@group_bp.route('/group/create', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    try:
        creator_user = session['user_id']
        group_name = request.form.get('group_name')
        invited_users = request.form.getlist('invited_users')

        if not group_name:
            flash("El nombre del grupo es obligatorio")
            return redirect(url_for('group.main'))

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

        return redirect(url_for('group.group_detail', ID=group_id))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500


@group_bp.route('/group/<int:ID>/delete', methods=['POST'])
def delete_group(ID):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    try:
        user_id = session['user_id']
        cursor = conexion.connection.cursor()

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
            return redirect(url_for('group.main'))

        group_creator = group[2]

        if group_creator != user_id:
            cursor.close()
            flash("Solo el creador del grupo puede borrarlo")
            return redirect(url_for('group.group_detail', ID=ID))

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
            return redirect(url_for('group.group_detail', ID=ID))

        cursor.execute(
            """
            DELETE es
            FROM `expense_shared` es
            INNER JOIN `expenses` e ON es.EXPENSE_ID = e.ID
            WHERE e.GROUP_ID = %s
            """,
            (ID,)
        )

        cursor.execute(
            """
            DELETE FROM `expenses`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        cursor.execute(
            """
            DELETE FROM `group_users`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

        cursor.execute(
            """
            DELETE FROM `debts`
            WHERE GROUP_ID = %s
            """,
            (ID,)
        )

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
        return redirect(url_for('group.main'))

    except Exception as ex:
        try:
            conexion.connection.rollback()
        except Exception:
            pass

        return jsonify({
            "mensaje": "Error",
            "error": str(ex)
        }), 500