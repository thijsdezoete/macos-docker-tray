from AppKit import NSObject, NSApplication, NSVariableStatusItemLength, NSImage, NSMenu, NSTimer, NSDate, NSRunLoop, NSDefaultRunLoopMode, NSStatusBar, NSMenuItem, NSToolbarSeparatorItemIdentifier, NSOnState, NSOffState
from PyObjCTools import AppHelper
import signal
import subprocess
import sys, os
import json
import syslog
from pprint import pprint

start_time = NSDate.date()

class MyTray(NSObject):
    statusbar = None
    state = 'setup'
    interval = 3.0
    loop_func = "instances_"
    which_terminal = "Terminal"
    kill = False
    toggles = ['kill', 'refresh']
    toggle_images = {}
    curr_config = {}

    # Init
    def applicationDidFinishLaunching_(self, _n):
        self.statusbar = NSStatusBar.systemStatusBar()

        self.statusitem = self.statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.image = NSImage.alloc().initByReferencingFile_("mydock.icns")
        for i in self.toggles:
            self.toggle_images[i] = NSImage.alloc().initByReferencingFile_(i+".png")

        #self.statusitem.setTitle_(u"Set up %s" % NAME)
        self.statusitem.setImage_(self.image)
        self.statusitem.setHighlightMode_(1)
        self.statusitem.setToolTip_("Docker tray tool")


        self.menu = NSMenu.alloc().init()

        # menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Kill', 'killornot:', '')
        # menuitem.setState_(NSOnState if not self.kill else NSOffState)
        # self.menu.addItem_(menuitem)

        # menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Docker instances', 'instances:', '')
        # self.menu.addItem_(menuitem)
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        self.menu.addItem_(menuitem)

        self.statusitem.setMenu_(self.menu)

        # Get config if there is any
        self.restore_config()

        #print("interval: %s" % self.interval)
        self.timer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(start_time, self.interval, self, 'loop:', None, True)
        getattr(self, self.loop_func)("Bs?")
        

    def restore_config(self):
        cfg = self._get_config()
        if not cfg:
            return

        print("Restored from config:")
        print(cfg)
        self.kill = cfg['kill']
        self.which_terminal = cfg['terminal']

    def _get_config(self):
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            with open(dir_path + '/config.json') as cfg:
                old_config = json.loads(cfg.read())
                return old_config
        except Exception as e:
            pass # print(e)
        return False

    def loadSavedState(self):
        self.curr_config = {}

    def saveState(self):
        self.curr_config['kill'] = self.kill
        self.curr_config['terminal'] = self.which_terminal
        dir_path = os.path.dirname(os.path.realpath(__file__))

        try:
            with open(dir_path + '/config.json', 'w') as cfg:
                cfg.write(json.dumps(self.curr_config))
        except Exception as e:
            print("Cannot write")
            print(e)
            return False

    def buildMenu(self):
        pass

    def itermtoggle_(self, _n):
        self.which_terminal = 'iTerm' if self.which_terminal != 'iTerm' else 'Terminal'
        self.saveState()
        _n.setState_(NSOffState if not self.which_terminal == 'iTerm' else NSOnState)

    def killornot_(self, _n):
        self.kill = not self.kill
        self.saveState()
        _n.setState_(NSOffState if self.kill else NSOnState)

    def instances_(self, _n):
        self.loop_func = sys._getframe(0).f_code.co_name
        try:
            x = subprocess.check_output(["/usr/local/bin/docker", "ps", "--format", "{{.Names}}"])
        except subprocess.CalledProcessError as e:
            #print(e)
            self.statusitem.setImage_(self.image)
            # Keep looping, but don't do anything
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
            return

        containers = x.splitlines()

        self.statusitem.setTitle_(str(len(containers)))

        new_menu = NSMenu.alloc().init()
        shellmenu = NSMenu.alloc().init()
        logmenu = NSMenu.alloc().init()

        i = NSMenuItem.alloc().init()
        i.setTitle_("Shell")
        i.setSubmenu_(shellmenu)
        new_menu.addItem_(i)

        i = NSMenuItem.alloc().init()
        i.setTitle_("Logs")
        i.setSubmenu_(logmenu)
        new_menu.addItem_(i)

        new_menu.addItem_(NSMenuItem.separatorItem())

        for container in containers:
            shellmenuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(container, 'shellinto:', '')
            shellmenu.addItem_(shellmenuitem)
            logmenuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(container, 'loginto:', '')
            logmenu.addItem_(logmenuitem)
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(container, 'killinstance:', '')
            menuitem.setImage_(self.toggle_images['kill' if self.kill else 'refresh'])
            # pprint(dir(menuitem))
            new_menu.addItem_(menuitem)

        new_menu.addItem_(NSMenuItem.separatorItem())

        i = NSMenuItem.alloc().init()
        configmenu = NSMenu.alloc().init()
        i.setTitle_("Settings")
        i.setSubmenu_(configmenu)
        new_menu.addItem_(i)


        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Kill', 'killornot:', '')
        menuitem.setState_(NSOnState if self.kill else NSOffState)
        configmenu.addItem_(menuitem)
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Restart', 'killornot:', '')
        menuitem.setState_(NSOnState if not self.kill else NSOffState)
        configmenu.addItem_(menuitem)
        configmenu.addItem_(NSMenuItem.separatorItem())
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('iTerm', 'itermtoggle:', '')
        menuitem.setState_(NSOnState if self.which_terminal == 'iTerm' else NSOffState)
        configmenu.addItem_(menuitem)
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Terminal', 'itermtoggle:', '')
        menuitem.setState_(NSOnState if not self.which_terminal == 'iTerm' else NSOffState)
        configmenu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        new_menu.addItem_(menuitem)

        self.menu = new_menu
        self.statusitem.setMenu_(self.menu)

        if self.state == 'setup':
            self.state = 'running'
        if self.state == 'running':
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)


    def loginto_(self, sender):
        instance_name = sender.SCTExtractTitle()
        get_container_id = cmd = ["/usr/local/bin/docker", "ps", "-aqf", 'name=' + str(instance_name) ]
        container_id = subprocess.check_output(get_container_id).strip()
        iterm_script =  """
set docker_id to "{container_id}"
tell application "iTerm"
	set newwindow to (create window with default profile)
	tell current session of newwindow
		write text "docker logs -f \" & docker_id & \""
	end tell
end tell"""
        terminal_script = """
set docker_id to "{container_id}"
tell application "Terminal"
	do script "docker logs -f \" & docker_id & \""
	activate
end tell"""
        cmd = iterm_script if self.which_terminal == "iTerm" else terminal_script

        cmd = cmd.format(
            container_id=container_id,
            #term_app="iTerm" if self.which_terminal == "iTerm"  else "Terminal",
        )
        from subprocess import PIPE
        p = subprocess.Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)# cmd, shell=True)
        stdout, stderr = p.communicate(cmd)
        p.terminate()

    def shellinto_(self, sender):
        instance_name = sender.SCTExtractTitle()
        get_container_id = cmd = ["/usr/local/bin/docker", "ps", "-aqf", 'name=' + str(instance_name) ]
        container_id = subprocess.check_output(get_container_id).strip()
        iterm_script =  """
set docker_id to "{container_id}"
tell application "iTerm"
	set newwindow to (create window with default profile)
	tell current session of newwindow
		write text "docker exec -it \" & docker_id & \" sh  "
	end tell
end tell"""
        terminal_script = """
set docker_id to "{container_id}"
tell application "Terminal"
	do script "docker exec -it \" & docker_id & \" sh  "
	activate
end tell"""
        cmd = iterm_script if self.which_terminal == "iTerm" else terminal_script

        cmd = cmd.format(
            container_id=container_id,
            #term_app="iTerm" if self.which_terminal == "iTerm"  else "Terminal",
        )
        from subprocess import PIPE
        p = subprocess.Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)# cmd, shell=True)
        stdout, stderr = p.communicate(cmd)
        p.terminate()

    def killinstance_(self, sender):
        #print(("Kill" if self.kill else "Restart") + " instance! %s" % sender)
        instance_name = sender.SCTExtractTitle()
        try:
            x = subprocess.check_output(["/usr/local/bin/docker", "kill" if self.kill else "restart", instance_name])
        except subprocess.CalledProcessError as e:
            print(e)

    def loop_(self, _n):
        getattr(self, self.loop_func)(_n)


def sigint_handler(signal, frame):
    print("\nSIGINT received. Quitting...")
    try:
        # Try to save the state
        print("Saving state...")
        d.saveState()
    except Exception as e:
        print("Failed to save state...")
        print(e)
        pass
    AppHelper.stopEventLoop()


if __name__=='__main__':
    syslog.openlog("Dockertray")
    syslog.syslog(syslog.LOG_INFO, "Starting app")
    app = NSApplication.sharedApplication()
    signal.signal(signal.SIGINT, sigint_handler)
    d = MyTray.alloc().init()
    app.setDelegate_(d)

    AppHelper.runEventLoop()
