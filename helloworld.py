import krpc
conn = krpc.connect(name='Remote example', address='192.168.0.2', rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel
print(vessel.name)