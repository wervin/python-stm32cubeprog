import os
import sys

from stm32cubeprog import CubeProgrammerApi, CubeProgrammerError

if __name__ == "__main__":
    path = os.path.join(os.path.expanduser('~'), "Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer")
    api = CubeProgrammerApi(path)
    stlinks = api.discover()

    if len(stlinks) != 1:
        sys.exit(-1)

    stlink = stlinks[0]
    print(f'STLink board: {stlink.board}')
    print(f'STLink firmware version: {stlink.firmware_version}')
    print(f'STLink serial number: {stlink.serial_number}')

    error = api.connect(stlink)
    if error != CubeProgrammerError.NONE:
        sys.exit(-1)
    
    target = api.info()
    api.disconnect()

    print(f'Device ID: {target.device_id}')
    print(f'Device name: {target.name}')
    print(f'Device revision ID: {target.revision_id}')
