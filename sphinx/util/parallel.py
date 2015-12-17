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
except ImportError:
    multiprocessing = None

from math import sqrt

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
        # main task performed by each task, returning result
        self._task_func = 0
        # (optional) function performed by each task on the result of main task
        self._result_func = 0
        # task arguments
        self._args = {}
        # list of subprocesses (both started and waiting)
        self._procs = {}
        # list of receiving pipe connections of running subprocesses
        self._precvs = {}
        # list of receiving pipe connections of waiting subprocesses
        self._precvsWaiting = {}
        # number of working subprocesses
        self._pworking = 0
        # task number of each subprocess
        self._taskid = 0

    def _process(self, pipe, func, arg):
        try:
            if arg is None:
                ret = func()
            else:
                ret = func(arg)
            pipe.send((False, ret))
        except BaseException as err:
            pipe.send((True, (err, traceback.format_exc())))

    def _result_func_wrapper(self, arg, result):
        result_func = self._result_func(arg, result)
        if result_func:
            result_func(result)

    def add_task(self, task_func, arg=None, result_func=None):
        self._task_func = task_func  # dummy code after first call
        self._result_func = result_func or (lambda *x: None)  # dummy code after first call
        tid = self._taskid
        self._taskid += 1
        self._args[tid] = arg
        precv, psend = multiprocessing.Pipe(False)
        proc = multiprocessing.Process(target=self._process,
                                       args=(psend, self._task_func, arg))
        self._procs[tid] = proc
        if self._pworking < self.nproc:
            self._precvs[tid] = precv
            self._pworking += 1
            proc.start()
        else:
            self._precvsWaiting[tid] = precv

    def join(self):
        while self._pworking:
            for tid, pipe in self._precvs.items():
                if pipe.poll():
                    exc, result = pipe.recv()
                    if exc:
                        raise SphinxParallelError(*result)
                    self._result_func_wrapper(self._args[tid], result)
                    self._procs[tid].join()
                    if len(self._precvsWaiting) > 0:
                        newtid, newprecv = self._precvsWaiting.popitem()
                        self._precvs[newtid] = newprecv
                        self._procs[newtid].start()
                        break
                    else:
                        self._pworking -= 1


def make_chunks(arguments, nproc, maxbatch=10):
    # determine how many documents to read in one go
    nargs = len(arguments)
    chunksize = min(nargs // nproc, maxbatch)
    if chunksize == 0:
        chunksize = 1
    if chunksize == maxbatch:
        # try to improve batch size vs. number of batches
        chunksize = int(sqrt(nargs/nproc * maxbatch))
    nchunks, rest = divmod(nargs, chunksize)
    if rest:
        nchunks += 1
    # partition documents in "chunks" that will be written by one Process
    return [arguments[i*chunksize:(i+1)*chunksize] for i in range(nchunks)]
