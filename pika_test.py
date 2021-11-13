import pika, sys, os
from candle_data_service.candle_pb2 import Candle


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    bot_name = sys.argv[1]
    channel.queue_declare(queue=bot_name)
    channel.queue_bind(bot_name, "candles", "BTC_USDT_1m")
    channel.queue_bind(bot_name, "candles", "ETH_USDT_5m")

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)
        candle = Candle()
        candle.ParseFromString(body)
        print(str(candle))
    channel.basic_consume(queue=bot_name, on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)