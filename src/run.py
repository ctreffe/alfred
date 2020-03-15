# -*- coding: utf-8 -*-

# --- THIS FILE SHOULD NOT BE CHANGED --- #

from alfred.helpmates import socket_checker
import alfred.settings as settings
import script
import webbrowser
from alfred.alfredlog import init_logging
init_logging('alfred')

if settings.experiment.type == "qt-wk":
    from alfred.helpmates.localserver import Generator 
    generator = Generator()
    generator.set_generator(script.generate_experiment)
    exp = generator.generate_experiment(config=None)
    exp.start()
    
elif settings.experiment.type == "web":
    import sys
    import alfred.helpmates.localserver as ls

    ls.script.set_generator(script.generate_experiment)
    
    port = 5000
    while not socket_checker(port):
            port += 1
    #if open:
    webbrowser.open('http://127.0.0.1:{port}/start'.format(port=port))
    sys.stderr.writelines([" * Start local experiment using http://127.0.0.1:%d/start\n" % port])
    ls.app.run(port=port, threaded=True)
else:
    RuntimeError("Unexpected value of experiment type")