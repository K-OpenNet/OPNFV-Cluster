# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import six

from tacker.common import exceptions
from tacker.services import service_base


@six.add_metaclass(abc.ABCMeta)
class VnfClusterPluginBase(service_base.NFVPluginBase):

    @abc.abstractmethod
    def create_cluster(self, context, cluster_config):
        pass

    @abc.abstractmethod
    def delete_cluster(self, context, cluster_id):
        pass

    @abc.abstractmethod
    def get_cluster(self, context, cluster_id, fields=None):
        pass

    @abc.abstractmethod
    def get_clusters(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_clustermember(self, context, clustermember):
        pass

    @abc.abstractmethod
    def get_clustermembers(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_clustermember(self, context, clustermember_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_clustermember(self, context, clustermember_id):
        pass


class VnfClusterNotFound(exceptions.NotFound):
    message = ('VnfCluster %(cluster_id)s could not be found')


class VnfClusterMemberNotFound(exceptions.NotFound):
    message = ('VnfClusterMember %(cluster_member_id)s could not be found')


class VnfClusterMemberRoleNotFound(exceptions.NotFound):
    message = ('VnfClusterMember with role: '
               '%(member_role)s could not be found')
