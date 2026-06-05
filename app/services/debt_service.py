def recalculate_group_debts(cursor, group_id):
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

        user_a = min(from_user, to_user)
        user_b = max(from_user, to_user)
        pair_key = (user_a, user_b)

        if pair_key not in pair_balances:
            pair_balances[pair_key] = 0.0

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