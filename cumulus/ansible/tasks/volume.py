from cumulus.celery import command
from cumulus.ansible.tasks.inventory import simple_inventory

from cumulus.ansible.tasks.utils import run_playbook
from cumulus.ansible.tasks.utils import get_playbook_directory
from cumulus.ansible.tasks.utils import get_callback_plugins_path
from cumulus.ansible.tasks.utils import get_library_path

import os
from cumulus.ssh.tasks.key import _key_path

@command.task
def create_volume(profile, volume, secret_key, girder_callback_info):

    playbook = os.path.join(get_playbook_directory(),
                            'volumes', 'ec2', 'create.yml')

    extra_vars = {
        'girder_volume_id': volume['_id'],
        'profile_id': profile['_id'],
        'volume_name': volume['name'],
        'volume_size': volume['size'],
        'volume_zone': volume['zone'],
        'ansible_ssh_private_key_file': _key_path(profile)
    }
    extra_vars.update(girder_callback_info)

    env = os.environ.copy()
    env.update({'AWS_ACCESS_KEY_ID': profile['accessKeyId'],
                'AWS_SECRET_ACCESS_KEY': secret_key,
                'ANSIBLE_HOST_KEY_CHECKING': 'false',
                'ANSIBLE_CALLBACK_PLUGINS': get_callback_plugins_path(),
                'ANSIBLE_LIBRARY': get_library_path()})

    inventory = simple_inventory('localhost')

    with inventory.to_tempfile() as inventory_path:
        run_playbook(playbook, inventory_path,
                     extra_vars, verbose=3, env=env)


@command.task
def attach_volume(profile, cluster, instance, volume, path,
                  secret_key, girder_callback_info):

    playbook = os.path.join(get_playbook_directory(),
                            'volumes', 'ec2', 'attach.yml')

    extra_vars = {
        'girder_volume_id': volume['_id'],
        'girder_cluster_id': cluster['_id'],
        'region': profile['regionName'],
        'volume_id': volume['ec2']['id'],
        'instance_id': instance['instance_id'],
        'path': path,
        'ansible_ssh_private_key_file': _key_path(profile),
        'ansible_user': cluster['config']['ssh']['user']
    }

    extra_vars.update(girder_callback_info)

    env = os.environ.copy()
    env.update({'AWS_ACCESS_KEY_ID': profile['accessKeyId'],
                'AWS_SECRET_ACCESS_KEY': secret_key,
                'ANSIBLE_HOST_KEY_CHECKING': 'false',
                'ANSIBLE_CALLBACK_PLUGINS': get_callback_plugins_path(),
                'ANSIBLE_LIBRARY': get_library_path()})

    inventory = simple_inventory({'head': [instance['public_ip']]})

    with inventory.to_tempfile() as inventory_path:
        run_playbook(playbook, inventory_path,
                     extra_vars, verbose=2, env=env)


@command.task
def detatch_volume(profile, cluster, instance, volume,
                   secret_key, girder_callback_info):

    playbook = os.path.join(get_playbook_directory(),
                            'volumes', 'ec2', 'detach.yml')

    extra_vars = {
        'girder_volume_id': volume['_id'],
        'girder_cluster_id': cluster['_id'],
        'volume_id': volume['ec2']['id'],
        'instance_id': instance['instance_id'],
        'path': volume['ec2']['path'],
        'region': profile['regionName'],
        'ansible_ssh_private_key_file': _key_path(profile),
        'ansible_user': cluster['config']['ssh']['user']
    }

    extra_vars.update(girder_callback_info)

    env = os.environ.copy()
    env.update({'AWS_ACCESS_KEY_ID': profile['accessKeyId'],
                'AWS_SECRET_ACCESS_KEY': secret_key,
                'ANSIBLE_HOST_KEY_CHECKING': 'false',
                'ANSIBLE_CALLBACK_PLUGINS': get_callback_plugins_path(),
                'ANSIBLE_LIBRARY': get_library_path()})

    inventory = simple_inventory({'head': [instance['public_ip']]})

    with inventory.to_tempfile() as inventory_path:
        run_playbook(playbook, inventory_path,
                     extra_vars, verbose=2, env=env)


@command.task
def delete_volume(profile, volume, secret_key, girder_callback_info):

    playbook = os.path.join(get_playbook_directory(),
                            'volumes', 'ec2', 'delete.yml')

    extra_vars = {
        'girder_volume_id': volume['_id'],
        'volume_id': volume['ec2']['id'],
        'region': profile['regionName'],
        'ansible_ssh_private_key_file': _key_path(profile),
    }

    extra_vars.update(girder_callback_info)

    env = os.environ.copy()
    env.update({'AWS_ACCESS_KEY_ID': profile['accessKeyId'],
                'AWS_SECRET_ACCESS_KEY': secret_key,
                'ANSIBLE_HOST_KEY_CHECKING': 'false',
                'ANSIBLE_CALLBACK_PLUGINS': get_callback_plugins_path(),
                'ANSIBLE_LIBRARY': get_library_path()})

    inventory = simple_inventory('localhost')

    with inventory.to_tempfile() as inventory_path:
        run_playbook(playbook, inventory_path,
                     extra_vars, verbose=2, env=env)
