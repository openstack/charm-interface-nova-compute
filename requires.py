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

from urllib.parse import urlparse
import uuid

from charms.reactive import set_flag, clear_flag
from charms.reactive import Endpoint
from charms.reactive import when_not, when


class NovaComputeRequires(Endpoint):

    @when('endpoint.{endpoint_name}.changed')
    def data_changed(self):
        """Set flag to indicate to charm relation data has changed."""
        set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        """Remove flag to indicate to charm relation has gone.."""
        clear_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        """Set flag to indicate to charm relation has been joined."""
        set_flag(self.expand_name('{endpoint_name}.connected'))

    def set_network_data(self, neutron_url, neutron_plugin=None,
                         network_manager=None, enable_security_groups=True):
        """Send compute nodes data relating to network setup.

        :param neutron_url: URL for network API service
        :type neutron_url: str
        :param neutron_plugin: Neutron plugin to use
        :type neutron_plugin: str
        :param network_manager: Network Manager
        :type network_manager: str
        :param enable_security_groups: Whether to enable security groups
        :type enable_security_group: bool
        """
        o = urlparse(neutron_url)
        if enable_security_groups:
            security_groups = 'yes'
        else:
            security_groups = 'no'
        for r in self.relations:
            r.to_publish_raw['quantum_host'] = o.hostname
            r.to_publish_raw['quantum_plugin'] = neutron_plugin or 'ovs'
            r.to_publish_raw['quantum_port'] = o.port
            r.to_publish_raw['quantum_security_groups'] = security_groups
            r.to_publish_raw['quantum_url'] = neutron_url
            r.to_publish_raw['network_manager'] = network_manager or 'neutron'

    def set_console_data(self, serial_console_base_url, enable_serial_console):
        """Send compute nodes data relating to serial console access.

        :param serial_console_base_url: URL for accessing the serial console.
        :type serial_console_base_url: str
        :param enable_serial_console: Whether to enable the serial console
        :type enable_serial_console: bool
        """
        for r in self.relations:
            r.to_publish_raw[
                'serial_console_base_url'] = serial_console_base_url
            r.to_publish_raw['enable_serial_console'] = enable_serial_console

    def trigger_remote_restart(self, restart_key=None):
        """Trigger a restart of services on the remote application.

        :param restart_key: Key to send to remote service, restarts are
                            triggered when the key changes.
        :type restart_key: str
        """
        if not restart_key:
            restart_key = uuid.uuid1()
        for relation in self.relations:
            relation.to_publish_raw['restart_trigger'] = restart_key

    def set_region(self, region):
        """Send compute nodes region information.

        :param region: Region compute nodes will belong to.
        :type region: str
        """
        for relation in self.relations:
            relation.to_publish_raw['region'] = region

    def set_volume_data(self, volume_service):
        """Send compute nodes volume information.

        :param volume_service: Name of volume service to use, eg cinder
        :type volume_service: str
        """
        for relation in self.relations:
            relation.to_publish_raw['volume_service'] = volume_service

    def set_ec2_data(self, ec2_host):
        """Send compute nodes ec2 information.

        :param ec2_host: Name of ec2_host.
        :type ec2_host: str
        """
        for relation in self.relations:
            relation.to_publish_raw['ec2_host'] = ec2_host

    def collect_ssh_keys(self, application_name=None):
        """Query related units and collect ssh artifacts.

        :param application_name: Only return artifacts from units of this
                                 applicationa.
        :type application_name: str
        :returns: {APP_NAME: {UNIT_NAME: {pupkey1:.., hostkey1:...}}}
        :rtype: dict
        """
        ssh_keys = {}
        for rel in self.relations:
            if application_name and application_name != rel.application_name:
                continue
            ssh_keys[rel.application_name] = {}
            for unit in rel.units:
                nova_ssh_pub_key = unit.received.get('nova_ssh_public_key')
                ssh_pub_key = unit.received.get('ssh_public_key')
                if nova_ssh_pub_key and ssh_pub_key:
                    ssh_keys[rel.application_name][unit.unit_name] = {
                        'nova_ssh_pub_key': nova_ssh_pub_key,
                        'hostname': unit.received.get('hostname'),
                        'private-address': unit.received.get(
                            'private-address'),
                        'ssh_pub_key': ssh_pub_key}
        return ssh_keys

    def send_ssh_keys(self, relation, settings):
        """Publish the provided ssh settings on the given relation

        :param relation: Relation to publish settings on.
        :type relation: charms.reactive.endpoints.Relation
        :param settings: SSH settings to publish.
        :type settings: dict
        """
        for key, value in settings.items():
            relation.to_publish_raw[key] = value
