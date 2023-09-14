import pika
import threading
import tkinter as tk


class CollaborativeTextEditor:
    def __init__(self, exchange_name, exchange_type, rabbitmq_server_url):
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.rabbitmq_server_url = rabbitmq_server_url
        # establish connection with the rabbit mq server
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(rabbitmq_server_url))
        self.channel = self.connection.channel()

        # add the exchange
        self.channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type)

        # create a queue using a random name (generate by the rabbitmq itself)
        # the queue will be delted automatically when the connection is lost
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = result.method.queue

        self.channel.queue_bind(queue=self.queue_name, exchange=exchange_name)

        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self.receive_message, auto_ack=True)

        self.stop_listening_flag = threading.Event()
        threading.Thread(target=self.channel.start_consuming).start()
        self.root = tk.Tk()
        self.root.title("Collaborative Text Editor")
        self.text_widget = tk.Text(self.root)
        self.text_widget.pack()
        self.previous_content = ""
        self.text_widget.bind("<KeyRelease>", self.on_key)
        self.cursor = "1.0"
        self.root.mainloop()

    def on_key(self, event):
        self.cursor = self.text_widget.index(tk.INSERT)
        text_widget_content = self.text_widget.get("1.0", "end-1c")
        if text_widget_content != self.previous_content:
            self.send_message(text_widget_content)
            self.previous_content = text_widget_content

    def send_message(self, message):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.rabbitmq_server_url))
        channel = connection.channel()
        channel.basic_publish(
            exchange=self.exchange_name, routing_key="", body=message)

    def receive_message(self, ch, method, properties, body):
        message = body.decode()
        self.set_text_content(message)
        self.text_widget.mark_set(tk.INSERT, self.cursor)

    def set_text_content(self, content):
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", content)


def main():
    collaborative_text_editor = CollaborativeTextEditor(
        "text-editor", "fanout", "localhost")


if __name__ == '__main__':
    main()
