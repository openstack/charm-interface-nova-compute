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


import unittest
from unittest import mock


with mock.patch('charmhelpers.core.hookenv.metadata') as _meta:
    _meta.return_Value = 'ss'
    import requires


_hook_args = {}

TO_PATCH = [
    'clear_flag',
    'set_flag',
]


def mock_hook(*args, **kwargs):

    def inner(f):
        # remember what we were passed.  Note that we can't actually determine
        # the class we're attached to, as the decorator only gets the function.
        _hook_args[f.__name__] = dict(args=args, kwargs=kwargs)
        return f
    return inner


class _unit_mock:
    def __init__(self, unit_name, received=None):
        self.unit_name = unit_name
        self.received = received or {}


class _relation_mock:
    def __init__(self, application_name=None, units=None):
        self.to_publish_raw = {}
        self.application_name = application_name
        self.units = units


class TestNovaComputeRequires(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._patched_hook = mock.patch('charms.reactive.when', mock_hook)
        cls._patched_hook_started = cls._patched_hook.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    @classmethod
    def tearDownClass(cls):
        cls._patched_hook.stop()
        cls._patched_hook_started = None
        cls._patched_hook = None
        # and fix any breakage we did to the module
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    def patch(self, method):
        _m = mock.patch.object(self.obj, method)
        _mock = _m.start()
        self.addCleanup(_m.stop)
        return _mock

    def setUp(self):
        self.ncr = requires.NovaComputeRequires('some-relation', [])
        self._patches = {}
        self._patches_start = {}
        self.obj = requires
        for method in TO_PATCH:
            setattr(self, method, self.patch(method))

    def tearDown(self):
        self.ncr = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_kr(self, attr, return_value=None):
        mocked = mock.patch.object(self.ncr, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def test_registered_hooks(self):
        # test that the decorators actually registered the relation
        # expressions that are meaningful for this interface: this is to
        # handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_patterns = {
            'data_changed': ('endpoint.{endpoint_name}.changed', ),
            'joined': ('endpoint.{endpoint_name}.joined', ),
            'broken': ('endpoint.{endpoint_name}.joined', ),
        }
        for k, v in _hook_args.items():
            self.assertEqual(hook_patterns[k], v['args'])

    def test_date_changed(self):
        self.ncr.data_changed()
        self.set_flag.assert_called_once_with('some-relation.available')

    def test_broken(self):
        self.ncr.broken()
        self.clear_flag.assert_called_once_with('some-relation.available')

    def test_joined(self):
        self.ncr.joined()
        self.set_flag.assert_called_once_with('some-relation.connected')

    def test_set_network_data(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_network_data(
            'http://bob:345/dddd/')
        expect = {
            'quantum_host': 'bob',
            'quantum_plugin': 'ovs',
            'quantum_port': 345,
            'quantum_security_groups': 'yes',
            'quantum_url': 'http://bob:345/dddd/',
            'network_manager': 'neutron'
        }
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_set_network_data_no_defaults(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_network_data(
            'http://bob:345/dddd/',
            neutron_plugin='vTokenRing',
            network_manager='vTRManager',
            enable_security_groups=False)
        expect = {
            'quantum_host': 'bob',
            'quantum_plugin': 'vTokenRing',
            'quantum_port': 345,
            'quantum_security_groups': 'no',
            'quantum_url': 'http://bob:345/dddd/',
            'network_manager': 'vTRManager'
        }
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_set_console_data(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_console_data(
            'http://bob:345/serial/',
            enable_serial_console=True)
        expect = {
            'serial_console_base_url': 'http://bob:345/serial/',
            'enable_serial_console': True}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_trigger_remote_restart(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.trigger_remote_restart(restart_key='akey')
        expect = {'restart_trigger': 'akey'}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_trigger_remote_restart_gen_key(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.trigger_remote_restart()
        expect = {'restart_trigger': mock.ANY}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_set_region(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_region('Region12')
        expect = {'region': 'Region12'}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_set_volume_data(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_volume_data('http://volhost')
        expect = {'volume_service': 'http://volhost'}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_set_ec2_data(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.ncr._relations = [mock_rel1, mock_rel2]
        self.ncr.set_ec2_data('http://ec2host')
        expect = {'ec2_host': 'http://ec2host'}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_collect_ssh_keys_single_relation(self):
        unit1_data = {
            'hostname': 'juju-4665be-20180716142533-9',
            'private-address': '10.5.0.17',
            'nova_ssh_public_key': 'unit1 nova pub key',
            'ssh_public_key': 'unit1 pub key'}
        mock_unit1 = _unit_mock(unit_name='unit1', received=unit1_data)
        mock_rel1 = _relation_mock(
            application_name='nova-compute',
            units=[mock_unit1])
        self.ncr._relations = [mock_rel1]
        expect = {'nova-compute': {'unit1': {
            'hostname': 'juju-4665be-20180716142533-9',
            'nova_ssh_pub_key': 'unit1 nova pub key',
            'private-address': '10.5.0.17',
            'ssh_pub_key': 'unit1 pub key'}}}
        self.assertEqual(self.ncr.collect_ssh_keys(), expect)

    def test_collect_ssh_keys_single_relation_set_app_name(self):
        unit1_data = {
            'hostname': 'juju-4665be-20180716142533-9',
            'private-address': '10.5.0.17',
            'nova_ssh_public_key': 'unit1 nova pub key',
            'ssh_public_key': 'unit1 pub key'}
        mock_unit1 = _unit_mock(unit_name='unit1', received=unit1_data)
        mock_rel1 = _relation_mock(
            application_name='nova-compute',
            units=[mock_unit1])
        self.ncr._relations = [mock_rel1]
        expect = {'nova-compute': {'unit1': {
            'hostname': 'juju-4665be-20180716142533-9',
            'nova_ssh_pub_key': 'unit1 nova pub key',
            'private-address': '10.5.0.17',
            'ssh_pub_key': 'unit1 pub key'}}}
        self.assertEqual(
            self.ncr.collect_ssh_keys(application_name='nova-compute'),
            expect)

    def test_collect_ssh_keys_mutli_relation(self):
        unit1_data = {
            'hostname': 'juju-4665be-20180716142533-9',
            'private-address': '10.5.0.17',
            'nova_ssh_public_key': 'unit1 nova pub key',
            'ssh_public_key': 'unit1 pub key'}
        unit2_data = {
            'hostname': 'juju-4665be-20180716142533-8',
            'private-address': '10.5.0.16',
            'nova_ssh_public_key': 'unit2 nova pub key',
            'ssh_public_key': 'unit2 pub key'}
        mock_unit1 = _unit_mock(unit_name='unit1', received=unit1_data)
        mock_unit2 = _unit_mock(unit_name='unit2', received=unit2_data)
        mock_rel1 = _relation_mock(
            application_name='nova-compute',
            units=[mock_unit1])
        mock_rel2 = _relation_mock(
            application_name='nova-compute-cell3',
            units=[mock_unit2])
        self.ncr._relations = [mock_rel1, mock_rel2]
        expect = {
            'nova-compute': {
                'unit1': {
                    'hostname': 'juju-4665be-20180716142533-9',
                    'nova_ssh_pub_key': 'unit1 nova pub key',
                    'private-address': '10.5.0.17',
                    'ssh_pub_key': 'unit1 pub key'}},
            'nova-compute-cell3': {
                'unit2': {
                    'hostname': 'juju-4665be-20180716142533-8',
                    'nova_ssh_pub_key': 'unit2 nova pub key',
                    'private-address': '10.5.0.16',
                    'ssh_pub_key': 'unit2 pub key'}}}
        self.assertEqual(
            self.ncr.collect_ssh_keys(),
            expect)

    def test_collect_ssh_keys_mutli_relation_app_name(self):
        unit1_data = {
            'hostname': 'juju-4665be-20180716142533-9',
            'private-address': '10.5.0.17',
            'nova_ssh_public_key': 'unit1 nova pub key',
            'ssh_public_key': 'unit1 pub key'}
        unit2_data = {
            'hostname': 'juju-4665be-20180716142533-8',
            'private-address': '10.5.0.16',
            'nova_ssh_public_key': 'unit2 nova pub key',
            'ssh_public_key': 'unit2 pub key'}
        mock_unit1 = _unit_mock(unit_name='unit1', received=unit1_data)
        mock_unit2 = _unit_mock(unit_name='unit2', received=unit2_data)
        mock_rel1 = _relation_mock(
            application_name='nova-compute',
            units=[mock_unit1])
        mock_rel2 = _relation_mock(
            application_name='nova-compute-cell3',
            units=[mock_unit2])
        self.ncr._relations = [mock_rel1, mock_rel2]
        expect = {
            'nova-compute': {
                'unit1': {
                    'hostname': 'juju-4665be-20180716142533-9',
                    'nova_ssh_pub_key': 'unit1 nova pub key',
                    'private-address': '10.5.0.17',
                    'ssh_pub_key': 'unit1 pub key'}}}
        self.assertEqual(
            self.ncr.collect_ssh_keys(application_name='nova-compute'),
            expect)

    def test_send_ssh_keys(self):
        mock_rel1 = _relation_mock()
        self.ncr.send_ssh_keys(mock_rel1, {'key1': 'k1', 'key2': 'k2'})
        self.assertEqual(
            mock_rel1.to_publish_raw,
            {'key1': 'k1', 'key2': 'k2'})
