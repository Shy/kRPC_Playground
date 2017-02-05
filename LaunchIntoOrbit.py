import math
import time
import krpc

turn_start_altitude = 250
turn_end_altitude = 50000
target_altitude = 100000

conn = krpc.connect(name='Launch into orbit', address='192.168.0.3', rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel

# Set up streams for telemetry
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
stage_5_resources = vessel.resources_in_decouple_stage(stage=5, cumulative=False)
stage_4_resources = vessel.resources_in_decouple_stage(stage=4, cumulative=False)
stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)

srb_fuel5 = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
srb_fuel4 = conn.add_stream(stage_4_resources.amount, 'LiquidFuel')
srb_fuel3 = conn.add_stream(stage_3_resources.amount, 'LiquidFuel')

# Pre-launch setup
vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1.0

# Countdown...
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')

# Activate the first stage
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_roll = 0
vessel.auto_pilot.target_pitch_and_heading(90, 90)
# Main ascent loop
srbs3_separated = False
srbs4_separated = False
srbs5_separated = False
turn_angle = 0
while True:

    # Gravity turn
    if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
        frac = (altitude() - turn_start_altitude) / (turn_end_altitude - turn_start_altitude)
        new_turn_angle = frac * 90
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle

            vessel.auto_pilot.target_pitch_and_heading(90-turn_angle, 90)

    # Separate LRBs when finished
    if not srbs5_separated:
        if srb_fuel5() < 0.1:
            vessel.control.activate_next_stage()
            srbs5_separated = True
            print('Stage 5 LRBs separated at {}'.format(altitude()))
    if srbs5_separated and not srbs4_separated:
        if srb_fuel4() < 0.1:
            vessel.control.activate_next_stage()
            srbs4_separated = True
            print('Stage 4 LRBs separated at {}'.format(altitude()))
    if srbs4_separated and not srbs3_separated:
        if srb_fuel3() < 0.1:
            vessel.control.activate_next_stage()
            srbs3_separated = True
            print('Stage 3 LRBs separated at {}'.format(altitude()))

    # Decrease throttle when approaching target apoapsis
    if apoapsis() > target_altitude*0.9:
        print('Approaching target apoapsis at {}'.format(altitude()))
        break

# Disable engines when target apoapsis is reached
vessel.control.throttle = 0.25
while apoapsis() < target_altitude:
    pass
print('Target apoapsis reached at {}'.format(altitude()))
vessel.control.throttle = 0.0

# Wait until out of atmosphere
print('Coasting out of atmosphere at {}'.format(altitude()))
while altitude() < 70500:
    pass

# Plan circularization burn (using vis-viva equation)
print('Planning circularization burn at {}'.format(altitude()))
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu*((2./r)-(1./a1)))
v2 = math.sqrt(mu*((2./r)-(1./a2)))
delta_v = v2 - v1
node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

# Calculate burn time (using rocket equation)
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# Orientate ship
print('Orientating ship for circularization burn at {}'.format(altitude()))
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.control.rcs = True
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.wait()

# Wait until burn
print('Waiting until circularization burn at {}'.format(altitude()))
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)

# Execute burn
print('Ready to execute burn at {}'.format(altitude()))
time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2.) > 0:
    pass
print('Executing burn at {}'.format(altitude()))
vessel.control.throttle = 1.0
time.sleep(burn_time - 0.1)
print('Fine tuning at {}'.format(altitude()))
vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > 0:
    pass
vessel.control.throttle = 0.0
node.remove()

print('Launch complete')
