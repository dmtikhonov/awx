# Copyright (c) 2015 Ansible, Inc.
# This file is a utility Ansible plugin that is not part of the AWX or Ansible
# packages.  It does not import any code from either package, nor does its
# license apply to Ansible or AWX.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    Neither the name of the <ORGANIZATION> nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import memcache
import json

try:
    from ansible.cache.base import BaseCacheModule
except:
    from ansible.plugins.cache.base import BaseCacheModule


class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        # Basic in-memory caching for typical runs
        self.mc = memcache.Client([os.environ['MEMCACHED_LOCATION']], debug=0)
        self.inventory_id = os.environ['INVENTORY_ID']

    @property
    def host_names_key(self):
        return '{}'.format(self.inventory_id)

    def translate_host_key(self, host_name):
        return '{}-{}'.format(self.inventory_id, host_name)

    def translate_modified_key(self, host_name):
        return '{}-{}-modified'.format(self.inventory_id, host_name)

    def get(self, key):
        host_key = self.translate_host_key(key)
        value_json = self.mc.get(host_key)
        if not value_json:
            raise KeyError
        return json.loads(value_json)

    def set(self, key, value):
        host_key = self.translate_host_key(key)
        modified_key = self.translate_modified_key(key)

        self.mc.set(host_key, json.dumps(value))
        self.mc.set(modified_key, True)

    def keys(self):
        return self.mc.get(self.host_names_key)

    def contains(self, key):
        val = self.mc.get(key)
        if val is None:
            return False
        return True

    def delete(self, key):
        self.mc.delete(self.translate_host_key(key))
        self.mc.delete(self.translate_modified_key(key))

    def flush(self):
        for k in self.mc.get(self.host_names_key):
            self.mc.delete(self.translate_host_key(k))
            self.mc.delete(self.translate_modified_key(k))

    def copy(self):
        ret = dict()
        for k in self.mc.get(self.host_names_key):
            ret[k] = self.mc.get(self.translate_host_key(k))
        return ret

