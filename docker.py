from AppKit import NSObject, NSApplication, NSVariableStatusItemLength, NSImage, NSMenu, NSTimer, NSDate, NSRunLoop, NSDefaultRunLoopMode, NSStatusBar, NSMenuItem, NSToolbarSeparatorItemIdentifier, NSOnState, NSOffState
from PyObjCTools import AppHelper
import subprocess
import sys

NAME = "Docker"
start_time = NSDate.date()

class MyTray(NSObject):
    statusbar = None
    state = 'setup'
    interval = 3.0
    loop_func = "instances_"
    kill = False

    # Init
    def applicationDidFinishLaunching_(self, _n):
        self.statusbar = NSStatusBar.systemStatusBar()

        self.statusitem = self.statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.image = NSImage.alloc().initByReferencingFile_("mydock.icns")
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

        #print("interval: %s" % self.interval)
        self.timer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(start_time, self.interval, self, 'loop:', None, True)
        getattr(self, self.loop_func)("Bs?")
        
    def buildMenu(self):
        pass

    def killornot_(self, _n):
        self.kill = not self.kill
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
        submenu = NSMenu.alloc().init()

        i = NSMenuItem.alloc().init()
        i.setTitle_("Shell")
        i.setSubmenu_(submenu)
        new_menu.addItem_(i)

        for container in containers:
            shellmenuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(container, 'shellinto:', '')
            submenu.addItem_(shellmenuitem)
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(container, 'killinstance:', '')
            new_menu.addItem_(menuitem)

        new_menu.addItem_(NSMenuItem.separatorItem())

        i = NSMenuItem.alloc().init()
        configmenu = NSMenu.alloc().init()
        i.setTitle_("Behaviour")
        i.setSubmenu_(configmenu)
        new_menu.addItem_(i)


        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Kill', 'killornot:', '')
        menuitem.setState_(NSOnState if self.kill else NSOffState)
        configmenu.addItem_(menuitem)
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Restart', 'killornot:', '')
        menuitem.setState_(NSOnState if not self.kill else NSOffState)
        configmenu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        new_menu.addItem_(menuitem)

        self.menu = new_menu
        self.statusitem.setMenu_(self.menu)

        if self.state == 'setup':
            self.state = 'running'
        if self.state == 'running':
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)


    def shellinto_(self, sender):
        instance_name = sender.SCTExtractTitle()
        get_container_id = cmd = ["/usr/local/bin/docker", "ps", "-aqf", 'name=' + str(instance_name) ]
        container_id = subprocess.check_output(get_container_id).strip()
        cmd = """
set docker_id to "{container_id}"
tell application "iTerm"
	set newWindow to (create window with default profile)
	tell current session of newWindow
		write text "docker exec -it \" & docker_id & \" sh  "
	end tell
end tell
""".format(container_id=container_id)
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


if __name__=='__main__':
    app = NSApplication.sharedApplication()
    d = MyTray.alloc().init()
    app.setDelegate_(d)
    AppHelper.runEventLoop()
