# coding: utf-8

import cherrypy
import sys, os, socket
import ConfigParser
import subprocess
import qrcode
import logging
from cherrypy.lib.static import serve_file
from StringIO import StringIO
from stat import S_ISREG, ST_MTIME, ST_MODE
from time import gmtime, strftime, sleep

# create logger
logger = logging.getLogger('cherrypy')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("/tmp/app.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

sys.path.append(".")
try:
    from aliyun import Aliyun
    aliyunInst = Aliyun(logger)
except:
    from local import Local
    aliyunInst = Local(logger)

_hostname = '0.0.0.0'
_port = 80
if 'justin-laptop' == socket.gethostname():
    _port = 4080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# try:
#     s.bind((_hostname, _port))
# except socket.error as e:
#     sleep(10)

server_config = {
    'server.socket_host': _hostname,
    'server.socket_port': _port,
    'response.timeout': 10*60
}
cherrypy.config.update(server_config)

def error_page_404(status, message, traceback, version):
    return "Oops! Looks like you're lost"
cherrypy.config.update({'error_page.404': error_page_404})

def jsonify_tool_callback(*args, **kwargs):
    response = cherrypy.response
    response.headers['Content-Type'] = 'application/json'
cherrypy.tools.jsonify = cherrypy.Tool('before_finalize', jsonify_tool_callback, priority=30)


class App(object):
    PROJECT_PATH = "projects/"
    VIDEO_PATH = "videos/"
    SHARE_PATH = "share/"
    FILE_TEMPLATE = "%s/%s"

    @cherrypy.expose
    def index(self, **args):
        url = cherrypy.url()
        if 'scratch.svachina.com' in url:
            return self.ide(**args)
        else:
            return file('scratch/tutorial.html')

    @cherrypy.expose
    def ide(self, **args):
        uid = args.get('userid') if 'userid' in args else 'Guest'
        uname = args.get('username') if 'username' in args else 'Guest'
        logger.debug(uid + "  " + uname)
        content = "".join(file('scratch/Scratch.html').readlines())
        content = content.replace('__USERID__', uid)
        content = content.replace('__USERNAME__', uname)
        try:
            content = content.replace('__SUBSCRIBE_INFO__', aliyunInst.get_url('static/wechat_official_account.jpg', True))
            content = content.replace('__CDN_URL__', aliyunInst.get_cdn_url())
        except:
            pass
        return StringIO(unicode(content))

    @cherrypy.expose
    def tutorial(self, **args):
        return file('scratch/tutorial.html')

    @cherrypy.expose
    def save(self, **args):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        user = self.encode(args.get('user'))
        filename = self.encode(args.get('filename'))
        filename = filename.replace(' ', '_')
        _type = args.get('type') if 'type' in args else 'project'

        if _type == 'video':
            template = App.VIDEO_PATH + App.FILE_TEMPLATE
            dest = template % (user, file)
            url = aliyunInst.upload_convert_get_link(user, filename, rawbody)
            if url:
                self.generate_qrcode(url, filename +'.png')
                return file(filename +'.png')
            else:
                return self.error('converting video failed')

        elif _type == 'project':

            template = App.PROJECT_PATH + App.FILE_TEMPLATE
            dest = template % (user, filename)
            status = aliyunInst.upload_bytes(dest, rawbody)

            logger.debug("uploading project to %s and return code %s." % (dest, str(status)))

        return True

    def generate_qrcode(self, url, img_name):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data('http://scratch.svachina.com/share?video=' + url)
        # qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        img.save(img_name)

    @cherrypy.expose
    def share(self, **args):
        # todo fix the issue, not full url
        video = args.get('video')
        if not video: return ''

        url = aliyunInst.get_url(video)
        if url:
            return '<html><head><meta name="viewport" content="width=device-width"></head><body><video controls="true" autoplay="true" name="media"><source src="' + url +'" type="video/mp4"></video></body></html>'
        else:
            return 'Oops! Cannot find the video to play'

    @cherrypy.expose
    def load(self, **args):
        user = self.encode(args.get('user'))
        _type = args.get('type')
        logger.debug("%s %s" % (user, _type))

        if _type == 'project':
            project = args.get('project')
            if not project: return self.error('project name is necessary')
            if (not project.endswith('.sb2')):
                project += '.sb2'

            for _u in [user, 'demo', 'default']:
                project_file = App.PROJECT_PATH + App.FILE_TEMPLATE % (_u, project)
                logger.debug(project_file)

                if aliyunInst.is_object_exist(project_file):
                    return aliyunInst.get_url(project_file)
                
            return self.error('project %s is not exist, please try others' % (project))

        elif _type == 'listproject':
            path = App.PROJECT_PATH + App.FILE_TEMPLATE % (user, '')
            entries = aliyunInst.list_files(path, 'sb2')
            plist = map(lambda (ts, path): "|".join((os.path.basename(path)[:-len(".sb2")], strftime("%Y-%m-%d %H:%M:%S", gmtime(ts)))), sorted(entries))

            plistStr = ','.join(plist)
            logger.debug(plistStr)
            return plistStr

        elif _type == 'removeproject':
            project = args.get('project')
            if not user or user in ['', '/', '.', '..', '*', 'demo', 'guest', 'default']:
                return self.error('invalid user name: ' + user)
            if not project: return self.error('project name is necessary')

            if not project.endswith('.sb2'):
                project += '.sb2'

            project_file = App.PROJECT_PATH + App.FILE_TEMPLATE % (user, project)
            if aliyunInst.is_object_exist(project_file):
                aliyunInst.remove_object(project_file)
            
            return True

        elif _type == 'subscribe':
            return aliyunInst.get_url('static/wechat_official_account.jpg', True)
        else:
            return self.error('correct type is necessary')

    def error(self, message):
        return self.message('ERROR', message)

    def message(self, code, message):
        return "[%s]: %s" % (code, message)
    
    def encode(self, _str, charset='uft-8'):
        try:
            return "{}".format(_str.encode('utf-8'))
        except:
            return _str


if __name__ == '__main__':
    working_directory = os.getcwd()    
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(working_directory)
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        },
        '/scratch': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'scratch'
        },
        '/projects': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'projects'
        },
        '/crossdomain.xml': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': working_directory + '/crossdomain.xml'
        }
    }
    

    webapp = App()
    webapp.config = ConfigParser.ConfigParser()
    webapp.config.read('./app.cnf')
    try:
        import daemon
        with daemon.DaemonContext(files_preserve = [fh.stream],working_directory=working_directory):
            cherrypy.quickstart(webapp, '/', conf)
    except:
        cherrypy.quickstart(webapp, '/', conf)
