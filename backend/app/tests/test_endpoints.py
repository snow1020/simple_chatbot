import pytest
import socketio
import asyncio
import uuid # Ensure uuid is imported
from fastapi.testclient import TestClient
from uvicorn.config import Config
from uvicorn.server import Server

# Assuming your FastAPI app and socket_app are in these locations
# Adjust imports based on your actual project structure
from app.main import app  # FastAPI app instance
from app.api.endpoints import sio, socket_app # socket_app is the ASGIApp for Socket.IO
from app.services.connection_manager import manager # Import the global manager instance

# Fixture to run the FastAPI/Uvicorn server in a separate thread
@pytest.fixture(scope="session")
def live_server_url():
    # Use a different port for testing to avoid conflicts
    TEST_SERVER_PORT = 8001
    server_url = f"http://localhost:{TEST_SERVER_PORT}"

    config = Config(app=app, host="localhost", port=TEST_SERVER_PORT, log_level="info")
    server = Server(config=config)

    import threading
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()

    import time
    time.sleep(1)

    yield server_url

@pytest.mark.asyncio
async def test_client_can_connect(live_server_url):
    '''Test that a client can successfully connect to the WebSocket server.'''
    client = socketio.AsyncClient()
    connected_event = asyncio.Event()

    @client.event
    async def connect():
        print("Test client connected to server.")
        connected_event.set()

    @client.event
    async def connect_error(data):
        print(f"Test client connection error: {data}")
        pytest.fail(f"Connection failed: {data}")

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        assert client.connected
    except asyncio.TimeoutError:
        pytest.fail("Client did not connect within timeout.")
    except Exception as e:
        pytest.fail(f"An exception occurred during connection: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_server_registers_connection(live_server_url):
    '''Test that the server registers the client connection in the ConnectionManager.'''
    client = socketio.AsyncClient()
    client_sid = None

    initial_sids = manager.get_active_sids().copy()

    @client.event
    async def connect():
        nonlocal client_sid
        client_sid = client.sid
        print(f"Test client connected with SID: {client_sid}")

    @client.event
    async def connect_error(data):
        pytest.fail(f"Connection failed for SID registration test: {data}")

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.sleep(0.5)

        assert client.connected
        assert client_sid is not None, "Client SID was not set on connect"

        current_sids = manager.get_active_sids()
        assert client_sid in current_sids, \
            f"Client SID {client_sid} not found in manager. Active SIDs: {current_sids}"
        assert client_sid not in initial_sids, \
            f"Client SID {client_sid} was already in initial_sids."

    except Exception as e:
        pytest.fail(f"An exception occurred during SID registration test: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_connection_stability_long_poll(live_server_url):
    '''Test that a connection remains stable for a short period.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    disconnected_event = asyncio.Event()
    error_occurred = False

    @client.event
    async def connect():
        print("Stability test client connected.")
        connected_event.set()

    @client.event
    async def disconnect():
        print("Stability test client disconnected.")
        disconnected_event.set()

    @client.event
    async def connect_error(data):
        nonlocal error_occurred
        print(f"Stability test connection error: {data}")
        error_occurred = True
        connected_event.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)

        if error_occurred:
            pytest.fail("Connection error occurred during stability test.")

        assert client.connected, "Client failed to connect for stability test."
        await asyncio.sleep(5)
        assert client.connected, "Client disconnected during the 5s waiting period."
        assert not disconnected_event.is_set(), "Client received disconnect event during wait period."

    except asyncio.TimeoutError:
        pytest.fail("Client did not connect within timeout for stability test.")
    except Exception as e:
        pytest.fail(f"An exception occurred during stability test: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_rapid_messages_stability(live_server_url):
    '''Test sending rapid messages and verify connection stability and processing.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    error_occurred = False
    NUM_MESSAGES = 5
    received_message_count = 0
    all_messages_received_event = asyncio.Event()

    @client.event
    async def connect():
        print("Rapid message test client connected.")
        connected_event.set()

    @client.event
    async def connect_error(data):
        nonlocal error_occurred
        print(f"Rapid message test connection error: {data}")
        error_occurred = True
        connected_event.set()

    @client.on("new_message")
    async def on_new_message(data):
        nonlocal received_message_count
        received_message_count += 1
        print(f"Rapid test received message: {data}")
        if received_message_count >= NUM_MESSAGES * 2:
            all_messages_received_event.set()

    @client.event
    async def error(data):
        nonlocal error_occurred
        print(f"Server sent error event: {data}")
        error_occurred = True

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)

        if error_occurred:
            pytest.fail("Connection error occurred during rapid message test.")
        assert client.connected, "Client failed to connect for rapid message test."

        send_tasks = []
        for i in range(NUM_MESSAGES):
            payload = {"text": f"Rapid message {i+1}"}
            send_tasks.append(client.emit("chat_message", payload))

        await asyncio.gather(*send_tasks, return_exceptions=True)
        await asyncio.wait_for(all_messages_received_event.wait(), timeout=10.0)

        assert received_message_count == NUM_MESSAGES * 2, \
            f"Expected {NUM_MESSAGES * 2} messages, but received {received_message_count}."
        assert client.connected, "Client disconnected during rapid message sending."
        assert not error_occurred, "An error event was received from the server or a connection error occurred."

    except asyncio.TimeoutError:
        if not all_messages_received_event.is_set():
             pytest.fail(f"Client did not receive all messages within timeout. Received {received_message_count} out of {NUM_MESSAGES * 2}.")
        else:
             pytest.fail("A timeout occurred during the rapid messages test, but not related to message receiving.")
    except Exception as e:
        pytest.fail(f"An exception occurred during rapid message test: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_send_message_received_by_backend(live_server_url):
    '''Test that a message sent by a client is received by the backend.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    message_processed_by_server = asyncio.Event()
    test_message_text = f"Test message {uuid.uuid4()}"

    @client.event
    async def connect():
        connected_event.set()

    @client.on("new_message")
    async def on_new_message(data):
        if not data.get("is_ai", False) and data.get("text") == test_message_text:
            message_processed_by_server.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        assert client.connected

        await client.emit("chat_message", {"text": test_message_text})
        await asyncio.wait_for(message_processed_by_server.wait(), timeout=5.0)

        assert message_processed_by_server.is_set(), "Server did not acknowledge message processing (e.g., via echo)."

    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for connection or server message processing.")
    except Exception as e:
        pytest.fail(f"An exception occurred: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_backend_echoes_message(live_server_url):
    '''Test that the backend echoes a received message back to the sending client.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    echo_received_event = asyncio.Event()

    unique_message_text = f"Echo test message - {uuid.uuid4()}"
    client_sid = None

    @client.event
    async def connect():
        nonlocal client_sid
        client_sid = client.sid
        connected_event.set()

    @client.on("new_message")
    async def on_new_message(data):
        if not data.get("is_ai", False) and \
           data.get("text") == unique_message_text and \
           data.get("sender_sid") == client_sid:
            echo_received_event.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        assert client.connected
        assert client_sid is not None

        await client.emit("chat_message", {"text": unique_message_text})
        await asyncio.wait_for(echo_received_event.wait(), timeout=5.0)

        assert echo_received_event.is_set(), "Backend did not send the correct echo message."

    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for connection or echo message.")
    except Exception as e:
        pytest.fail(f"An exception occurred: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_backend_sends_ai_response(live_server_url):
    '''Test that the backend sends a dummy AI response after a user message.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    ai_response_received_event = asyncio.Event()

    user_message_text = f"User message for AI - {uuid.uuid4()}"

    @client.event
    async def connect():
        connected_event.set()

    @client.on("new_message")
    async def on_new_message(data):
        if data.get("is_ai", False) and "text" in data:
            ai_response_received_event.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        assert client.connected

        await client.emit("chat_message", {"text": user_message_text})
        await asyncio.wait_for(ai_response_received_event.wait(), timeout=5.0)

        assert ai_response_received_event.is_set(), "Backend did not send an AI response."

    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for connection or AI response.")
    except Exception as e:
        pytest.fail(f"An exception occurred: {e}")
    finally:
        if client.connected:
            await client.disconnect()

@pytest.mark.asyncio
async def test_message_broadcast_to_other_clients(live_server_url):
    '''Test that messages (user echo and AI response) are broadcast to other connected clients.'''
    client1 = socketio.AsyncClient(logger=True, engineio_logger=True)
    client2 = socketio.AsyncClient(logger=True, engineio_logger=True)

    client1_connected = asyncio.Event()
    client2_connected = asyncio.Event()

    message_text = f"Broadcast test message - {uuid.uuid4()}"

    client2_received_user_message = asyncio.Event()
    client2_received_ai_message = asyncio.Event()
    client1_sid = None

    @client1.event
    async def connect():
        nonlocal client1_sid
        client1_sid = client1.sid
        client1_connected.set()

    @client2.event
    async def connect():
        client2_connected.set()

    @client2.on("new_message")
    async def client2_on_new_message(data):
        if not data.get("is_ai") and \
           data.get("text") == message_text and \
           data.get("sender_sid") == client1_sid:
            client2_received_user_message.set()
        elif data.get("is_ai"):
            client2_received_ai_message.set()

    all_clients_setup = asyncio.Event()

    async def setup_clients():
        try:
            await client1.connect(live_server_url, socketio_path="ws")
            await client2.connect(live_server_url, socketio_path="ws")
            await asyncio.wait_for(client1_connected.wait(), timeout=5)
            await asyncio.wait_for(client2_connected.wait(), timeout=5)
            assert client1.connected and client2.connected
            assert client1_sid is not None
            all_clients_setup.set()
        except Exception as e:
            print(f"Client setup failed: {e}")
            raise

    try:
        await asyncio.wait_for(setup_clients(), timeout=10)
        if not all_clients_setup.is_set():
             pytest.fail("One or more clients failed to connect or setup correctly.")

        await client1.emit("chat_message", {"text": message_text})

        await asyncio.wait_for(client2_received_user_message.wait(), timeout=5)
        await asyncio.wait_for(client2_received_ai_message.wait(), timeout=5)

        assert client2_received_user_message.is_set(), "Client2 did not receive the user message broadcast."
        assert client2_received_ai_message.is_set(), "Client2 did not receive the AI message broadcast."

    except asyncio.TimeoutError:
        details = []
        if not client1_connected.is_set(): details.append("Client1 not connected")
        if not client2_connected.is_set(): details.append("Client2 not connected")
        if all_clients_setup.is_set():
            if not client2_received_user_message.is_set(): details.append("Client2 user message timeout")
            if not client2_received_ai_message.is_set(): details.append("Client2 AI message timeout")
        if not details: details.append("Unknown timeout reason")
        pytest.fail(f"Timeout during broadcast test. Details: {'; '.join(details)}")
    except Exception as e:
        pytest.fail(f"An exception occurred during broadcast test: {e}")
    finally:
        if client1.connected:
            await client1.disconnect()
        if client2.connected:
            await client2.disconnect()

@pytest.mark.asyncio
async def test_multiple_clients_concurrent_interactions(live_server_url):
    '''Test concurrent connections and message interactions from multiple clients.'''
    NUM_CLIENTS = 3
    clients = [socketio.AsyncClient(logger=True, engineio_logger=True) for _ in range(NUM_CLIENTS)]

    connection_events = [asyncio.Event() for _ in range(NUM_CLIENTS)]
    sids = [None] * NUM_CLIENTS

    EXPECTED_MESSAGES_PER_CLIENT = 2 * NUM_CLIENTS

    received_message_counts = [0] * NUM_CLIENTS
    all_messages_received_events = [asyncio.Event() for _ in range(NUM_CLIENTS)]

    client_messages_text = [f"Msg from Client{i} {uuid.uuid4()}" for i in range(NUM_CLIENTS)]

    for i in range(NUM_CLIENTS):
        client = clients[i]

        def create_connect_handler(index):
            async def connect_handler():
                sids[index] = clients[index].sid
                connection_events[index].set()
                print(f"Client {index} connected with SID {sids[index]}")
            return connect_handler

        def create_connect_error_handler(index):
            async def connect_error_handler(data):
                pytest.fail(f"Client {index} connection error: {data}")
            return connect_error_handler

        def create_new_message_handler(index):
            async def on_new_message_handler(data):
                received_message_counts[index] += 1
                print(f"Client {index} (SID: {clients[index].sid}) received message: {data}. Count: {received_message_counts[index]}")
                assert "text" in data
                assert "is_ai" in data
                assert "sender_sid" in data
                if received_message_counts[index] >= EXPECTED_MESSAGES_PER_CLIENT:
                    all_messages_received_events[index].set()
            return on_new_message_handler

        def create_error_handler(index):
            async def error_handler(data):
                 pytest.fail(f"Client {index} received server error: {data}")
            return error_handler

        client.event(create_connect_handler(i))
        client.event(create_connect_error_handler(i))
        client.on("new_message")(create_new_message_handler(i))
        client.event(create_error_handler(i))

    connect_tasks = []
    for i in range(NUM_CLIENTS):
        connect_tasks.append(clients[i].connect(live_server_url, socketio_path="ws"))

    try:
        await asyncio.gather(*connect_tasks, return_exceptions=True)

        for i in range(NUM_CLIENTS):
            await asyncio.wait_for(connection_events[i].wait(), timeout=5.0)
            assert clients[i].connected, f"Client {i} failed to connect."
            assert sids[i] is not None, f"Client {i} SID not set."
        print(f"All {NUM_CLIENTS} clients connected. SIDs: {sids}")

        send_message_tasks = []
        for i in range(NUM_CLIENTS):
            send_message_tasks.append(
                clients[i].emit("chat_message", {"text": client_messages_text[i]})
            )
        await asyncio.gather(*send_message_tasks, return_exceptions=True)
        print(f"All {NUM_CLIENTS} clients sent their messages.")

        for i in range(NUM_CLIENTS):
            await asyncio.wait_for(all_messages_received_events[i].wait(), timeout=15.0)
            assert received_message_counts[i] == EXPECTED_MESSAGES_PER_CLIENT, \
                f"Client {i} expected {EXPECTED_MESSAGES_PER_CLIENT} messages, got {received_message_counts[i]}"

        print(f"All {NUM_CLIENTS} clients received the expected number of messages.")

    except asyncio.TimeoutError as e:
        details = []
        for i in range(NUM_CLIENTS):
            if not connection_events[i].is_set(): details.append(f"Client{i} connect timeout")
            elif not all_messages_received_events[i].is_set():
                 details.append(f"Client{i} msg timeout (got {received_message_counts[i]}/{EXPECTED_MESSAGES_PER_CLIENT})")
        if not details: details.append(f"Unknown timeout: {e}")
        pytest.fail(f"Timeout during multi-client test. Details: {'; '.join(details)}")
    except Exception as e:
        pytest.fail(f"An exception occurred during multi-client test: {e}")
    finally:
        disconnect_tasks = [client.disconnect() for client in clients if client.connected]
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        print(f"All {NUM_CLIENTS} clients disconnected.")

@pytest.mark.asyncio
async def test_graceful_disconnection(live_server_url):
    '''Test that the server handles client disconnection gracefully.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()

    client_sid_to_disconnect = None

    observer_client = socketio.AsyncClient(logger=True, engineio_logger=True)
    observer_connected = asyncio.Event()
    user_left_message_received = asyncio.Event()

    @client.event
    async def connect():
        nonlocal client_sid_to_disconnect
        client_sid_to_disconnect = client.sid
        connected_event.set()
        print(f"Disconnect test: Client to be disconnected is {client_sid_to_disconnect}")

    @client.event
    async def disconnect():
        print(f"Disconnect test: Client {client_sid_to_disconnect} confirmed disconnection itself.")

    @observer_client.event
    async def connect():
        observer_connected.set()
        print("Disconnect test: Observer client connected.")

    @observer_client.on("message")
    async def on_observer_message(data):
        nonlocal client_sid_to_disconnect
        print(f"Disconnect test: Observer client received message: {data}")
        if data.get("type") == "status" and f"User {client_sid_to_disconnect} has left." in data.get("data", ""):
            user_left_message_received.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await observer_client.connect(live_server_url, socketio_path="ws")

        await asyncio.wait_for(connected_event.wait(), timeout=5)
        await asyncio.wait_for(observer_connected.wait(), timeout=5)

        assert client.connected
        assert observer_client.connected
        assert client_sid_to_disconnect is not None

        initial_sids = manager.get_active_sids()
        assert client_sid_to_disconnect in initial_sids, "Client to disconnect was not registered in manager."

        await client.disconnect()
        await asyncio.sleep(1.0)

        sids_after_disconnect = manager.get_active_sids()
        assert client_sid_to_disconnect not in sids_after_disconnect, \
            f"Disconnected client SID {client_sid_to_disconnect} still in manager. SIDs: {sids_after_disconnect}"

        await asyncio.wait_for(user_left_message_received.wait(), timeout=5)
        assert user_left_message_received.is_set(), "Observer client did not receive 'user has left' message."

    except asyncio.TimeoutError as e:
        details = []
        if not connected_event.is_set(): details.append("Client to disconnect connect timeout")
        if not observer_connected.is_set(): details.append("Observer client connect timeout")
        # Check manager only if client_sid_to_disconnect was set
        if client_sid_to_disconnect and client.connected and client_sid_to_disconnect in manager.get_active_sids():
            details.append("Client not removed from manager")
        if not user_left_message_received.is_set(): details.append("User left message not received by observer")
        if not details: details.append(f"Unknown timeout: {e}")
        pytest.fail(f"Timeout during graceful disconnection test. Details: {'; '.join(details)}")
    except Exception as e:
        pytest.fail(f"An exception occurred during graceful disconnection test: {e}")
    finally:
        if client.connected:
            await client.disconnect()
        if observer_client.connected:
            await observer_client.disconnect()

@pytest.mark.asyncio
async def test_server_handles_invalid_message_format(live_server_url):
    '''Test that the server sends an error for invalid chat message format.'''
    client = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected_event = asyncio.Event()
    error_received_event = asyncio.Event()
    received_error_data = None

    @client.event
    async def connect():
        connected_event.set()

    @client.on("error")
    async def on_error(data):
        nonlocal received_error_data
        print(f"Invalid message test: Client received error: {data}")
        received_error_data = data
        error_received_event.set()

    try:
        await client.connect(live_server_url, socketio_path="ws")
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        assert client.connected

        invalid_payload = "just a string, not a dict"
        await client.emit("chat_message", invalid_payload)
        await asyncio.wait_for(error_received_event.wait(), timeout=5.0)

        assert error_received_event.is_set(), "Server did not send an error event for invalid message format."
        assert received_error_data is not None
        assert received_error_data.get("type") == "validation_error"
        assert "Invalid message format" in received_error_data.get("message", "")

    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for connection or server error response.")
    except Exception as e:
        pytest.fail(f"An exception occurred: {e}")
    finally:
        if client.connected:
            await client.disconnect()
