import alfred.settings as settings
import socket


def socket_checker(port):
    try:
        s = socket.socket()
        s.bind(('127.0.0.1', port))
        s.listen(1)
        s.close()
        return(True)
    except Exception:
        s.close()
        return(False)


if settings.experiment.type == 'qt-wk':
    import script
    exp = script.generate_experiment()
    exp.start()
elif settings.experiment.type == 'web':
    import sys
    import alfred.helpmates.localserver as ls
    import script
    ls.set_generator(script)
    port = 5000
    while not socket_checker(port):
        port += 1
    sys.stderr.writelines([" * Start local experiment using http://127.0.0.1:%d/start\n" % port])
    ls.app.run(port=port, threaded=True)
else:
    RuntimeError("Unexpected value of experiment type")
