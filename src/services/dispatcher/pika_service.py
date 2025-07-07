from contextlib import contextmanager
import pika


@contextmanager
def get_pika_session():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    try:
        yield connection
    except Exception as e:
        print(f"RabbitMq connection errro - {e}")
    finally:
        connection.close()
