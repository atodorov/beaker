
import os
import time
import sys
import signal
import daemon
from daemon import pidfile
from optparse import OptionParser
from datetime import datetime
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from DocXMLRPCServer import XMLRPCDocGenerator
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map as RoutingMap, Rule
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed, BadRequest
import gevent, gevent.pool, gevent.wsgi, gevent.event, gevent.monkey
from bkr.common.helpers import RepeatTimer
from bkr.labcontroller.proxy import Proxy, ProxyHTTP
from bkr.labcontroller.config import get_conf, load_conf
from bkr.labcontroller.utils import add_rotating_file_logger
from bkr.log import add_stderr_logger
import logging
logger = logging.getLogger(__name__)

class XMLRPCDispatcher(SimpleXMLRPCDispatcher, XMLRPCDocGenerator):

    def __init__(self):
        SimpleXMLRPCDispatcher.__init__(self, allow_none=True)
        XMLRPCDocGenerator.__init__(self)

    def _dispatch(self, method, params):
        """ Custom _dispatch so we can log time used to execute method.
        """
        start = datetime.utcnow()
        try:
            result = SimpleXMLRPCDispatcher._dispatch(self, method, params)
        except:
            logger.debug('Time: %s %s %s', datetime.utcnow() - start, str(method), str(params)[0:50])
            raise
        logger.debug('Time: %s %s %s', datetime.utcnow() - start, str(method), str(params)[0:50])
        return result

class WSGIApplication(object):

    def __init__(self, proxy):
        self.proxy = proxy
        self.proxy_http = ProxyHTTP(proxy)
        self.xmlrpc_dispatcher = XMLRPCDispatcher()
        self.xmlrpc_dispatcher.register_instance(proxy)
        self.url_map = RoutingMap([
            # pseudo-XML-RPC calls used in kickstarts:
            # (these permit GET to make it more convenient to trigger them using curl)
            Rule('/nopxe/<fqdn>', endpoint=(self.proxy, 'clear_netboot')),
            Rule('/install_start/<recipe_id>', endpoint=(self.proxy, 'install_start')),
            Rule('/install_done/<recipe_id>/<fqdn>',
                    endpoint=(self.proxy, 'install_done')),
            Rule('/postinstall_done/<recipe_id>',
                    endpoint=(self.proxy, 'postinstall_done')),
            Rule('/postreboot/<recipe_id>', endpoint=(self.proxy, 'postreboot')),
            # harness API:
            Rule('/recipes/<recipe_id>/', methods=['GET'],
                    endpoint=(self.proxy_http, 'get_recipe')),
            Rule('/recipes/<recipe_id>/watchdog', methods=['POST'],
                    endpoint=(self.proxy_http, 'post_watchdog')),
            Rule('/recipes/<recipe_id>/status', methods=['POST'],
                    endpoint=(self.proxy_http, 'post_recipe_status')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/status', methods=['POST'],
                    endpoint=(self.proxy_http, 'post_task_status')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/results/', methods=['POST'],
                    endpoint=(self.proxy_http, 'post_result')),
            Rule('/recipes/<recipe_id>/logs/', methods=['GET'],
                    endpoint=(self.proxy_http, 'list_recipe_logs')),
            Rule('/recipes/<recipe_id>/logs/<path:path>', methods=['GET', 'PUT'],
                    endpoint=(self.proxy_http, 'do_recipe_log')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/logs/', methods=['GET'],
                    endpoint=(self.proxy_http, 'list_task_logs')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/logs/<path:path>',
                    methods=['GET', 'PUT'],
                    endpoint=(self.proxy_http, 'do_task_log')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/results/<result_id>/logs/',
                    methods=['GET'],
                    endpoint=(self.proxy_http, 'list_result_logs')),
            Rule('/recipes/<recipe_id>/tasks/<task_id>/results/<result_id>/logs/<path:path>',
                    methods=['GET', 'PUT'],
                    endpoint=(self.proxy_http, 'do_result_log')),
        ])

    @Request.application
    def __call__(self, req):
        if req.path in ('/', '/RPC2', '/server'):
            if req.method == 'POST':
                # XML-RPC
                if req.content_type != 'text/xml':
                    return BadRequest('XML-RPC requests must be text/xml')
                result = self.xmlrpc_dispatcher._marshaled_dispatch(req.data)
                return Response(response=result, content_type='text/xml')
            elif req.method in ('GET', 'HEAD'):
                # XML-RPC docs
                return Response(
                        response=self.xmlrpc_dispatcher.generate_html_documentation(),
                        content_type='text/html')
            else:
                return MethodNotAllowed()
        try:
            (obj, attr), args = self.url_map.bind_to_environ(req.environ).match()
            if obj is self.proxy:
                # pseudo-XML-RPC
                result = getattr(obj, attr)(**args)
                return Response(response=repr(result), content_type='text/plain')
            else:
                return getattr(obj, attr)(req, **args)
        except HTTPException, e:
            return e

