
import os
import subprocess as sp

from .utils import MachopLogger, iscallable, ensure_list
from .async import MachopAsyncCommand
from .watch import MachopWatchCommand
from .strings import invalid_command


_log = MachopLogger('api')


def _leer(*args, **kwargs):
    _log.out("no default command has been set!")


def machop_init(*args, **kwargs):
    _log.out("this will initialize a karatechop.py file in cwd")


CURRENT_DIRECTORY = os.getcwd()
__join_list__ = []
__move_list__ = {'focus-energy': _leer, 'init': machop_init}


def _get_callables(cmdlist):
    commands = []
    for cmd in cmdlist:
        if not iscallable(cmd):
            entry = __move_list__.get(cmd, None)
            if not entry:
                raise KeyError("command %s not found" % cmd)
            commands.extend(_get_callables(ensure_list(entry)))
        else:
            commands.append(cmd)
    return commands


def getlog(source):
    newlog = MachopLogger(origin=source)
    return newlog


def default(defaultcommands):
    command('focus-energy', defaultcommands)


def command(cmdstring, cmdfunction):
    # @@@ TODO: validate command names before adding!
    cmdfunction = ensure_list(cmdfunction)
    __move_list__[cmdstring] = cmdfunction


def run(command, *args, **kwargs):
    if not __move_list__.get(command, None):
        _log.out(invalid_command(command, __move_list__.keys()))
        return
    actions = ensure_list(__move_list__[command])
    cmdpath = None
    # @@@ determine if the action is a callable, or another command to run
    if 'cmdpath' not in kwargs.keys():
        cmdpath = CURRENT_DIRECTORY
    for action in actions:
        if not hasattr(action, '__call__'):
            if not cmdpath:
                run(action, *args, **kwargs)
            else:
                run(action, cmdpath, *args, **kwargs)
            continue
        result = None
        if cmdpath:
            result = action(cmdpath=cmdpath, *args, **kwargs)
            continue
        result = action(*args, **kwargs)
        if result:
            pass
    # @@@ raise exceptions or log for error results?


def async(commands, shell=False):
    """
    commands must be a list of callables or registered commands
    *** if you want async shells use machop.shell([...], async=True)
    """
    commands = _get_callables(ensure_list(commands))
    for cmd in commands:
        cmdproc = MachopAsyncCommand(cmd)
        cmdproc.start()
        __join_list__.append(cmdproc)


def watch(globpatterns, commandchain):
    """
    watch accepts glob-style pattern(s) as a list which are then monitored
    for modifications, at which point commandchain is executed. commandchain
    is a single or list of functions or registered commands.
    """
    globs = ensure_list(globpatterns)
    commands = ensure_list(commandchain)
    commands = _get_callables(commands)
    watchman = MachopWatchCommand(globs, commands, CURRENT_DIRECTORY)
    watchman.start()
    __join_list__.append(watchman)


def shell(command):
    """
    does not support async right now!
    """
    proc = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    exit = proc.returncode
    return (exit, stdout, stderr)


def _wait():
    try:
        while __join_list__:
            strand = __join_list__[0]
            if strand.exitcode is None:
                strand.join(1)
            else:
                strand.cleanup()
                __join_list__.remove(strand)
    except KeyboardInterrupt:
        _log.out("shutting down...")
        for strand in __join_list__:
            strand.shutdown()
            strand.join(2)
            strand.terminate()
