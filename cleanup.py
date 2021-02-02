import sys
from core import (
    physical_volumes,
    physical_volume_from_group,
    remove_physical_volume,
    remove_volume_group,
    volume_groups,
    volumes
)


def is_block_device_exist(block_device: str) -> bool:
    return block_device in physical_volumes()


def is_lvmpy_environment_valid(block_device: str, volume_group: str) -> bool:
    pv = physical_volume_from_group(volume_group)
    print('IVD', repr(block_device), repr(pv))
    lvs = volumes()
    return pv == block_device or lvs == []


def is_cleanup_needed(block_device: str, volume_group: str) -> bool:
    if volume_group not in volume_groups():
        return False
    if physical_volume_from_group(volume_group) == block_device:
        return False
    return True


def cleanup_lvmpy_aritifacts(volume_group: str) -> None:
    pv = physical_volume_from_group(volume_group)
    remove_volume_group(volume_group)
    remove_physical_volume(pv)


def main() -> None:
    block_device = sys.argv[1]
    volume_group = sys.argv[2]
    if not is_lvmpy_environment_valid(block_device, volume_group):
        print(
            'Lvmpy cannot be created. '
            f'Volume group {volume_group} exists with volumes',
            file=sys.stderr
        )
        exit(1)
    if is_cleanup_needed(block_device, volume_group):
        print('Cleaning lvmpy artifacts ...')
        cleanup_lvmpy_aritifacts(volume_group)
    print('Cleanup actions for lvmpy executed successfully')


if __name__ == '__main__':
    main()
