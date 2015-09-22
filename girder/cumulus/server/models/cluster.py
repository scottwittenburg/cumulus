import json
from jsonpath_rw import parse
from girder.models.model_base import ValidationException
from bson.objectid import ObjectId
from girder.constants import AccessType
from girder.api.rest import RestException
from .base import BaseModel
from cumulus.constants import ClusterType
from ..utility.cluster_adapters import get_cluster_adapter
from cumulus.common.girder import create_status_notifications, \
    check_group_membership
import cumulus


class Cluster(BaseModel):

    def __init__(self):
        super(Cluster, self).__init__()

    def initialize(self):
        self.name = 'clusters'

        self.exposeFields(level=AccessType.READ,
                          fields=('_id', 'status', 'name', 'config', 'template',
                                  'type'))

    def filter(self, cluster, user, passphrase=True):
        cluster = super(Cluster, self).filter(doc=cluster, user=user)

        if parse('config.ssh.passphrase').find(cluster) and passphrase:
            try:
                check_group_membership(user, cumulus.config.girder.group)
            except RestException:
                del cluster['config']['ssh']['passphrase']

        # Use json module to convert ObjectIds to strings
        cluster = json.loads(json.dumps(cluster, default=str))

        return cluster

    def validate(self, cluster):
        if not cluster['name']:
            raise ValidationException('Name must not be empty.', 'name')

        if not cluster['type']:
            raise ValidationException('Type must not be empty.', 'type')

        adapter = get_cluster_adapter(cluster)

        return adapter.validate()

    def _create(self, user, cluster):
        self.setUserAccess(cluster, user=user, level=AccessType.ADMIN)
        group = {
            '_id': ObjectId(self.get_group_id())
        }
        doc = self.setGroupAccess(cluster, group, level=AccessType.ADMIN)

        # Add userId field to indicate ownership
        doc['userId'] = user['_id']

        self.save(doc)

        return doc

    def create_ec2(self, user, config_id, name, template):
        cluster = {
            'name': name,
            'template': template,
            'log': [],
            'status': 'created',
            'config': {
                '_id': config_id
            },
            'type': ClusterType.EC2
        }

        return self._create(user, cluster)

    def create_traditional(self, user, name, hostname, username):
        cluster = {
            'name': name,
            'log': [],
            'status': 'creating',
            'config': {
                'host': hostname,
                'ssh': {
                    'user': username
                }
            },
            'type': ClusterType.TRADITIONAL
        }

        return self._create(user, cluster)

    def add_log_record(self, user, id, record):
        # Load first to force access check
        self.load(id, user=user, level=AccessType.WRITE)
        self.update({'_id': ObjectId(id)}, {'$push': {'log': record}})

    def update_cluster(self, user, cluster):
        # Load first to force access check
        cluster_id = cluster['_id']
        current_cluster = self.load(cluster_id, user=user,
                                    level=AccessType.WRITE)

        # If the status has changed create a notification
        new_status = cluster['status']
        if current_cluster['status'] != new_status:
            notification = {
                '_id': cluster_id,
                'status': new_status
            }
            create_status_notifications('cluster', notification,
                                        current_cluster)

        return self.save(cluster)

    def log_records(self, user, id, offset=0):
        # TODO Need to figure out perms a remove this force
        cluster = self.load(id, user=user, level=AccessType.READ)

        return cluster['log'][offset:]

    def delete(self, user, id):
        cluster = self.load(id, user=user, level=AccessType.ADMIN)

        adapter = get_cluster_adapter(cluster)
        adapter.delete()

        self.remove(cluster)
