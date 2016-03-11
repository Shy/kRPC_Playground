import krpc
conn = krpc.connect(name='Navball directions', address='192.168.0.2', rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel
ap = vessel.auto_pilot
ap.reference_frame = vessel.surface_reference_frame
ap.engage()

# Point the vessel north on the navball, with a pitch of 0 degrees
ap.target_direction = (0,1,0)
ap.wait()

# Point the vessel vertically upwards on the navball
ap.target_direction = (1,0,0)
ap.wait()

# Point the vessel west (heading of 270 degrees), with a pitch of 0 degrees
ap.target_direction = (0,0,-1)
ap.wait()

ap.disengage()
