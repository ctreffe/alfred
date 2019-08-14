import alfred.settings as settings
import webbrowser
from alfred.helpmates import socket_checker

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
    webbrowser.open('http://127.0.0.1:{port}/start'.format(port=port), new=2)
    sys.stderr.writelines([" * Start local experiment using http://127.0.0.1:%d/start\n" % port])
    ls.app.run(port=port, threaded=True)
else:
    RuntimeError("Unexpected value of experiment type")
