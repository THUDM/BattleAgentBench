from asyncio import StreamWriter, StreamReader, Queue

import json


class PlayerConnection(object):
    writer = None  # type: StreamWriter
    reader = None  # type: StreamReader
    buffer = b''
    action_queue = Queue()

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.writer = writer
        self.reader = reader

    async def read(self):
        buffer = await self.reader.readline()
        try:
            return json.loads(buffer)
        except json.JSONDecodeError:
            return None 

    async def write(self, data):
        writer = self.writer
        if writer is None:
            return
        raw_data = json.dumps(data, ensure_ascii=False).encode()
        writer.write(raw_data)
        writer.write(b'\n')
        await self.drain()

    async def drain(self):
        try:
            await self.writer.drain()
        except ConnectionError:
            self.writer = None

    async def write_ok(self, **kwargs):
        data = {'status': 'OK'}
        data.update(kwargs)
        await self.write(data)

    async def write_error(self, message):
        await self.write({'status': 'ERROR', 'message': message})

    async def write_reward(self, data):
        data['status'] = 'reward'
        await self.write(data)