# type: ignore
#!/usr/bin/env python3
"""
NVIDIA Driver Patcher
Removes artificial restrictions on mining/compute GPUs
Based on keylase/nvidia-patch
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nvidia-patch/nvp.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BLACKLISTED_DEVICES: Dict[int, str] = {
    0x15C2: 'GP100 [CMP 100-100]',
    0x1B07: 'GP102 [P102-100]',
    0x1B87: 'GP104 [P104-100]',
    0x1BC7: 'GP104 [P104-101]',
    0x1C07: 'GP106 [P106-100]',
    0x1C09: 'GP106 [P106-090]',
    0x1D83: 'GV100 [CMP 100-200]',
    0x1D84: 'GV100 [CMP 100-210]',
    0x1DC1: 'GV100 [CMP 100-200]',
    0x1E09: 'TU102 [CMP 50HX]',
    0x1E49: 'TU104 [unknown CMP]',
    0x1EBC: 'TU104 [unknown CMP]',
    0x1EFC: 'TU117 [unknown CMP]',
    0x1F0B: 'TU106 [CMP 40HX]',
    0x2081: 'GA100',
    0x2082: 'GA100 [CMP 170HX]',
    0x2083: 'GA100 [unknown CMP]',
    0x20C2: 'GA100 [CMP 170HX]',
    0x2189: 'TU116 [CMP 30HX]',
    0x220D: 'GA102 [CMP 90HX]',
    0x224D: 'GA102 [unknown CMP]',
    0x248A: 'GA104 [CMP 70HX]',
    0x24CA: 'GA104 [unknown CMP]',
    0x250A: 'GA106 [unknown CMP]',
}

PATTERN_V1 = re.compile(
    b'(?:'
    + b'.[^\x00]\x00{10}\x07\x00{3}'
    + b')+'
    + b'('
    + b'|'.join(
        dev_id.to_bytes(2, 'little') + b'\x00{10}\x07\x00{3}'
        for dev_id in BLACKLISTED_DEVICES.keys()
    )
    + b')+'
    + b'(?:'
    + b'.[^\x00]\x00{10}\x07\x00{3}'
    + b')+'
)

PATTERN_V2 = re.compile(
    b'(?:'
    + b'.[^\x00]\x07\x00'
    + b')+'
    + b'('
    + b'|'.join(
        dev_id.to_bytes(2, 'little') + b'\x07\x00'
        for dev_id in BLACKLISTED_DEVICES.keys()
    )
    + b')+'
    + b'(?:'
    + b'.[^\x00]\x07\x00'
    + b')+'
)


def scan_and_patch(
    pattern: 're.Pattern[bytes]',
    pattern_name: str,
    flag_width: int,
    binary: bytearray,
    auto_yes: bool = False,
) -> bool:
    """
    Scan for restricted device IDs and patch them

    Args:
        pattern: Compiled regex pattern to search
        pattern_name: Human-readable pattern name
        flag_width: Width of each flag entry in bytes
        binary: Binary data to patch
        auto_yes: Skip confirmation prompt

    Returns:
        True if modifications were made, False otherwise
    """
    modified = False
    matches = list(pattern.finditer(binary))

    if not matches:
        logger.info(f'No {pattern_name} patterns found')
        return False

    for match in matches:
        logger.info(
            f'{pattern_name} match found - '
            f'start:0x{match.start():08X} '
            f'end:0x{match.end():08X} '
            f'len:{match.end() - match.start()}'
        )

        found_devices = []
        for i in range(match.start(), match.end(), flag_width):
            dev_id = int.from_bytes(binary[i : i + 2], 'little')
            device_name = BLACKLISTED_DEVICES.get(dev_id, 'Unknown')
            logger.info(f'  pos:0x{i:08X} dev:0x{dev_id:04X} {device_name}')
            found_devices.append((i, dev_id, device_name))

        if not auto_yes:
            response = input('\nPatch these devices? (Y/N): ').strip().upper()
            if response != 'Y':
                logger.info('Skipping patch for this match')
                continue

        for i, dev_id, device_name in found_devices:
            binary[i] = 0xFF
            binary[i + 1] = 0xFF
            logger.info(f'Patched 0x{dev_id:04X} ({device_name}) at 0x{i:08X}')

        modified = True

    return modified


def patch_nvidia_binary(filepath: Path, auto_yes: bool = False) -> bool:
    """
    Main patching function

    Args:
        filepath: Path to NVIDIA kernel object file
        auto_yes: Skip confirmation prompts

    Returns:
        True if successful, False otherwise
    """
    try:
        if not filepath.exists():
            logger.error(f'File not found: {filepath}')
            return False

        logger.info(f'Loading binary: {filepath}')
        binary = bytearray(filepath.read_bytes())
        original_size = len(binary)
        logger.info(f'Binary size: {original_size} bytes')

        modified = False

        if scan_and_patch(PATTERN_V1, 'sandbag_v1', 16, binary, auto_yes):
            logger.info('Applied v1 patches')
            modified = True

        if scan_and_patch(PATTERN_V2, 'sandbag_v2', 4, binary, auto_yes):
            logger.info('Applied v2 patches')
            modified = True

        if not modified:
            logger.info('No patches needed - file is clean or unsupported')
            return True

        filepath.write_bytes(binary)
        logger.info(f'Successfully patched: {filepath}')

        if len(binary) != original_size:
            logger.error('ERROR: Binary size changed after patching!')
            return False

        return True

    except PermissionError:
        logger.error(f'Permission denied: {filepath}')
        return False
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return False


def main() -> int:
    """Main entry point"""
    if len(sys.argv) < 2:
        logger.error('Usage: nvp.py <nvidia_binary_path>')
        return 1

    filepath = Path(sys.argv[1])
    auto_yes = os.environ.get('NVIDIA_PATCH_AUTO_YES', '').lower() in (
        '1',
        'yes',
        'true',
    )

    logger.info('=' * 60)
    logger.info('NVIDIA Driver Patcher')
    logger.info('=' * 60)

    success = patch_nvidia_binary(filepath, auto_yes)

    if success:
        logger.info('Patching completed successfully')
        return 0

    logger.error('Patching failed')
    return 1


if __name__ == '__main__':
    sys.exit(main())

