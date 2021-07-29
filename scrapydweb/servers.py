import dataclasses
import logging
import re
from collections import namedtuple
from typing import List, Sequence

SCRAPYD_SERVER_PATTERN = re.compile(r"""
                                        ^
                                        (?:
                                            (?:(.*?):)      # username:
                                            (?:(.*?)@)      # password@
                                        )?
                                        (.*?)               # ip
                                        (?::(.*?))?         # :port
                                        (?:\#(.*?))?        # #group
                                        $
                                    """, re.X)

logger = logging.getLogger(__name__)

# Used for configuration
ServerConfig = namedtuple('ServerConfig', 'name hostname port group username password')


# Used at runtime
@dataclasses.dataclass(order=True, unsafe_hash=True)
class ScrapydServer:
    name: str
    ip: str
    port: int
    auth: tuple = (None, None)
    group: str = 'group'
    public_url: str = ''
    protocol: str = "http"

    def url(self):
        return f'{self.protocol}://{self.ip}:{self.port}'

    def __iter__(self):
        logger.warning("__iter__ called on a ScrapydServer! This should be replaced")
        yield from [self.group, self.ip, self.port, self.auth, self.public_url]

    def __str__(self):
        return f"{self.name or '??'} @ {self.ip}:{self.port}"


def find_by_name(servers: List[ScrapydServer], name: str) -> int:
    for i, server in enumerate(servers):
        if server.name == name:
            return i+1
    return 0


def names_to_nodes(servers: List[ScrapydServer], node_names: List[str]) -> List[int]:
    return [find_by_name(servers, name) for name in node_names]


def from_tuple(tupl: Sequence[str]) -> ScrapydServer:
    usr, psw, ip, port, group = tupl

    ip = ip.strip()
    port = int(port.strip())
    name = f"{ip}:{port}"

    server = ScrapydServer(name, ip, port)

    if group and group.strip():
        server.group = group.strip()
    if usr and psw:
        server.auth = (usr, psw)

    return server


def from_str(server: str) -> ScrapydServer:
    tupl = re.search(SCRAPYD_SERVER_PATTERN, server.strip()).groups()
    return from_tuple(tupl)
