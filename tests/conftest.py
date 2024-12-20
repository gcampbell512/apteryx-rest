import apteryx
import json
import os
import pytest
import requests
import subprocess
import time


# TEST CONFIGURATION

server_uri = 'http://localhost:8080'
server_auth = None
# server_uri = 'https://192.168.6.2:443'
# server_auth = requests.auth.HTTPBasicAuth('manager', 'friend')
docroot = '/api'

get_restconf_headers = {"Accept": "application/yang-data+json"}
set_restconf_headers = {"Content-Type": "application/yang-data+json"}

# TEST HELPERS

# Path segments are defined in ABNF grammar as
# node-identifier = [prefix ":"] identifier
# prefix = identifier
# identifier = (ALPHA / "_")*(ALPHA / DIGIT / "_" / "-" / ".")
# ALPHA = A-Z / a-z

# List keys and leaf-list values in path segments.
# https://en.wikipedia.org/wiki/Percent-encoding
# The key value is specified as a string, using the canonical
# representation for the YANG data type.  Any reserved characters
# MUST be percent-encoded, according to Sections 2.1 and 2.5 of
# [RFC3986]. The comma (",") character MUST be percent-encoded if
# it is present in the key value.
# NOTE Python requests library will automatically percent-encode
# or ignore some characters if they are not already percent-encoded
# e.g. '[]% ' are automatically percent-encoded, '#' is removed?
# TODO? newline,space,",%,-,.,<,>,\,^,_,`,{,|,},~
rfc3986_reserved = "!#$&'()*+,/:;=?@[]" + "% "

db_default = [
    # Default namespace
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/settings/readonly', '0'),
    ('/test/settings/hidden', 'friend'),
    ('/test/state/counter', '42'),
    ('/test/state/uptime/days', '5'),
    ('/test/state/uptime/hours', '50'),
    ('/test/state/uptime/minutes', '30'),
    ('/test/state/uptime/seconds', '20'),
    ('/test/animals/animal/cat/name', 'cat'),
    ('/test/animals/animal/cat/type', '1'),
    ('/test/animals/animal/dog/name', 'dog'),
    ('/test/animals/animal/dog/colour', 'brown'),
    ('/test/animals/animal/mouse/name', 'mouse'),
    ('/test/animals/animal/mouse/type', '2'),
    ('/test/animals/animal/mouse/colour', 'grey'),
    ('/test/animals/animal/hamster/name', 'hamster'),
    ('/test/animals/animal/hamster/type', '2'),
    ('/test/animals/animal/hamster/food/banana/name', 'banana'),
    ('/test/animals/animal/hamster/food/banana/type', 'fruit'),
    ('/test/animals/animal/hamster/food/nuts/name', 'nuts'),
    ('/test/animals/animal/hamster/food/nuts/type', 'kibble'),
    ('/test/animals/animal/parrot/name', 'parrot'),
    ('/test/animals/animal/parrot/type', '1'),
    ('/test/animals/animal/parrot/colour', 'blue'),
    ('/test/animals/animal/parrot/toys/toy/rings', 'rings'),
    ('/test/animals/animal/parrot/toys/toy/puzzles', 'puzzles'),
    # Default namespace augmented path
    ('/test/settings/volume', '1'),
    # Non-default namespace same path as default
    ('/t2:test/settings/priority', '2'),
    # Non-default namespace augmented path
    ('/t2:test/settings/speed', '2'),
    # Apteryx namespace
    ('/test3/state/age', '99'),
    # Data for with-defaults testing
    ('/interfaces/interface/eth0/name', 'eth0'),
    ('/interfaces/interface/eth0/mtu', '8192'),
    ('/interfaces/interface/eth0/status', 'up'),
    ('/interfaces/interface/eth1/name', 'eth1'),
    ('/interfaces/interface/eth1/status', 'up'),
    ('/interfaces/interface/eth2/name', 'eth2'),
    ('/interfaces/interface/eth2/mtu', '9000'),
    ('/interfaces/interface/eth2/status', 'not feeling so good'),
    ('/interfaces/interface/eth3/name', 'eth3'),
    ('/interfaces/interface/eth3/mtu', '1500'),
    ('/interfaces/interface/eth3/status', 'waking up'),
]


@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    apteryx.prune("/test")
    apteryx.prune("/t2:test")
    apteryx.prune("/test3")
    apteryx.prune("/t4:test")
    for path, value in db_default:
        apteryx.set(path, value)
    yield
    # After test
    os.system("echo After test")
    apteryx.prune("/test")
    apteryx.prune("/t2:test")
    apteryx.prune("/test3")
    apteryx.prune("/t4:test")
