import krpc, time
conn = krpc.connect(name='Sub Orbit', address='192.168.0.2', rpc_port=50000, stream_port=50001)

vessel = conn.space_center.active_vessel
vessel.auto_pilot.target_pitch_and_heading(90,90)
vessel.auto_pilot.engage()
vessel.control.throttle = 1
time.sleep(1)

print("Launch")
vessel.control.activate_next_stage()

while vessel.resources.amount('SolidFuel') > .1:
    time.sleep(1)
print("Booster separation")
vessel.control.activate_next_stage()

while vessel.flight().mean_altitude < 10000:
        time.sleep(1)
print('Gravity turn')
vessel.auto_pilot.target_pitch_and_heading(60,90)

while vessel.orbit.apoapsis_altitude < 100000:
    time.sleep(1)
print('Launch Stage Separation')
vessel.control.throttle = 0
time.sleep(1)
vessel.control.activate_next_stage()
vessel.auto_pilot.disengage()

while vessel.flight().surface_altitude > 1000:
    time.sleep(1)
vessel.control.activate_next_stage()

while vessel.flight(vessel.orbit.body.reference_frame).vertical_speed < -0.1:
    print('Altitude = %.1f meters' % vessel.flight().surface_altitude)
    time.sleep(1)
print('Landed!')

