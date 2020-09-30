# GPLv3 License
#
# Copyright (C) 2020 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
An elementary json encoder-decoder to transmit Proxy and Delta items

This module and the resulting encoding are by no way optimal. It is just a simple
implementation that does the job.
"""
import json
from typing import Any, Mapping

from mixer.blender_data.proxy import (
    DatablockProxy,
    DatablockRefProxy,
    StructProxy,
    DatablockCollectionProxy,
    StructCollectionProxy,
    NodeLinksProxy,
    NodeTreeProxy,
    Delta,
    DeltaAddition,
    DeltaDeletion,
    DeltaUpdate,
)

# https://stackoverflow.com/questions/38307068/make-a-dict-json-from-string-with-duplicate-keys-python/38307621#38307621
# https://stackoverflow.com/questions/31085153/easiest-way-to-serialize-object-in-a-nested-dictionary

struct_like_classes = [
    DatablockProxy,
    DatablockRefProxy,
    StructProxy,
    StructProxy,
    NodeLinksProxy,
    NodeTreeProxy,
]
collection_classes = [
    StructCollectionProxy,
    DatablockCollectionProxy,
]
delta_classes = [
    Delta,
    DeltaAddition,
    DeltaDeletion,
    DeltaUpdate,
]
_classes = {c.__name__: c for c in struct_like_classes}
_classes.update({c.__name__: c for c in collection_classes})
_classes.update({c.__name__: c for c in delta_classes})

options = ["_bpy_data_collection", "_class_name", "_datablock_uuid", "_initial_name"]
MIXER_CLASS = "__mixer_class__"


def default_optional(obj, option_name: str) -> Mapping[str, Any]:
    option = getattr(obj, option_name, None)
    if option is not None:
        return {option_name: option}
    return {}


def default(obj):
    # called top down
    class_ = obj.__class__

    # TODO AOS and SOA

    is_known = issubclass(class_, (StructProxy, DatablockRefProxy, Delta)) or class_ in collection_classes
    if is_known:
        # Add the proxy class so that the decoder and instantiate the right type
        d = {MIXER_CLASS: class_.__name__}
        if issubclass(class_, Delta):
            d.update({"value": obj.value})
        else:
            d.update({"_data": obj._data})

        for option in options:
            d.update(default_optional(obj, option))
        return d
    return None


def decode_optional(obj, x, option_name):
    option = x.get(option_name)
    if option is not None:
        setattr(obj, option_name, option)


def decode_hook(x):
    class_name = x.get(MIXER_CLASS)
    class_ = _classes.get(class_name)
    if class_ is None:
        return x

    del x[MIXER_CLASS]
    obj = class_()
    if class_ in delta_classes:
        obj.value = x["value"]
    else:
        obj._data.update(x["_data"])

    for option in options:
        decode_optional(obj, x, option)
    return obj


class Codec:
    def encode(self, obj):
        return json.dumps(obj, default=default)

    def decode(self, message):
        return json.loads(message, object_hook=decode_hook)
