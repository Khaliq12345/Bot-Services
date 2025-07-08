from contextlib import contextmanager
import pika
from core.config import (
    RABBIT_MQ_HOST,
    RABBIT_MQ_USERNAME,
    RABBIT_MQ_PASSWORD,
    RABBIT_MQ_PORT,
)


@contextmanager
def get_pika_session():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBIT_MQ_HOST,
            port=RABBIT_MQ_PORT,
            credentials=pika.PlainCredentials(
                username=RABBIT_MQ_USERNAME,
                password=RABBIT_MQ_PASSWORD,
            ),
        )
    )
    try:
        yield connection
    except Exception as e:
        print(f"RabbitMq connection errro - {e}")
    finally:
        connection.close()

