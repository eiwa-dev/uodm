"""Test the uodm"""

from __future__ import division, print_function, unicode_literals

import posixpath

import pymongo

import uodm
from uodm import Attr

__author__ = [  "Juan Carrano <jc@eiwa.ag>",
                "Federico Allo Ron <far@eiwa.ag>"
             ]
__copyright__ = "Copyright 2016 EIWA S.A. All rights reserved."
__license__ = """Unauthorized copying of this file, via any medium is
                 strictly prohibited. Proprietary and confidential"""

class City(uodm.Document):
    DB_COLLECTION = 'cities'

    ATTRIBUTES = {
        'name': Attr(),
        'population': Attr('m'),
        'ancient': Attr('', False),
    }

class Person(uodm.Document):
    DB_COLLECTION = 'people'

    ATTRIBUTES = {
        'name': Attr(),
        'age': Attr('m'),
        'city': Attr('mr', City),
        'is_cool': Attr('', True)
    }


if __name__ == '__main__':
    import sys

    mongo_conn_uri = sys.argv[1]

    dbname = posixpath.basename(mongo_conn_uri)
    client = pymongo.MongoClient(mongo_conn_uri)[dbname]

    odm = uodm.ODM(client)
