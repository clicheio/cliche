""":mod:`cliche.credentials` --- Authentication methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import BigInteger, Integer, String

from .user import Credential


__all__ = 'TwitterCredential',


class TwitterCredential(Credential):
    """Information about Twitter User"""

    #: (:class:`int`) The primary key from :class:`Credential.id`.
    id = Column(Integer, ForeignKey('credential.id'), primary_key=True)

    #: (:class:`int`) Twitter user id
    identifier = Column(BigInteger, nullable=False, unique=True)

    #: (:class:`str`) The oauth token.
    token = Column(String)

    #: (:class:`str`) The oauth secret token.
    token_secret = Column(String)

    __tablename__ = 'twitter_credential'
    __mapper_args__ = {'polymorphic_identity': 'twitter'}
    __repr_columns__ = id, identifier
