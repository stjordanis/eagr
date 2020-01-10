# Copyright 2020-present Kensho Technologies, LLC.
"""Helpers for testing grpc clients"""
from concurrent import futures
from contextlib import contextmanager

import grpc


CONNECTION_MASK = "localhost:{}"
GRPC_GRACE_PERIOD = 1  # seconds


@contextmanager
def inprocess_grpc_server(servicer, servicer_add_function, num_threads=1):
    """Create an in-process grpc server for the servicer for testing purposes

    This should not be used anywhere in production.

    Sample usage:

        class MyServicer(foo_pb2_grpc.ServiceServicer):
            def bar(self, req, context):
                return Bar()

        with inprocess_grpc_server(
            MyServicer(), foo_pb2_grpc.add_ServiceServicer_to_server
        ) as address:
            client = make_grpc_client("", "", address, foo_pb2_grpc.ServiceStub)
            bar = client.bar()

    Args:
        servicer: a grpc servicer class derived from the base generated by the compiler
        servicer_add_function: generated function for adding a servicer to the server
        num_threads: optional number of threads to run. 1 by default

    Yields:
        a connection string for the client to open an insecure channel
    """
    grpc_server = None
    try:
        thread_pool = futures.ThreadPoolExecutor(max_workers=num_threads)
        grpc_server = grpc.server(thread_pool)
        grpc_address = CONNECTION_MASK.format(0)
        servicer_add_function(servicer, grpc_server)
        actual_port = grpc_server.add_insecure_port(grpc_address)
        actual_connection_address = CONNECTION_MASK.format(actual_port)
        grpc_server.start()
        yield actual_connection_address
    finally:
        if grpc_server:
            event = grpc_server.stop(GRPC_GRACE_PERIOD)
            event.wait(GRPC_GRACE_PERIOD)