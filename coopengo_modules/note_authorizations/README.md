## Trytond Note Authorizations

This modules enriches the *Note* functionality of
[tryton](http://www.tryton.org). It adds:
- Configurable note types
- Authorizations definitions per note type

Notes that are linked to a type that the current user is not allowed to view
will be invisible to this user. He will not be able to create any note with
those types.
