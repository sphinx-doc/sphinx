# -*- coding: utf-8 -*-
"""
    sphinx.util.parallel
    ~~~~~~~~~~~~~~~~~~~~

    Parallel building utilities.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
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
        self._threads = []
        self._nthreads = 0
        # queue of result objects to process
        self.result_queue = queue.Queue()
        self._nprocessed = 0
        # maps tasks to result functions
        self._result_funcs = {}
        # allow only "nproc" worker processes at once
        self._semaphore = threading.Semaphore(self.nproc)

    def _process_thread(self, tid, func, arg):
        def process(pipe, arg):
            try:
                if arg is None:
                    ret = func()
                else:
                    ret = func(arg)
                pipe.send((False, ret))
            except BaseException as err:
                pipe.send((True, (err, traceback.format_exc())))

        precv, psend = multiprocessing.Pipe(False)
        proc = multiprocessing.Process(target=process, args=(psend, arg))
        proc.start()
        result = precv.recv()
        self.result_queue.put((tid, arg) + result)
        proc.join()
        self._semaphore.release()

    def add_task(self, task_func, arg=None, result_func=None):
        tid = len(self._threads)
        self._semaphore.acquire()
        t = threading.Thread(target=self._process_thread,
                             args=(tid, task_func, arg))
        t.setDaemon(True)
        t.start()
        self._nthreads += 1
        self._threads.append(t)
        self._result_funcs[tid] = result_func or (lambda *x: None)
        # try processing results already in parallel
        try:
            tid, arg, exc, result = self.result_queue.get(False)
        except queue.Empty:
            pass
        else:
            if exc:
                raise SphinxParallelError(*result)
            self._result_funcs.pop(tid)(arg, result)
            self._nprocessed += 1

    def join(self):
        while self._nprocessed < self._nthreads:
            tid, arg, exc, result = self.result_queue.get()
            if exc:
                raise SphinxParallelError(*result)
            self._result_funcs.pop(tid)(arg, result)
            self._nprocessed += 1

        for t in self._threads:
            t.join()


class ParallelChunked(ParallelTasks):
    """Executes chunks of a list of arguments in parallel."""

    def __init__(self, process_func, result_func, nproc, maxbatch=10):
        ParallelTasks.__init__(self, nproc)
        self.process_func = process_func
        self.result_func = result_func
        self.maxbatch = maxbatch
        self._chunks = []
        self.nchunks = 0

    def set_arguments(self, arguments):
        # determine how many documents to read in one go
        nargs = len(arguments)
        chunksize = min(nargs // self.nproc, self.maxbatch)
        if chunksize == 0:
            chunksize = 1
        nchunks, rest = divmod(nargs, chunksize)
        if rest:
            nchunks += 1
        # partition documents in "chunks" that will be written by one Process
        self._chunks = [arguments[i*chunksize:(i+1)*chunksize] for i in range(nchunks)]
        self.nchunks = len(self._chunks)

    def iter_chunks(self):
        assert self._chunks
        for chunk in self._chunks:
            yield chunk
            self.add_task(self.process_func, chunk, self.result_func)
