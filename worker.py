#!/bin/env python3

import sys
import multiprocessing
from enum import Enum

# Enum

class ExceptionHandling(Enum):
    IGNORE = "IGNORE"
    THROW = "THROW"

# Utility Class

class Worker(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, exception_handling=ExceptionHandling.IGNORE):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.exception_handling = exception_handling
    def run(self):
        while True:
            try:
                next_task = self.task_queue.get()
                if not next_task:
#                    print("%s Poisoned" % multiprocessing.current_process().name, file=sys.stderr)
                    self.task_queue.task_done()
                    break
                try:
                    result = next_task()
                    self.result_queue.put(result)
                except Exception as e:
                    if self.exception_handling == ExceptionHandling.IGNORE:
#                        print("%s Exception: %s" % (multiprocessing.current_process().name, e), file=sys.stderr)
#                        print("%s IGNORE error" % multiprocessing.current_process().name, file=sys.stderr)
                        pass
                    elif self.exception_handling == ExceptionHandling.THROW:  # Caution
                        self.task_queue.task_done()
                        raise e
                    else:  # Special Token
                        self.result_queue.put(self.exception_handling)
                self.task_queue.task_done()
            except Exception as e:
                raise e
                pass

class WorkerPool:
    def __init__(self, n, exception_handling=ExceptionHandling.IGNORE):
        self.n = n
        self.task_queue = multiprocessing.JoinableQueue()
        self.result_queue = multiprocessing.Queue()
        self.workers = [ Worker(self.task_queue, self.result_queue) for i in range(0, n) ]
        self.started = False
    def start(self):
        if not self.started:
            for w in self.workers:
                w.start()
            self.started = True
    def terminate(self, timeout=None):
        while not self.task_queue.empty():
            self.task_queue.get()
        for i in range(0, self.n):
            self.task_queue.put(None)
        if not timeout:
            for w in self.workers:
                w.join()
        else:
            for w in self.workers:
                w.join(timeout)
            for w in self.workers:
                w.terminate()
                w.join()
    def health_check(self):
        return sum((1 if w.is_alive else 0 for w in self.workers))
    def put(self, task):
        self.task_queue.put(task)
        if not self.started:
            self.start()
    def get(self, timeout=None):
        return self.result_queue.get(timeout=timeout)

# Example Task

class Task(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __call__(self):
        pass  # Do some work here
        return self.a * self.b
    def __str__(self):
        return ""

