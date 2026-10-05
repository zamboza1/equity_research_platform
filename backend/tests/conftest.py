import os
import socket
import pytest
os.environ['VERTIGE_OFFLINE']='1'
os.environ['HF_HUB_OFFLINE']='1'
@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a,**k):raise AssertionError('Network forbidden in tests')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket,'create_connection',blocked)
