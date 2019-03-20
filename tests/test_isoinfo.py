# This work is licensed under the GNU GPLv2 or later.
# See the COPYING file in the top-level directory.

import logging
import os
import pytest

from . import util


@pytest.mark.parametrize('_os', util.DataFiles.oses(), ids=lambda o: o.shortid)
def test_iso_detection(_os):
    for isodatamedia in _get_isodatamedias(_os):
        detected = []
        for __os in util.DataFiles.oses():
            for media in __os.medias:
                if isodatamedia.match(media.iso):
                    if _os.shortid != __os.shortid:
                        logging.warning(
                            'ISO \'%s\' was matched by OS \'%s\' while it '
                            'should only be matched by OS \'%s\'',
                            isodatamedia.filename, __os.shortid, _os.shortid)
                    else:
                        logging.info('ISO \'%s\' matched by OS \'%s\'',
                                     isodatamedia.filename, __os.shortid)
                    # For several distros we do not have the volume-size
                    # set as part of our DB, thus multiple detections may
                    # occur. Although this case is not the optimal, as long
                    # as we detect the very same distro it's okay-ish.
                    if __os.shortid not in detected:
                        detected.append(__os.shortid)

        if len(detected) != 1:
            logging.warning('Some ISOs have been matched several times by '
                            'the different OSes, which indicates an issue '
                            'in the DB entries.')
        assert len(detected) == 1


class _ISODataMedia():
    def __init__(self, filename, volumeid, publisherid, systemid,
                 applicationid, volumesize):

        self.filename = filename
        self.volumeid = volumeid if volumeid is not None else ''
        self.publisherid = publisherid if publisherid is not None else ''
        self.systemid = systemid if systemid is not None else ''
        self.applicationid = applicationid \
                if applicationid is not None else ''
        self.volumesize = volumesize if volumesize is not None else 0

    def match(self, media):
        volumesize = media.volumesize
        if volumesize == 0:
            volumesize = self.volumesize

        if bool(media.volumeid.match(self.volumeid)) and \
           bool(media.publisherid.match(self.publisherid)) and \
           bool(media.applicationid.match(self.applicationid)) and \
           bool(media.systemid.match(self.systemid)) and \
           volumesize == self.volumesize:
            return True

        return False


def _get_value(string, prefix, return_type=str):
    if string.startswith(prefix):
        return return_type(string.split(': ')[-1].strip())
    return None


def _get_volumeid(string):
    return _get_value(string, 'Volume id: ')


def _get_publisherid(string):
    return _get_value(string, 'Publisher id: ')


def _get_systemid(string):
    return _get_value(string, 'System id: ')


def _get_applicationid(string):
    return _get_value(string, 'Application id: ')


def _get_logicalblock(string):
    return _get_value(string, 'Logical block size is: ', int)


def _get_volumesize(string):
    return _get_value(string, 'Volume size is: ', int)


def _get_isodatamedia(filepath):
    volumeid = None
    publisherid = None
    systemid = None
    applicationid = None
    logicalblock = None
    volumesize = None

    with open(filepath, 'r') as out:
        for line in out.readlines():
            if volumeid is None:
                volumeid = _get_volumeid(line)
            if publisherid is None:
                publisherid = _get_publisherid(line)
            if systemid is None:
                systemid = _get_systemid(line)
            if applicationid is None:
                applicationid = _get_applicationid(line)
            if logicalblock is None:
                logicalblock = _get_logicalblock(line)
            if volumesize is None:
                volumesize = _get_volumesize(line)

    if logicalblock is not None and volumesize is not None:
        volumesize *= logicalblock
    else:
        volumesize = None

    return _ISODataMedia(filepath, volumeid, publisherid, systemid,
                         applicationid, volumesize)


def _get_isodatamedias(_os):
    isodata_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'isodata')
    shortid_path = os.path.join(isodata_path, _os.distro, _os.shortid)

    medias = []
    if not os.path.exists(shortid_path):
        return []

    for _file in os.listdir(shortid_path):
        path = os.path.join(shortid_path, _file)
        if not os.path.exists(path):
            continue

        medias.append(_get_isodatamedia(path))
    return medias
