# -*- coding: utf-8 -*-
"""
    sphinx.util.parallel
    ~~~~~~~~~~~~~~~~~~~~

    Parallel building utilities.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import traceback

try:
    import multiprocessing
    import threading
except ImportError:
    multiprocessing = threading = None

from six.moves import queue

from sphinx.errors import SphinxParallelError

# our parallel functionality only works for the forking Process
parallel_available = multiprocessing and (os.name == 'posix')


class SerialTasks(object):
    """Has the same interface as ParallelTasks, but executes tasks directly."""

    def __init__(self, nproc=1):
        pass

    def add_task(self, task_func, arg=None, result_func=None):
        if arg is not None:
            res = task_func(arg)
        else:
            res = task_func()
        if result_func:
            result_func(res)

    def join(self):
        pass


class ParallelTasks(object):
    """Executes *nproc* tasks in parallel after forking."""

    def __init__(self, nproc):
        self.nproc = nproc
        # list of threads to join when waiting for completion
        self._taskid = 0
        self._threads = {}
        self._nthreads = 0
        # queue of result objects to process
        self.result_queue = queue.Queue()
        self._nprocessed = 0
        # maps tasks to result functions
        self._result_funcs = {}
        # allow only "nproc" worker processes at once
        self._semaphore = threading.Semaphore(self.nproc)

    def _process(self, pipe, func, arg):
        try:
            if arg is None:
                ret = func()
            else:
                ret = func(arg)
            pipe.send((False, ret))
        except BaseException as err:
            pipe.send((True, (err, traceback.format_exc())))

    def _process_thread(self, tid, func, arg):
        precv, psend = multiprocessing.Pipe(False)
        proc = multiprocessing.Process(target=self._process,
                                       args=(psend, func, arg))
        proc.start()
        result = precv.recv()
        self.result_queue.put((tid, arg) + result)
        proc.join()
        self._semaphore.release()

    def add_task(self, task_func, arg=None, result_func=None):
        tid = self._taskid
        self._taskid += 1
        self._semaphore.acquire()
        thread = threading.Thread(target=self._process_thread,
                                  args=(tid, task_func, arg))
        thread.setDaemon(True)
        thread.start()
        self._nthreads += 1
        self._threads[tid] = thread
        self._result_funcs[tid] = result_func or (lambda *x: None)
        # try processing results already in parallel
        try:
            tid, arg, exc, result = self.result_queue.get(False)
        except queue.Empty:
            pass
        else:
            del self._threads[tid]
            if exc:
                raise SphinxParallelError(*result)
            result_func = self._result_funcs.pop(tid)(arg, result)
            if result_func:
                result_func(result)
            self._nprocessed += 1

    def join(self):
        while self._nprocessed < self._nthreads:
            tid, arg, exc, result = self.result_queue.get()
            del self._threads[tid]
            if exc:
                raise SphinxParallelError(*result)
            result_func = self._result_funcs.pop(tid)(arg, result)
            if result_func:
                result_func(result)
            self._nprocessed += 1

        # there shouldn't be any threads left...
        for t in self._threads.values():
            t.join()


def make_chunks(arguments, nproc, maxbatch=10):
    # determine how many documents to read in one go
    nargs = len(arguments)
    chunksize = min(nargs // nproc, maxbatch)
    if chunksize == 0:
        chunksize = 1
    nchunks, rest = divmod(nargs, chunksize)
    if rest:
        nchunks += 1
    # partition documents in "chunks" that will be written by one Process
    return [arguments[i*chunksize:(i+1)*chunksize] for i in range(nchunks)]
