# -*- coding: utf-8 -*-

from twisted.internet import reactor,threads
from coherence.upnp.core import DIDLLite
from coherence import log
from coherence.backend import AbstractBackendStore, Container, BackendItem 

TRACK_MIMETYPE = "audio/flac"

class TrackItem(BackendItem):
    logCategory = "mbira"

    def __init__(self, track_number=1, artist="Unknown", title="Unknown"):
        self.track_number = track_number
        self.artist = artist
        self.title = title
        self.name=self.title # Remove after own sort method.
        self.mimetype = TRACK_MIMETYPE
        self.item = None
        self.location = "/srv/music/flac-private/Erik Hassle/Mariefred Sessions/01 - Are You Leaving.flac"

    def get_item(self):
        if self.item == None:
            upnp_id = self.storage_id
            upnp_parent_id = self.parent.get_id()
            url = self.store.urlbase + str(self.storage_id)
            self.item = DIDLLite.MusicTrack(upnp_id, upnp_parent_id, self.title)

            res = DIDLLite.Resource(url, 'http-get:*:%s:*' % (self.mimetype))
            self.item.res.append(res)
        return self.item

    def get_name(self):
        return self.title

    def get_path(self):
        return self.location  

    def get_size(self):
        return self.size
    
    def get_id (self):
        return self.storage_id


class MbiraStore(AbstractBackendStore):

    logCategory = 'mbira'
    implements = ['MediaServer']
    description = ('mbira', '', None)

    def __init__(self, server, **kwargs):
        AbstractBackendStore.__init__(self, server, **kwargs)
        self.name = 'Mbira'
        threads.deferToThread(self.extractAudioCdInfo)
        

    def upnp_init(self):
        if self.server:
            self.server.connection_manager_server.set_variable(0, 'SourceProtocolInfo',
                        ['http-get:*:%s:*' % (TRACK_MIMETYPE)],
                        default=True)
            self.server.content_directory_server.set_variable(0, 'SystemUpdateID', self.update_id)


    def extractAudioCdInfo (self):
        """ extract the CD info (album art + artist + tracks), and construct the UPnP items"""
        self.disc_title = "My disk"
        self.name = "Mbira"

        root_item = Container(None, self.disc_title)
        self.set_root_item(root_item)

        item = TrackItem(10, "Unknown", "Title")
        root_item.add_child(item, external_id = "10")

        self.info('Sharing audio CD %s' % self.disc_title)

        self.init_completed()
        
    def __repr__(self):
        return self.__class__.__name__        
