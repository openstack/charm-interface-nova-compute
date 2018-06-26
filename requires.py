# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
from urllib.parse import urlparse
import uuid

from charmhelpers.core import hookenv

from charms.reactive import set_flag, clear_flag
from charms.reactive import Endpoint
from charms.reactive import when_any, when_not, when


class NovaComputeRequires(Endpoint):

    @when('endpoint.{endpoint_name}.changed')
    def data_changed(self):
        #set_flag(self.expand_name('{endpoint_name}.available'))
        pass

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        clear_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        set_flag(self.expand_name('{endpoint_name}.connected'))


    def set_network_data(self, neutron_url, neutron_plugin=None, network_manager=None, enable_security_groups=True):
        o = urlparse(neutron_url)
        if enable_security_groups:
            security_groups = 'yes'
        else:
            security_groups = 'no'
        for relation in self.relations:
            relation.to_publish_raw['quantum_host'] = o.hostname
            relation.to_publish_raw['quantum_plugin'] = neutron_plugin or 'ovs'
            relation.to_publish_raw['quantum_port'] = o.port
            relation.to_publish_raw['quantum_security_groups'] = security_groups
            relation.to_publish_raw['quantum_url'] = neutron_url
            relation.to_publish_raw['network_manager'] = network_manager or 'neutron'

    def set_console_data(self, serial_console_base_url, enable_serial_console):
        for relation in self.relations:
            relation.to_publish_raw['serial_console_base_url'] = serial_console_base_url
            relation.to_publish_raw['enable_serial_console'] = enable_serial_console

    def trigger_remote_restart(self):
        trigger = uuid.uuid1()
        for relation in self.relations:
            relation.to_publish_raw['restart_trigger'] = trigger

    def set_region(self, region):
        for relation in self.relations:
            relation.to_publish_raw['region'] = region

    def set_volume_data(self, volume_service):
        for relation in self.relations:
            relation.to_publish_raw['volume_service'] = volume_service

    def set_ec2_data(self, ec2_host):
        for relation in self.relations:
            relation.to_publish_raw['ec2_host'] = ec2_host
