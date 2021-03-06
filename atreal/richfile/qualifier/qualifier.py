import re
from DateTime import DateTime

from zope.interface import implements
from zope.component.interfaces import ComponentLookupError
from zope.traversing.adapters import Traverser
from zope.interface import alsoProvides, noLongerProvides
from zope.event import notify
from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.utils import getToolByName

# we get the registry
from atreal.richfile.qualifier.registry import filequalifier_registry, provided_interfaces
from atreal.richfile.qualifier.interfaces import IFileQualifier
from atreal.richfile.qualifier.events import FileQualifiedEvent, MimetypeChangedEvent
from atreal.richfile.qualifier.common import RFPlugin

class FileQualifier(RFPlugin):

    implements(IFileQualifier)


    def process(self):
        """ Proceed to the markage """
        # We abort the process while we are in the creation process 
        # (portal_factory...)
        if self.context.checkCreationFlag():
            return
        if self._setInterfaces():
            notify(FileQualifiedEvent(self.context))


    def cleanUp(self):
        """ """
        super(FileQualifier, self).cleanUp()
        self._cleanupInterfaces()


    def _setInterfaces(self):
        """ Mark the object with the right interfaces """
        contenttype = self.content_type
        # We check if the content type has changed
        if self.info.has_key('contenttype') and self.info['contenttype'] != contenttype:
            # It changed, so we have to clean the interface and notify the plugins
            notify(MimetypeChangedEvent(self.context))
            self._cleanupInterfaces()
        # We store the content type
        self.info['contenttype'] = contenttype
        need_mark = False
        interfaces = []
        if filequalifier_registry.has_key(contenttype):
            # We have plugins that can work on this content type
            interfaces.extend(filequalifier_registry[contenttype])
            need_mark = True
        # Special use case for plugins allowing '*/*' mimetype
        # XXX TODO : support mimetype like 'image/*'
        if filequalifier_registry.has_key('*/*'):
            interfaces.extend(filequalifier_registry['*/*'])
            need_mark = True
        if need_mark:
            # We clean
            self._cleanupInterfaces()
            # We mark it
            for interface in interfaces:
                alsoProvides(self.context, interface)
            self.context.reindexObject(idxs=['object_provides'])
            return True
        return False


    def _cleanupInterfaces(self):
        """ Clean up our own interfaces """
        for interface in provided_interfaces:
            noLongerProvides(self.context, interface)
