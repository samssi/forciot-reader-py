import sys
import time
import platform
import asyncio
import logging

from bleak import BleakClient

logger = logging.getLogger(__name__)

ADDRESS = (
    "DC:DA:66:34:CD:C2"
    if platform.system() != "Darwin"
    else "D6EDE002-EC04-4BD7-AE83-F16D77DBE7BD"
)
CHARACTERISTIC_UUID = '32de600a-93e8-412a-9e7e-48398bc7d5b3'
RUNTIME = 10000.0
MEASURE_FREQ = 0.5


async def run_ble_client(address: str, char_uuid: str, queue: asyncio.Queue):
    async def callback_handler(sender, data):
        await queue.put((time.time(), data))

    async with BleakClient(address) as client:
        logger.info(f"Connected: {client.is_connected}")
        await client.start_notify(char_uuid, callback_handler)
        await asyncio.sleep(RUNTIME)
        await client.stop_notify(char_uuid)
        await queue.put((time.time(), None))


async def run_queue_consumer(queue: asyncio.Queue):
    previous_time = 0
    while True:
        epoch, data = await queue.get()
        if data is None:
            logger.info('Disconnecting')
            break
        else:
            if epoch - previous_time > MEASURE_FREQ:
                previous_time = epoch
                handle2_bytes = bytes(data)
                int_values = [byte for byte in handle2_bytes]
                logger.info(f'{int_values}')
                with open('samples.txt', 'a') as file:
                    file.write(str(int_values)+'\n')


async def main(address: str, char_uuid: str):
    queue = asyncio.Queue()
    client_task = run_ble_client(address, char_uuid, queue)
    consumer_task = run_queue_consumer(queue)
    await asyncio.gather(client_task, consumer_task)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    asyncio.run(
        main(
            sys.argv[1] if len(sys.argv) > 1 else ADDRESS,
            sys.argv[2] if len(sys.argv) > 2 else CHARACTERISTIC_UUID,
        )
    )