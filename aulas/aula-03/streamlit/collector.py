"""Coletor em memoria compartilhado pelas sessoes do dashboard; nao e historiador."""
import asyncio
import threading
from collections import deque
from opc_client import collect

class Collector:
    def __init__(self, endpoint, capacity=600):
        self.samples = deque(maxlen=capacity)
        self.error = "Aguardando primeira leitura OPC UA"
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=lambda: asyncio.run(collect(endpoint, self.publish, self.stop)), daemon=True)
        self.thread.start()

    def publish(self, sample, error):
        with self.lock:
            self.error = error
            if sample is not None:
                self.samples.append(sample)

    def snapshot(self):
        with self.lock:
            return list(self.samples), self.error

    def close(self):
        self.stop.set()
        self.thread.join(timeout=6)
