import cherrypy
import yaml

class VarstackServer(object):

    def __init__(self, varstack_obj):
        self.varstack_obj = varstack_obj

    @cherrypy.expose
    @cherrypy.tools.response_headers(headers=[('Content-Type', 'application/yaml')])
    def index(self, **variables):
        res = self.varstack_obj.evaluate(variables)
        return yaml.dump(res)



def setup_server(varstack_obj, interface='localhost', port=5050):
    cherrypy.config.update({'server.socket_host': interface,
                            'server.socket_port': port})
    cherrypy.tree.mount(VarstackServer(varstack_obj), "/", {})
    cherrypy.engine.start()


def teardown_server():
    cherrypy.engine.stop()
