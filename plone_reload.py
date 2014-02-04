import re
from . import requests
import sublime
import sublime_plugin
import threading


def format_error_message(html):
    xpr = re.compile('<strong.*?>(.*?)</strong>', re.DOTALL)
    match = xpr.search(str(html))
    errors = "YOUR CODE SUCKS:\n"
    errors += "----------------\n\n"
    errors += "Reload not possible\n\n"
    if match:
        for error in match.groups()[:2]:
            errors += error + '\n'

    sublime.error_message(errors)
    return


class PloneReload(threading.Thread):
    def __init__(self, domain, port, user, pw):
        self.domain = domain
        self.port = port
        self.user = user
        self.pw = pw
        threading.Thread.__init__(self)

    def run(self):
        url = 'http://{0}:{1}/reload?action=code'.format(self.domain,
                                                         self.port)

        try:
            req = requests.get(url, auth=(self.user, self.pw))
        except requests.exceptions.ConnectionError:
            print('No zope running on {}:{}'.format(self.domain, self.port))

            return

        if req.status_code == 200:

            if b'Code reloaded:' in req._content:
                print('Code reloaded', req.status_code)
            elif b'No code reloaded!' in req._content:
                print('No code reloaded', req.status_code)
            else:
                print('Strange content', req._content)
        elif req.status_code == 401:
            print('Unauthorized', req.status_code)

        elif b'<h2>Site Error</h2>' in req._content:
            print('YOUR CODE SUCKS', req.status_code)
            format_error_message(req._content)
        else:
            print('Error', req.status_code)


class PloneReloadEvent(sublime_plugin.EventListener):

    def on_post_save(self, view):

        if view.settings().get('syntax').lower().find('python') == -1:
            return

        # sublime.status_message does not work

        settings = sublime.load_settings('PloneReload.sublime-settings')

        if not settings.get('enabled', True):
            print("PloneReload is disabled")
            return

        domain = settings.get('domain', None)
        port = settings.get('port', None)
        user = settings.get('user', None)
        pw = settings.get('pw', None)

        if not domain and not port and not user and not pw:
            # set defaults
            settings.set('domain', 'localhost')
            settings.set('port', '8080')
            settings.set('user', 'admin')
            settings.set('pw', 'admin')
            settings.set('enabled', True)
            sublime.save_settings('PloneReload.sublime-settings')

            # Open prefs
            view.window().open_file('../User/PloneReload.sublime-settings')

        thread = PloneReload(
            settings.get('domain'),
            settings.get('port'),
            settings.get('user'),
            settings.get('pw'))
        thread.start()
