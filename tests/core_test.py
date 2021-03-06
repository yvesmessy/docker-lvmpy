import os
import time
from multiprocessing import Process

import mock
import pytest

from core import (
    create, remove, volumes, LvmPyError,
    mount, path, unmount,
    get as get_volume,
    device_users,
    file_users,
    mountpoint_users,
    physical_volume_from_group,
    volume_mountpoint
)

FIRST_VOLUME_NAME = 'vol-a'
SECOND_VOLUME_NAME = 'vol_b'


def test_create_remove(vg):
    create(FIRST_VOLUME_NAME, '250m')
    create(SECOND_VOLUME_NAME, '300M')

    lvs = volumes()
    assert FIRST_VOLUME_NAME in lvs
    assert SECOND_VOLUME_NAME in lvs

    with pytest.raises(LvmPyError):
        create(FIRST_VOLUME_NAME, '250m')

    remove(FIRST_VOLUME_NAME)
    remove(SECOND_VOLUME_NAME)

    lvs = volumes()
    assert FIRST_VOLUME_NAME not in lvs
    assert SECOND_VOLUME_NAME not in lvs
    assert not os.path.isdir(volume_mountpoint(FIRST_VOLUME_NAME))
    assert not os.path.isdir(volume_mountpoint(SECOND_VOLUME_NAME))


def test_remove_not_existing(vg):
    def timeouts_mock(retries):
        return [1 for _ in range(retries)]
    with mock.patch('core.compose_exponantional_timeouts', timeouts_mock):
        with pytest.raises(LvmPyError):
            remove('Not-existing-volume')


def test_create_small_size(vg):
    with pytest.raises(LvmPyError):
        create(FIRST_VOLUME_NAME, '1m')


def test_get_volume(vg):
    create(FIRST_VOLUME_NAME, '250m')

    name = get_volume(FIRST_VOLUME_NAME)
    assert name == FIRST_VOLUME_NAME
    assert get_volume('Not-existing-volume') is None

    remove(FIRST_VOLUME_NAME)


def test_mount_unmount(vg):
    create(FIRST_VOLUME_NAME, '250m')

    mount(FIRST_VOLUME_NAME)

    mountpoint = path(FIRST_VOLUME_NAME)
    assert mountpoint == '/dev/mapper/schains-vol--a'

    unmount(FIRST_VOLUME_NAME)
    with pytest.raises(LvmPyError):
        path(FIRST_VOLUME_NAME)

    remove(FIRST_VOLUME_NAME)


def aquire_volume(volume_name):
    timeout_before_unmount = 20
    mount(volume_name)
    volume_filename = os.path.join(
        volume_mountpoint(volume_name),
        'test'
    )
    with open(volume_filename, 'w'):
        time.sleep(timeout_before_unmount)
    unmount(volume_name)


def test_device_users(vg):
    create(FIRST_VOLUME_NAME, '250m')

    p = Process(target=aquire_volume, args=(FIRST_VOLUME_NAME,))
    p.start()
    time.sleep(10)
    device_consumers_running = device_users(FIRST_VOLUME_NAME)
    p.join()
    device_consumers_finished = device_users(FIRST_VOLUME_NAME)
    remove(FIRST_VOLUME_NAME)

    assert isinstance(device_consumers_running, list)
    assert device_consumers_finished == []


def test_mountpoint_users(vg):
    create(SECOND_VOLUME_NAME, '250m')

    p = Process(target=aquire_volume, args=(SECOND_VOLUME_NAME,))
    p.start()
    time.sleep(3)
    mountpoint_consumers_running = mountpoint_users(SECOND_VOLUME_NAME)
    p.join()
    mountpoint_consumers_finished = mountpoint_users(SECOND_VOLUME_NAME)
    remove(SECOND_VOLUME_NAME)

    assert isinstance(mountpoint_consumers_running, list)
    assert mountpoint_consumers_finished == []


def test_file_users(vg):
    create(SECOND_VOLUME_NAME, '250m')

    p = Process(target=aquire_volume, args=(SECOND_VOLUME_NAME,))
    p.start()
    time.sleep(3)
    file_consumers_running = file_users(SECOND_VOLUME_NAME)
    p.join()
    file_consumers_finished = file_users(SECOND_VOLUME_NAME)
    remove(SECOND_VOLUME_NAME)

    assert isinstance(file_consumers_running, list)
    assert file_consumers_finished == []


def test_physical_volume_from_group(pv, vg) -> str:
    block_device = physical_volume_from_group(vg)
    assert block_device == pv
    block_device = physical_volume_from_group('not-existing-vg')
    assert block_device is None
