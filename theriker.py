from twisted.internet import epollreactor
epollreactor.install()

from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log

import sys, re

class FunctionBot(IRCClient):
    function_regex = re.compile('!(\w+)\s*')
    regex_regex = re.compile('s/([^/]*)/([^/]*)(?:/([ig]*)(?:\s+(\w+))?)?')

    def signedOn(self):
        for c in self.factory.settings.CHANNELS:
            self.join(c)

    def kickedFrom(self, channel, kicker, message):
        if self.factory.settings.REJOIN_ON_KICK:
            reactor.callLater(self.factory.settings.REJOIN_DELAY, self.join, channel)

    def privmsg(self, user, channel, msg):
        user = user[:user.index('!')]
        mo = self.function_regex.match(msg)
        if mo:
            name = mo.group(1)
            arg = msg[mo.end(0):]
            #self.msg(channel, 'Function %s called with arg "%s" by %s.' % (mo.group(1), arg, user))
            return
        mo = self.regex_regex.match(msg)
        if mo:
            pat, repl, opt, target = mo.group(1, 2, 3, 4)
            count = 1
            flags = 0
            if target == None:
                target = user
            if (channel+target) not in self.linelog:
                return
            if opt != None:
                if opt.count('g') == 1:
                    count = 0
                if opt.count('i') == 1:
                    flags = re.I
            msg, subs = re.subn(pat, repl, self.linelog[channel+target], count, flags)
            if subs > 0:
                self.msg(channel, '<%s> %s' % (target, msg))
                self.linelog[channel+target] = msg
            #self.msg(channel, 'Regex! "%s" "%s" "%s" for %s' % (pat,repl,opt,target))
            return
        self.linelog[channel+user] = msg
            

class FunctionBotFactory(ReconnectingClientFactory):
    def __init__(self, settings):
        self.settings = settings

    def buildProtocol(self, addr):
        self.resetDelay()
        p = FunctionBot()
        p.factory = self
        p.nickname = self.settings.NICKNAME
        p.password = self.settings.PASSWORD
        p.realname = self.settings.REALNAME
        p.username = self.settings.USERNAME
        p.linelog = {}
        return p

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    __import__(sys.argv[1])
    settings = sys.modules[sys.argv[1]]
    factory = FunctionBotFactory(settings)
    if settings.SSL:
        sys.exit(1)
    else:
        reactor.connectTCP(settings.HOST, settings.PORT, factory)
    reactor.run()
