from backend.app.database.connection import get_db_connection
from backend.app.modules.ingestion.schemas import MessageIn


def save_message(data: MessageIn):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO raw_messages
            (customer_id, source, message, received_at)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                data.customer_id,
                data.source,
                data.message,
                data.received_at,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()