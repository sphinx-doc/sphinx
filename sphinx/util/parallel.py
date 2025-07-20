"""Parallel building utilities."""

from __future__ import annotations

import os
import queue
import time
import traceback
from typing import TYPE_CHECKING

try:
    import multiprocessing

    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False

from sphinx.errors import SphinxParallelError
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from logging import LogRecord
    from typing import Any

    InQueueArg = tuple[int, Callable[..., Any], Any]
    OutQueueArg = tuple[int, tuple[bool, list[LogRecord], Any]]

logger = logging.getLogger(__name__)

# our parallel functionality only works for the forking Process
parallel_available = HAS_MULTIPROCESSING and os.name == 'posix'


class SerialTasks:
    """Has the same interface as ParallelTasks, but executes tasks directly."""

    def __init__(self, nproc: int = 1) -> None:
        pass

    def add_task(
        self,
        task_func: Callable[[Any], Any] | Callable[[], Any],
        arg: Any = None,
        result_func: Callable[[Any], Any] | None = None,
    ) -> None:
        if arg is not None:
            res = task_func(arg)  # type: ignore[call-arg]
        else:
            res = task_func()  # type: ignore[call-arg]
        if result_func:
            result_func(res)

    def start(self) -> None:
        pass

    def join(self) -> None:
        pass


class ParallelTasks:
    """Executes *nproc* tasks in parallel after forking."""

    def __init__(self, nproc: int) -> None:
        self.nproc = nproc
        # (optional) function performed by each task on the result of main task
        self._result_funcs: dict[int, Callable[[Any, Any], Any]] = {}
        # task arguments
        self._args: dict[int, list[Any] | None] = {}
        # list of subprocesses (both started and waiting)
        self._procs: dict[int, Any] = {}
        # list of receiving pipe connections of running subprocesses
        self._precvs: dict[int, Any] = {}
        # list of receiving pipe connections of waiting subprocesses
        self._precvs_waiting: dict[int, Any] = {}
        # number of working subprocesses
        self._pworking = 0
        # task number of each subprocess
        self._taskid = 0
        self._args_queue: multiprocessing.Queue[Any] = multiprocessing.Queue()
        self._result_queue: multiprocessing.Queue[Any] = multiprocessing.Queue()

    def add_task(
        self,
        task_func: Callable[[Any], Any] | Callable[[], Any],
        arg: Any = None,
        result_func: Callable[[Any, Any], Any] | None = None,
    ) -> None:
        tid = self._taskid
        self._taskid += 1
        self._result_funcs[tid] = result_func or (lambda arg, result: None)
        self._args[tid] = arg
        self._args_queue.put((tid, task_func, arg))

    def start(self) -> None:
        # start the worker processes
        for i in range(self._pworking, self.nproc + self._pworking):
            proc = multiprocessing.Process(
                target=process_data_chunks,
                args=(self._args_queue, self._result_queue),
                name=f'SphinxParallelWorker-{i}',
            )
            self._procs[i] = proc
            self._pworking += 1
            proc.start()

    def join(self) -> None:
        try:
            while self._pworking:
                while not self._result_queue.empty():
                    tid, result = self._result_queue.get_nowait()
                    if tid in self._result_funcs:
                        exc, logs, res = result
                        if exc:
                            raise SphinxParallelError(*res)
                        for log in logs:
                            logger.handle(log)
                        self._result_funcs[tid](self._args.pop(tid), res)
                    else:
                        raise SphinxParallelError(
                            message=f'Result function for task {tid} not found. '
                                    f'This is a bug in Sphinx.',
                            traceback='',
                        )
                for num, proc in list(self._procs.items()):
                    if not proc.is_alive():
                        self._procs.pop(num)
                        self._pworking -= 1
            if self._pworking:
                time.sleep(0.02)
        finally:
            # shutdown other child processes on failure
            self.terminate()

    def terminate(self) -> None:
        for tid in list(self._procs):
            self._procs[tid].terminate()
            self._result_funcs.pop(tid)
            self._procs.pop(tid)
            self._pworking -= 1

        # clear queues to avoid memory leaks
        while not self._args_queue.empty():
            try:
                self._args_queue.get_nowait()
            except queue.Empty:
                break

        # clear result queue to avoid memory leaks
        while not self._result_queue.empty():
            try:
                self._result_queue.get_nowait()
            except queue.Empty:
                break


def make_chunks(arguments: Sequence[str], nproc: int, maxbatch: int = 10) -> list[Any]:
    # determine how many documents to read in one go
    nargs = len(arguments)
    chunksize = nargs // nproc
    chunksize = max(min(chunksize, maxbatch), 1)
    nchunks, rest = divmod(nargs, chunksize)
    if rest:
        nchunks += 1
    # partition documents in "chunks" that will be written by one Process
    return [arguments[i * chunksize : (i + 1) * chunksize] for i in range(nchunks)]


def process_data_chunks(
        queue_in: multiprocessing.Queue[InQueueArg],
        queue_out: multiprocessing.Queue[OutQueueArg]
) -> None:
    """Process data chunks from the queue using the given function."""
    while True:
        try:
            task_id, func, arg = queue_in.get_nowait()
        except queue.Empty:
            break
        collector = logging.LogCollector()
        try:
            with collector.collect():
                if arg is not None:
                    result = func(arg)
                else:
                    result = func()
            failed = False
        except BaseException as err:
            failed = True
            errmsg = traceback.format_exception_only(err.__class__, err)[0].strip()
            result = (errmsg, traceback.format_exc())
        logging.convert_serializable(collector.logs)
        queue_out.put((task_id, (failed, collector.logs, result)))
