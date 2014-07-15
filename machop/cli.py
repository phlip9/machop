# -*- coding: utf-8 -*-
import sys
import os

from .strings import ascii_machop, ascii_fainted, ascii_choose_you
from .strings import ascii_runaway
from .strings import txt_startup_msg, txt_config_error
from .mplog import MachopLog, MachopLogDaemon
from .api import _set_api_q, run, _command_wait
from .utils import import_config


class MachopCLI(object):
    """ creates and manages the CLI for machop """

    def setup(self, path=None):
        self.karatechop = import_config()
        self.args = sys.argv[1:]
        self.exitstatus = 0
        self.path = path
        if not self.path:
            self.path = os.getcwd()
        elif self.path != os.getcwd():
            raise ValueError("process paths not equal!")
        self.daemon = MachopLogDaemon()
        self.daemon.create_queue()
        _set_api_q(self.daemon.queue)
        self.daemon.start()
        self.log = MachopLog(self.daemon.queue, origin='main')
        if not self.karatechop:
            self.log.out(txt_config_error)
            self.exitstatus = 1
            sys.exit()

    def runcli(self, path=None):
        self.setup(path)
        try:
            if len(self.args) > 0:
                # running specific commands
                # self.log.out("\n" + ascii_machop, noformat=True)
                for command in self.args:
                    # @@@ TODO use argparse to config params to commands
                    run(command, cmdpath=self.path)
                _command_wait()
            else:
                # running default command
                self.log.out(ascii_choose_you, noformat=True)
                self.log.out(ascii_machop, noformat=True)
                self.log.out(txt_startup_msg, noformat=True)
                # @@@ TODO use argparse to config params to commands
                run('focus-energy', cmdpath=self.path)
                _command_wait()
                self.log.out(ascii_runaway, True)
        except Exception:
            self.log.out(ascii_fainted, True)
            import traceback
            self.log.out(traceback.format_exc())
        self.daemon.queue.put_nowait(None)
        self.daemon.join()
        raise SystemExit(self.exitstatus)
