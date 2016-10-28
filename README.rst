===========================
uODM: Micro-ODM for MongoDB
===========================

Features
--------

- All attribute writes are immediately commited.
- An `ODM` object encapsulates the connection and allows only one object
  per document to exist at a given time.
- Does NOT use the "_id" field. Documents are indexed by a "_name_"
  field with a uuid. It is an error to have two documents with the
  same name.
- Object can hold referenced to other objects.
- Attributes can be defined as mutable or immutable.

Limitations
-----------

- Untyped schema.
- Attributes cannot be nested (but attributes can be dictionaries)

Possible enhancements
---------------------

- Add support for read-modify-write.
