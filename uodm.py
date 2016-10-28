"""Micro-ODM for MongoDB.

Features:
  - All attribute writes are immediately commited.
  - An ODM object encapsulates the connection and allows only one object
        per document to exist at a given time.
  - Does NOT use the "_id" field. Documents are indexed by a "_name_"
        field with a uuid. It is an error to have two documents with the
        same name.
  - Untyped schema.
  - Object can hold referenced to other objects.
"""

from __future__ import division, print_function, unicode_literals

import weakref
import abc
import uuid

__author__ = [  "Juan Carrano <jc@eiwa.ag>",
                "Diego Vazquez <dv@eiwa.ag>"
             ]
__copyright__ = "Copyright 2016 EIWA S.A. All rights reserved."
__license__ = """Unauthorized copying of this file, via any medium is
                 strictly prohibited. Proprietary and confidential"""


class DocumentError(Exception):
    pass

class Attr:
    """Describe a Document attribute."""
    def __init__(self, flags='', *args):
        """Flags is a string which can be empty or have any of the
         following characters:
            'm': mutable (can be modified)
            'r': reference (is a reference to another MappedDocument)

        If 'r' is specified, the class of the referenced MappedDocument
        must be specified as an additional argument.

        If 'r' is not specified, an additional argument is interpreted
        as a default value.
        """

        self.mutable = 'm' in flags
        self.reference = 'r' in flags

        if self.reference:
            self.ref_class = args[0]

        self.has_default = not self.reference and len(args)

        if self.has_default:
            self.default = args[0]

class Document(abc.ABC):
    """A Document object maps to a document in a collection.
    All documents have a _name_ attribute consisting of a UUID.

    Attributes can be references to other Documents. The database
    document will store the UUID of the referred document. When the
    attribute is acceces, the UUID is looked up in the ODM context and
    the corresponding Document object is returned.
    """

    @property
    @abc.abstractmethod
    def DB_COLLECTION(self):
        """The name of the collection where object of this type will be
        stored."""
        pass

    @property
    @abc.abstractmethod
    def ATTRIBUTES(self):
        """Mapping from attribute name to an Attr object.

        Example:

        ATTRIBUTES={
            'first_name': Attr()
            'nickname': Attr('s')
            'logged_in': Attr('s', False)
            'city': Attr('sr', CityClass)
            'parent': Attr('r', Parent)
        """
        pass


    def __init__(self, odm, _name_ = None, **kwargs):
        """Initialize the Document with the given values. If _name_
        is not given, it is assigned a new UUID.

        odm must be a ODM object.

        This constructor DOES NOT write the document to the database.

        Note that you probably don't want to use this method directly,
        but rather call ODM.new or Document.new_like .
        """

        self.contents = {}
        _kwargs = dict(kwargs)

        for k, attr_ in self.ATTRIBUTES.items():
            if k in _kwargs:
                value = _kwargs.pop(k)
            elif attr_.has_default:
                value = attr_.default
            else:
                raise ValueError("Argument ´%s´ not given and no default available"%k)

            raw_value = value if not attr_.reference else value._name_

            self.contents[k] = raw_value

        _kwargs.pop('_id', None)
        if _kwargs:
            raise ValueError("Too many keyword arguments")

        self._name_ = _name_ or self.generate_uuid()
        self._odm = odm

    @classmethod
    def generate_uuid(cls):
        return uuid.uuid1()

    def write(self):
        """Insert the document in the database. This is a low-level
        method"""
        _doc = {"_name_": self._name_}
        _doc.update(self.contents)

        self._odm.db_conn[self.DB_COLLECTION].insert(_doc)

    def __getattr__(self, name):
        if name in self.ATTRIBUTES:
            _attr = self.ATTRIBUTES[name]
            raw_value = self.contents[name]
            if _attr.reference:
                return self._odm.find_one(_attr.ref_class, raw_value)
            else:
                return raw_value
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self.ATTRIBUTES:
            _attr = self.ATTRIBUTES[name]

            if not _attr.mutable:
                raise AttributeError("Attribute %s is read-only"%name)

            raw_value = value if not _attr.reference else value._name_

            # FIXME: ensure that if the db update fails, this object is
            # not modified.
            self._odm.db_conn[self.DB_COLLECTION].update(
                        {"_name_":self._name_},
                        {'$set':{name: raw_value}})
            self.contents[name] = raw_value
        else:
            super().__setattr__(name, value)

    def set_multiple(self, d):
        """Modify multiple values in one operation.
        This works because document-level operations in Mongo are atomic.
        """
        raw_update = {}

        for k, v in d:
            try:
                _attr = self.ATTRIBUTES[k]
            except KeyError:
                raise AttributeError("Attribute %s not defined"%k)

            if not _attr.mutable:
                raise AttributeError("Attribute %s is read-only"%k)

            raw_value = v if not _attr.reference else v._name_

            raw_update[k] = raw_value

        self._odm.db_conn[self.DB_COLLECTION].update(
                                {"_name_":self._name_},
                                {'$set':raw_update})

    def find_one(self, _name_):
        """Find one document of the same type in the same ODM context as
        this object.
        """
        return self._odm.find_one(type(self), _name_)

    def find_all(self, criteria):
        """Find all document of the same type which match "criteria"
        in the same ODM context as this object.
        """
        return self._odm.find_all(type(self), criteria)

    def new_like(self, **kwargs):
        """Create a new object of the same type of this object in the
        same ODM context"""
        return self._odm.new(type(self), **kwargs)

class ODM:
    """ODM context.

    This class encapsulates a database connection. The key is that it
    provides a cache to ensure that only one object with a given _name_
    exists at any given time. This is the reason for using UUIDs instead
    of Mongo's _id field, which is guaranteed to be unique only within
    one collection.
    """
    def __init__(self, db_conn):
        """db_conn must be a mongo database. Example:
            client = pymongo.MongoClient(connection_uri)[db_name]
        """
        self.db_conn = db_conn
        self._cache = weakref.WeakValueDictionary()

    def find_one(self, cls, _name_):
        """Find a document by name. If more or less than one document is
        found, raise a DocumentError.

        cls: A class derived from Document
        _name_: a UUID.
        """
        try:
            obj = self._cache[_name_]
            return obj
        except KeyError:
            pass

        cursor = db_conn[cls.DB_COLLECTION].find({'_name_':_name_})

        if cursor.count() == 0:
            raise DocumentError("No such document.")
        elif cursor.count() != 1:
            raise DocumentError("More than one document with the same _name_. Possible DB corruption.")

        d = cursor[0]
        return self._new(cls, **d)

    def find_all(self, cls, criteria):
        """Return an iterable yielding all matching documents.

        cls: A class derived from Document
        criteria: search criteria like the one used in mongo's find()
            method.
        """
        cursor = self.db_conn[cls.DB_COLLECTION].find(criteria)

        for d in cursor:
            try:
                obj = self._cache[d['_name_']]
                yield obj
                continue
            except KeyError:
                pass

            yield self._new(cls, **d)

    def _new(self, cls, **kwargs):
        """Create a new object and register it in the cache.
        """
        obj = cls(self, **kwargs)
        self._cache[obj._name_] = obj
        return obj

    def new(self, cls, **kwargs):
        """Create a new object, register it in the cache and commit it
        to the database.

        cls: A class derived from Document
        kwargs: Object initializers.
        """
        obj = self._new(cls, **kwargs)
        obj.write()
        return obj
