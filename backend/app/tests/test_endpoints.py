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
    client = socketio.AsyncClient(logger=True, engineio_logger=True)

    client_sio_instance_sid = None # SID from client.sid property
    server_reported_sid_event = asyncio.Event()
    server_sid_for_client = None

    initial_sids_from_manager = manager.get_active_sids().copy() # Ensure it's a copy
    print(f"[Test Setup] Initial SIDs in manager: {initial_sids_from_manager}")

    @client.event
    async def connect():
        nonlocal client_sio_instance_sid
        client_sio_instance_sid = client.sid
        print(f"[Client Event] 'connect' event fired. Client instance SID: {client_sio_instance_sid}")

    @client.on('server_registered_sid')
    async def on_server_registered_sid(data):
        nonlocal server_sid_for_client
        server_sid_for_client = data['sid']
        print(f"[Client Event] 'server_registered_sid' received. Server says SID is: {server_sid_for_client}")
        server_reported_sid_event.set()

    @client.event
    async def connect_error(data):
        print(f"[Client Event] 'connect_error' event fired. Data: {data}")
        pytest.fail(f"Connection failed for SID registration test: {data}")

    try:
        await client.connect(live_server_url, socketio_path="ws", transports=['websocket'])

        # Wait for the client to connect and receive the server_registered_sid event
        await asyncio.wait_for(server_reported_sid_event.wait(), timeout=5.0)

        assert client.connected, f"Client not connected. State: {client.eio.state if client.eio else 'N/A'}"
        assert client_sio_instance_sid is not None, "Client SID (client.sid) was not set."
        assert server_sid_for_client is not None, "Server_reported_sid was not received/set."

        print(f"[Test Check] Client instance SID (client.sid): {client_sio_instance_sid}")
        print(f"[Test Check] SID reported by server event: {server_sid_for_client}")

        # Key diagnostic: are they the same?
        if client_sio_instance_sid != server_sid_for_client:
            print(f"WARNING: Client instance SID '{client_sio_instance_sid}' and server-reported SID '{server_sid_for_client}' MISMATCH!")
            # This is likely the core issue. The test should assert based on what the server *thinks* the SID is,
            # because that's what will be in the ConnectionManager.

        sids_in_manager_after_connect = manager.get_active_sids()
        print(f"[Test Check] SIDs in manager after connect: {sids_in_manager_after_connect}")

        # Assert that the SID *the server registered* is in the manager
        assert server_sid_for_client in sids_in_manager_after_connect, \
            f"Server-reported SID {server_sid_for_client} not found in manager. Active SIDs: {sids_in_manager_after_connect}"

        assert server_sid_for_client not in initial_sids_from_manager, \
            f"Server-reported SID {server_sid_for_client} was already in initial_sids."

    except asyncio.TimeoutError:
        details = "Timeout waiting for server_registered_sid event. "
        if not client.connected: details += "Client not connected. "
        if client_sio_instance_sid is None: details += "client.sid not set. "
        if server_sid_for_client is None: details += "server_sid_for_client not set. "
        pytest.fail(details)
    except Exception as e:
        pytest.fail(f"An exception occurred during SID registration test: {e}")
    finally:
        if client.connected:
            await client.disconnect()
        await asyncio.sleep(0.1)

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
    server_sid_for_client = None # Store server-acknowledged SID
    server_sid_event = asyncio.Event()

    unique_message_text = f"Echo test message - {uuid.uuid4()}"

    @client.event
    async def connect():
        connected_event.set() # Client instance connected

    @client.on('server_registered_sid')
    async def on_server_registered_sid(data):
        nonlocal server_sid_for_client
        server_sid_for_client = data['sid']
        server_sid_event.set()
        print(f"Echo Test: Server registered SID {server_sid_for_client} for client {client.sid}")


    @client.on("new_message")
    async def on_new_message(data):
        nonlocal server_sid_for_client
        # Wait until server_sid_for_client is known
        if not server_sid_event.is_set():
            print("Echo Test: new_message received before server_sid known, deferring check.")
            await server_sid_event.wait() # ensure server_sid_for_client is set

        print(f"Echo Test: Received new_message: {data}, expecting sender_sid: {server_sid_for_client}")
        if not data.get("is_ai", False) and \
           data.get("text") == unique_message_text and \
           data.get("sender_sid") == server_sid_for_client: # Use server_sid_for_client
            echo_received_event.set()

    try:
        await client.connect(live_server_url, socketio_path="ws", transports=['websocket'])
        await asyncio.wait_for(connected_event.wait(), timeout=5.0)
        await asyncio.wait_for(server_sid_event.wait(), timeout=5.0) # Ensure server SID is received
        assert client.connected
        assert server_sid_for_client is not None

        await client.emit("chat_message", {"text": unique_message_text})
        await asyncio.wait_for(echo_received_event.wait(), timeout=5.0)

        assert echo_received_event.is_set(), f"Backend did not send the correct echo message. Expected sender_sid {server_sid_for_client}."

    except asyncio.TimeoutError:
        details = "Timeout in echo test. "
        if not connected_event.is_set(): details += "Client not connected. "
        if not server_sid_event.is_set(): details += "Server SID not received. "
        if not echo_received_event.is_set(): details += "Echo not received. "
        pytest.fail(details)
    except Exception as e:
        pytest.fail(f"An exception occurred: {e}")
    finally:
        if client.connected:
            await client.disconnect()
        await asyncio.sleep(0.1)

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

    server_client1_sid = None
    client1_server_sid_event = asyncio.Event()

    @client1.event
    async def connect():
        client1_connected.set()

    @client1.on('server_registered_sid')
    async def on_client1_server_sid(data):
        nonlocal server_client1_sid
        server_client1_sid = data['sid']
        client1_server_sid_event.set()
        print(f"Broadcast Test: Server registered SID {server_client1_sid} for client1 {client1.sid}")

    @client2.event
    async def connect():
        client2_connected.set()

    @client2.on("new_message")
    async def client2_on_new_message(data):
        nonlocal server_client1_sid
        if not client1_server_sid_event.is_set():
            print("Broadcast Test: new_message for client2 received before client1's server_sid known.")
            await client1_server_sid_event.wait()

        if not data.get("is_ai") and \
           data.get("text") == message_text and \
           data.get("sender_sid") == server_client1_sid:
            client2_received_user_message.set()
        elif data.get("is_ai"):
            client2_received_ai_message.set()

    all_clients_setup = asyncio.Event()

    async def setup_clients():
        try:
            # Connect with forced websocket transport
            await client1.connect(live_server_url, socketio_path="ws", transports=['websocket'])
            await client2.connect(live_server_url, socketio_path="ws", transports=['websocket'])

            await asyncio.wait_for(client1_connected.wait(), timeout=5)
            await asyncio.wait_for(client2_connected.wait(), timeout=5)
            await asyncio.wait_for(client1_server_sid_event.wait(), timeout=5) # Ensure client1's server SID is received

            assert client1.connected and client2.connected
            assert server_client1_sid is not None, "Client1's server-acknowledged SID not set"
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

    # Events for when server_registered_sid is received by each client
    server_sid_received_events = [asyncio.Event() for _ in range(NUM_CLIENTS)]

    # Store client.sid (instance SID) - will be populated after connection
    client_instance_sids = [None] * NUM_CLIENTS
    # Store server-acknowledged SIDs
    server_sids = [None] * NUM_CLIENTS

    EXPECTED_MESSAGES_PER_CLIENT = 2 * NUM_CLIENTS
    received_message_counts = [0] * NUM_CLIENTS
    all_messages_received_events = [asyncio.Event() for _ in range(NUM_CLIENTS)]
    client_messages_text = [f"Msg from Client{i} {uuid.uuid4()}" for i in range(NUM_CLIENTS)]

    for i in range(NUM_CLIENTS):
        client = clients[i]

        # Note: The client's own 'connect' event handler seems unreliable in this specific multi-client test.
        # We will rely on 'server_registered_sid' as the primary indicator of successful connection and SID acquisition.
        # The client_instance_sids will be populated after server_sid_received_events is set.

        def create_server_registered_sid_handler(index):
            async def server_registered_sid_handler(data):
                server_sids[index] = data['sid']
                server_sid_received_events[index].set() # Indicates server SID is known
                print(f"Client {index} received server_registered_sid: {server_sids[index]}")
            return server_registered_sid_handler

        def create_connect_error_handler(index):
            async def connect_error_handler(data):
                pytest.fail(f"Client {index} connection error: {data}")
            return connect_error_handler

        def create_new_message_handler(index):
            async def on_new_message_handler(data):
                received_message_counts[index] += 1
                print(f"Client {index} (Server SID: {server_sids[index]}) received message: {data}. Count: {received_message_counts[index]}")
                assert "text" in data
                assert "is_ai" in data
                # Sender SID check: if it's not AI, it's an echo.
                # The sender_sid in data should be the server-acknowledged SID of the original sender.
                if not data.get("is_ai"):
                    original_sender_text = data.get("text")
                    original_sender_index = -1
                    for idx, text_to_find in enumerate(client_messages_text):
                        if text_to_find == original_sender_text:
                            original_sender_index = idx
                            break
                    assert original_sender_index != -1, "Could not find original sender index for echo"
                    assert data.get("sender_sid") == server_sids[original_sender_index], \
                        f"Echoed message sender SID {data.get('sender_sid')} does not match server SID {server_sids[original_sender_index]} for client {original_sender_index}"

                if received_message_counts[index] >= EXPECTED_MESSAGES_PER_CLIENT:
                    all_messages_received_events[index].set()
            return on_new_message_handler

        def create_error_handler(index):
            async def error_handler(data):
                 pytest.fail(f"Client {index} (Server SID: {server_sids[index]}) received server error: {data}")
            return error_handler

        # client.event(create_connect_handler(i)) # This was removed as connect event is unreliable here
        client.on('server_registered_sid')(create_server_registered_sid_handler(i))
        client.event(create_connect_error_handler(i))
        client.on("new_message")(create_new_message_handler(i))
        client.event(create_error_handler(i))

    connect_tasks = []
    for i in range(NUM_CLIENTS):
        # Force websocket transport
        connect_tasks.append(clients[i].connect(live_server_url, socketio_path="ws", transports=['websocket']))

    try:
        await asyncio.gather(*connect_tasks, return_exceptions=True)

        # Wait for all clients to have received their server_registered_sid
        for i in range(NUM_CLIENTS):
            await asyncio.wait_for(server_sid_received_events[i].wait(), timeout=10.0) # Increased timeout
            assert clients[i].connected, f"Client {i} failed to connect (state: {clients[i].eio.state if clients[i].eio else 'N/A'})."
            assert server_sids[i] is not None, f"Client {i} Server SID not set after server_registered_sid event."

            # Populate client_instance_sids after server confirms SID, as client.sid should be stable then
            client_instance_sids[i] = clients[i].sid
            if client_instance_sids[i] is None:
                print(f"ERROR: Client {i} client.sid is None even after server_registered_sid event.")
            elif client_instance_sids[i] != server_sids[i]:
                 print(f"Client {i} instance SID {client_instance_sids[i]} != Server SID {server_sids[i]} (WARNING)")

        print(f"All {NUM_CLIENTS} clients considered connected (server_registered_sid received). Server SIDs: {server_sids}")

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
            if not server_sid_received_events[i].is_set():
                details.append(f"Client{i} server SID event timeout (server_sid: {server_sids[i]})")
            elif not all_messages_received_events[i].is_set():
                 details.append(f"Client{i} msg timeout (got {received_message_counts[i]}/{EXPECTED_MESSAGES_PER_CLIENT}, server SID: {server_sids[i]})")
        if not details: details.append(f"Unknown timeout reason: {e}") # Add original error if no specific detail found
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
    client_connected_event = asyncio.Event()
    server_sid_of_client_to_disconnect = None
    client_server_sid_event = asyncio.Event()

    observer_client = socketio.AsyncClient(logger=True, engineio_logger=True)
    observer_connected_event = asyncio.Event()
    user_left_message_received = asyncio.Event()

    @client.event
    async def connect():
        client_connected_event.set()
        # client_sid_to_disconnect will be set by server_registered_sid event

    @client.on('server_registered_sid')
    async def on_client_server_sid(data):
        nonlocal server_sid_of_client_to_disconnect
        server_sid_of_client_to_disconnect = data['sid']
        client_server_sid_event.set()
        print(f"Disconnect Test: Server registered SID {server_sid_of_client_to_disconnect} for disconnecting client {client.sid}")

    @client.event
    async def disconnect():
        # This event uses client.sid, but server actions use server_sid_of_client_to_disconnect
        print(f"Disconnect Test: Client {client.sid} (Server SID: {server_sid_of_client_to_disconnect}) confirmed disconnection itself.")

    @observer_client.event
    async def connect():
        observer_connected_event.set()
        print("Disconnect test: Observer client connected.")

    # Observer doesn't need its own server_sid for this test's logic, but good to be aware of it.

    @observer_client.on("message")
    async def on_observer_message(data):
        nonlocal server_sid_of_client_to_disconnect
        # Wait for the SID of the disconnecting client to be known
        if not client_server_sid_event.is_set():
            await client_server_sid_event.wait()

        print(f"Disconnect test: Observer client received message: {data}, expecting user_left for SID: {server_sid_of_client_to_disconnect}")
        if data.get("type") == "status" and \
           server_sid_of_client_to_disconnect and \
           f"User {server_sid_of_client_to_disconnect} has left." in data.get("data", ""):
            user_left_message_received.set()

    try:
        # Connect with forced websocket transport
        await client.connect(live_server_url, socketio_path="ws", transports=['websocket'])
        await observer_client.connect(live_server_url, socketio_path="ws", transports=['websocket'])

        await asyncio.wait_for(client_connected_event.wait(), timeout=5)
        await asyncio.wait_for(observer_connected_event.wait(), timeout=5)
        await asyncio.wait_for(client_server_sid_event.wait(), timeout=5) # Crucial: wait for server SID

        assert client.connected
        assert observer_client.connected
        assert server_sid_of_client_to_disconnect is not None, "Server SID for client_to_disconnect was not set."

        initial_sids = manager.get_active_sids()
        assert server_sid_of_client_to_disconnect in initial_sids, \
            f"Client to disconnect (Server SID: {server_sid_of_client_to_disconnect}) was not registered in manager. Current manager SIDs: {initial_sids}"

        await client.disconnect() # This will trigger client's disconnect event and server's disconnect event

        # Wait for a short period for the server to process the disconnect
        # The disconnect event on the server should use the server_sid_of_client_to_disconnect
        await asyncio.sleep(1.0)

        sids_after_disconnect = manager.get_active_sids()
        assert server_sid_of_client_to_disconnect not in sids_after_disconnect, \
            f"Disconnected client (Server SID: {server_sid_of_client_to_disconnect}) still in manager. SIDs: {sids_after_disconnect}"

        await asyncio.wait_for(user_left_message_received.wait(), timeout=5)
        assert user_left_message_received.is_set(), "Observer client did not receive 'user has left' message for the correct SID."

    except asyncio.TimeoutError as e:
        details = []
        if not client_connected_event.is_set(): details.append("Client to disconnect connect timeout")
        if not observer_connected_event.is_set(): details.append("Observer client connect timeout")
        if not client_server_sid_event.is_set(): details.append("Server SID for disconnecting client not received")

        # Check manager only if server_sid_of_client_to_disconnect was set
        if server_sid_of_client_to_disconnect and server_sid_of_client_to_disconnect in manager.get_active_sids():
            details.append(f"Client {server_sid_of_client_to_disconnect} not removed from manager")
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