# Temporary hack to disable keepalive in gevent.wsgi.WSGIServer. This should be easier.
class WSGIHandler(gevent.wsgi.WSGIHandler):
    def read_request(self, *args):
        result = super(WSGIHandler, self).read_request(*args)
        self.close_connection = True
        return result

def daemon_shutdown(signum, frame):
    logger.info('Received signal %s, shutting down', signum)
    shutting_down.set()

def main_loop(proxy=None, conf=None, foreground=False):
    """infinite daemon loop"""
    global shutting_down
    shutting_down = gevent.event.Event()
    gevent.monkey.patch_all()

    # define custom signal handlers
    signal.signal(signal.SIGINT, daemon_shutdown)
    signal.signal(signal.SIGTERM, daemon_shutdown)

    # set up logging
    log_level_string = conf["LOG_LEVEL"]
    log_level = getattr(logging, log_level_string.upper(), logging.DEBUG)
    logging.getLogger().setLevel(log_level)
    if foreground:
        add_stderr_logger(logging.getLogger(), log_level=log_level)
    else:
        log_file = conf["LOG_FILE"]
        add_rotating_file_logger(logging.getLogger(), log_file,
                log_level=log_level, format=conf["VERBOSE_LOG_FORMAT"])

    login = RepeatTimer(conf['RENEW_SESSION_INTERVAL'], proxy.hub._login,
        stop_on_exception=False)
    login.daemon = True
    login.start()

    server = gevent.wsgi.WSGIServer(('', 8000), WSGIApplication(proxy),
            handler_class=WSGIHandler, spawn=gevent.pool.Pool())
    server.stop_timeout = None
    server.start()

    try:
        shutting_down.wait()
    finally:
        server.stop()
        login.stop()

def main():
    parser = OptionParser()
    parser.add_option("-c", "--config",
                      help="Full path to config file to use")
    parser.add_option("-f", "--foreground", default=False, action="store_true",
                      help="run in foreground (do not spawn a daemon)")
    parser.add_option("-p", "--pid-file",
                      help="specify a pid file")
    (opts, args) = parser.parse_args()

    if opts.config:
        load_conf(opts.config)
    conf = get_conf()

    pid_file = opts.pid_file
    if pid_file is None:
        pid_file = conf.get("PROXY_PID_FILE", "/var/run/beaker-lab-controller/beaker-proxy.pid")

    try:
        proxy = Proxy(conf=conf)
    except Exception, ex:
        sys.stderr.write("Error initializing Proxy: %s\n" % ex)
        sys.exit(1)

    if opts.foreground:
        main_loop(proxy=proxy, conf=conf, foreground=True)
    else:
        # See BZ#977269
        proxy.close()
        with daemon.DaemonContext(pidfile=pidfile.TimeoutPIDLockFile(
                pid_file, acquire_timeout=0)):
            main_loop(proxy=proxy, conf=conf, foreground=False)

if __name__ == '__main__':
    main()
