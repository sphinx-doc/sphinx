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


class ParallelProcess(object):

    def __init__(self, process_func, result_func, nproc, maxbatch=10):
        self.process_func = process_func
        self.result_func = result_func
        self.nproc = nproc
        self.maxbatch = maxbatch
        # list of threads to join when waiting for completion
        self._threads = []
        self._chunks = []
        self.nchunks = 0
        # queue of result objects to process
        self.result_queue = queue.Queue()
        self._nprocessed = 0

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

    def spawn(self):
        assert self._chunks

        def process(pipe, chunk):
            try:
                ret = self.process_func(chunk)
                pipe.send((False, ret))
            except BaseException as err:
                pipe.send((True, (err, traceback.format_exc())))

        def process_thread(chunk):
            precv, psend = multiprocessing.Pipe(False)
            proc = multiprocessing.Process(target=process, args=(psend, chunk))
            proc.start()
            result = precv.recv()
            self.result_queue.put((chunk,) + result)
            proc.join()
            semaphore.release()

        # allow only "nproc" worker processes at once
        semaphore = threading.Semaphore(self.nproc)

        for chunk in self._chunks:
            yield chunk
            semaphore.acquire()
            t = threading.Thread(target=process_thread, args=(chunk,))
            t.setDaemon(True)
            t.start()
            self._threads.append(t)
            # try processing results already in parallel
            try:
                chunk, exc, result = self.result_queue.get(False)
            except queue.Empty:
                pass
            else:
                if exc:
                    raise SphinxParallelError(*result)
                self.result_func(chunk, result)
                self._nprocessed += 1

    def join(self):
        while self._nprocessed < self.nchunks:
            chunk, exc, result = self.result_queue.get()
            if exc:
                raise SphinxParallelError(*result)
            self.result_func(chunk, result)
            self._nprocessed += 1

        for t in self._threads:
            t.join()
