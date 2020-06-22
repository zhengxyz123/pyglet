import sys as _sys
import queue as _queue
import struct as _struct
import socket as _socket
import asyncio as _asyncio
import threading as _threading

from pyglet.event import EventDispatcher as _EventDispatcher


class _BaseConnection(_EventDispatcher):
    """Base class for threaded socket connections."""

    def __init__(self, socket, address):
        self._socket = socket
        self._address = address[0]
        self._port = address[1]
        self._terminate = _threading.Event()
        self._queue = _queue.Queue()
        _threading.Thread(target=self._recv, daemon=True).start()
        _threading.Thread(target=self._send, daemon=True).start()
        self._sentinal = object()  # poison pill

    def close(self, exception=None):
        """Close the connection."""
        self._queue.put(self._sentinal)
        self._socket.close()
        if not self._terminate.is_set():
            self._terminate.set()
            self.dispatch_event('on_disconnect', self, exception)

    def _recv(self):  # Thread
        socket = self._socket

        while not self._terminate.is_set():
            try:
                header = socket.recv(4)
                while len(header) < 4:
                    header += socket.recv(4)

                size = _struct.unpack('I', header)[0]

                message = socket.recv(size)
                while len(message) < size:
                    message += socket.recv(size)
                self.dispatch_event('on_receive', self, message)
            except BaseException:
                info = _sys.exc_info()
                self.close(info[1])
                break

    def send(self, message):
        """Queue a message to send.

        Put a string of bytes into the queue to send.
        raises a `ConnectionError` if the connection
        has been closed or dropped.

       :Parameters:
            `message` : bytes
                A string of bytes to send.
        """
        if self._terminate.is_set():
            raise ConnectionError("Connection is closed.")
        self._queue.put(message)

    def _send(self):  # Thread
        while not self._terminate.is_set():
            message = self._queue.get()
            if message == self._sentinal:  # bail out on poison pill
                break
            try:
                packet = _struct.pack('I', len(message)) + message
                self._socket.sendall(packet)
            except BaseException:
                info = _sys.exc_info()
                self.close(info[1])
                break

    def on_receive(self, connection, message):
        """Event for received messages."""

    def on_disconnect(self, connection, exception=None):
        """Event for disconnection. """

    def __repr__(self):
        return f"Connection(address={self._address}, port={self._port})"


_BaseConnection.register_event_type('on_receive')
_BaseConnection.register_event_type('on_disconnect')


class Client(_BaseConnection):
    def __init__(self, address, port):
        """Create a Client connection to a Server."""
        self._socket = _socket.create_connection((address, port))
        super().__init__(self._socket, address)

    def on_disconnect(self, connection, exception=None):
        """Default disconnection handler. Raises Exceptions, if any."""
        if exception:
            raise exception

    def __repr__(self):
        return f"Client(address={self._address}, port={self._port})"


class AsyncConnection(_EventDispatcher):

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self._closed = False
        self._loop = _asyncio.get_event_loop()
        _asyncio.run_coroutine_threadsafe(self._recv(), self._loop)

    def close(self):
        if not self._closed:
            self._writer.transport.close()
            self._closed = True
            self.dispatch_event('on_disconnect', self)

    async def _recv(self):
        while not self._closed:
            try:
                header = await self._reader.readexactly(4)
                size = _struct.unpack('I', header)[0]
                message = await self._reader.readexactly(size)
                self._loop.call_soon(self.dispatch_event, 'on_receive', self, message)

            except _asyncio.IncompleteReadError:
                self.close()
                break

    async def _send(self, message):
        try:
            packet = _struct.pack('I', len(message)) + message
            self._writer.write(packet)
            await self._writer.drain()
        except ConnectionResetError:
            self.close()

    def send(self, message):
        # Synchrounously send a message in a async coroutine.
        if self._writer.transport is None or self._writer.transport.is_closing():
            self.close()
            return
        _future = _asyncio.run_coroutine_threadsafe(self._send(message), self._loop)

    def on_receive(self, connection, message):
        """Event for received messages."""

    def on_disconnect(self, connection):
        """Event for disconnection. """

    def __del__(self):
        print("GC: ", self)


AsyncConnection.register_event_type('on_receive')
AsyncConnection.register_event_type('on_disconnect')


class AsyncServer(_EventDispatcher):

    def __init__(self, address, port):
        self._address = address
        self._port = port
        self._async_thread = _threading.Thread(target=_asyncio.run, args=(self._start_server(),), daemon=True)
        self._async_thread.start()

    async def handle_connection(self, reader, writer):
        connection = AsyncConnection(reader, writer)
        self.dispatch_event('on_connection', connection)

    async def _start_server(self):
        server = await _asyncio.start_server(self.handle_connection, self._address, self._port)
        async with server:
            await server.serve_forever()

    def on_connection(self, connection):
        """Event for new Connections received."""


AsyncServer.register_event_type('on_connection')


class Server(_EventDispatcher):

    def __init__(self, address, port, reuse_port=False):
        """Create a threaded socket server"""
        self._alive = _threading.Event()
        self._socket = _socket.create_server((address, port), reuse_port=reuse_port)
        self._recv_thread = _threading.Thread(target=self._receive_connections, daemon=True)
        self._recv_thread.start()

    def close(self):
        self._alive.set()
        self._socket.close()

    def _receive_connections(self):  # Thread
        while not self._alive.is_set():
            try:
                new_socket, address = self._socket.accept()
                connection = _BaseConnection(new_socket, address)
                self.dispatch_event('on_connection', connection)
            except (BrokenPipeError, OSError):
                self._alive.set()
        self.dispatch_event('on_disconnect')

    def on_connection(self, connection):
        """Event for new Connections received."""


Server.register_event_type('on_connection')
