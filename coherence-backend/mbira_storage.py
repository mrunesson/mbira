# -*- coding: utf-8 -*-

from twisted.internet import reactor,threads
from coherence.upnp.core import DIDLLite
from coherence import log
from coherence.backend import AbstractBackendStore, Container, BackendItem 
import pymongo
import os

TRACK_MIMETYPE = "audio/flac"

class TrackItem(BackendItem):
    logCategory = "mbira"

    def __init__(self, track):
        self.track=track
        self.name=self.track[u'title'][0] # Remove after own sort method.
        self.mimetype = TRACK_MIMETYPE
        self.item = None
        self.location = self.track[u'_file'][0]
        statinfo = os.stat(self.location)
        self.size = statinfo.st_size

    def get_item(self):
        if self.item == None:
            upnp_id = self.storage_id
            upnp_parent_id = self.parent.get_id()
            url = self.store.urlbase + str(self.storage_id)
            self.item = DIDLLite.MusicTrack(upnp_id, upnp_parent_id, self.name)

            res = DIDLLite.Resource(url, 'http-get:*:%s:*' % (self.mimetype))
            self.item.res.append(res)
            self.item.artist=self.track[u'artist'][0]
            self.item.album=self.track[u'album'][0]
            self.item.originalTrackNumber = self.track[u'tracknumber'][0]
        return self.item

    def get_path(self):
        return self.location  

    def get_size(self):
        return self.size
    
    def get_id (self):
        return self.storage_id


class ArtistContainer(Container):

    def __init__(self, parent, artist):
        Container.__init__(self, parent, artist[u'artist'][0])
        self.artist=artist
        

    def populate_albums_for_artist(self):
        pass


class AlbumContainer(Container):

    def __init__(self, parent, album):
        Container.__init__(self, parent, album[u'album'][0])
        self.album=album
        

    def populate_tracks_for_album(self):
        pass


class MbiraStore(AbstractBackendStore):

    logCategory = 'mbira'
    implements = ['MediaServer']
    description = ('mbira', '', None)

    def __init__(self, server, **kwargs):
        AbstractBackendStore.__init__(self, server, **kwargs)
        self.name = 'Mbira'
        threads.deferToThread(self.init_data)
        

    def upnp_init(self):
        if self.server:
            self.server.connection_manager_server.set_variable(0,
                'SourceProtocolInfo',
                ['http-get:*:%s:*' % (TRACK_MIMETYPE)],
                default=True)
            self.server.content_directory_server.set_variable(0,
                'SystemUpdateID', self.update_id)

    def init_data(self):
        connection=pymongo.Connection()
        self.db=connection['mbira']
        self.init_container_structure()
        self.init_all_tracks()
        self.init_all_artists()
        self.init_all_albums()
        self.info("Init complete")
        self.init_completed()

    def init_all_tracks(self):
        tracks=self.db.tracks.find()
        for t in tracks:
            item = TrackItem(t)
            external_id = t[u'_id']
            self.allTracksContainer.add_child(item, external_id = external_id)
   
    def init_all_artists(self):
        artists=self.db.artists.find()
        for a in artists:
            item = ArtistContainer(self.get_root_item(), a)
            external_id = a[u'_id']
            self.artistsContainer.add_child(item, external_id = external_id)

    def init_all_albums(self):
        albums=self.db.albums.find()
        for a in albums:
            item = AlbumContainer(self.get_root_item(), a)
            external_id = a[u'_id']
            self.albumsContainer.add_child(item, external_id = external_id)


    def init_container_structure(self):
        self.name = "Mbira"
        root_item = Container(None, self.name)
        self.set_root_item(root_item)

        self.albumsContainer = Container(root_item, "Albums")
        root_item.add_child(self.albumsContainer, external_id = "Albums")

        self.allTracksContainer = Container(root_item, "All tracks")
        root_item.add_child(self.allTracksContainer, external_id = "AllTracks")

        self.artistsContainer = Container(root_item, "Artists")
        root_item.add_child(self.artistsContainer, external_id = "Artists")

        genresContainer = Container(root_item, "Genres")
        root_item.add_child(genresContainer, external_id = "Genres")

        playlistsContainer = Container(root_item, "Playlists")
        root_item.add_child(playlistsContainer, external_id = "Playlists")




        
    def __repr__(self):
        return self.__class__.__name__        
