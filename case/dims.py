"""Every dimension of the DaysSince case, in millimetres.

Front view convention: the sign as read on the whiteboard — two portrait
panels side by side (left = tens, right = ones), a "stack zone" strip below
them housing the Pi Zero + PiSugar stack, the 16 mm button, the LED window
and the reset pinhole. Origin is the top-left corner of the plate outline,
+y is down.

Values marked UNVERIFIED are datasheet/eyeball placeholders — replace with
caliper measurements (measure BOTH panel modules; the active-area-to-
mounting-hole offsets are rev-dependent and the critical dims).
"""

# ---------------------------------------------------------------- material
THICKNESS = 3.2            # UNVERIFIED — caliper the actual draftboard sheet
KERF = 0.18                # draftboard starting point; tune after first cut
SHEET_W, SHEET_H = 495.0, 279.0   # usable Glowforge bed

# ------------------------------------------------------------ front stack
# 1 = opaque plate with open bezel windows (original design)
# 2 = full-face Green Glass cover laminated over the windowed mask plate
FRONT_LAYERS = 2           # generate both; decide when the Green Glass is seen
# True once the button bushing is confirmed to span both front layers
# (~6.4 mm); False = cover gets a big clearance hole, button grabs mask only.
BUTTON_SPANS_BOTH_LAYERS = False   # UNVERIFIED — measure usable thread length

# ------------------------------------------------- panels (portrait, each)
# Waveshare 4.2" B rev 2.2, PCB rotated 90° so native 103.0 x 78.5 stands up.
PANEL_PCB_W = 78.5         # UNVERIFIED
PANEL_PCB_H = 103.0        # UNVERIFIED
PANEL_HOLE_INSET = 2.75    # UNVERIFIED — mounting hole centre from PCB edges
PANEL_HOLE_DIA = 3.0       # board hole; case uses M3 clearance below

ACTIVE_W = 63.6            # UNVERIFIED — active area, portrait
ACTIVE_H = 84.8            # UNVERIFIED
# Active-area centre offset from PCB centre, portrait front view (+x right,
# +y down). The FPC/driver border makes this non-zero on the real module.
ACTIVE_OFFSET_X = 0.0      # UNVERIFIED — the critical measurement
ACTIVE_OFFSET_Y = 0.0      # UNVERIFIED — the critical measurement

GLASS_W = 77.0             # UNVERIFIED — raw glass outline, portrait
GLASS_H = 91.0             # UNVERIFIED
GLASS_OFFSET_X = 0.0       # UNVERIFIED — glass centre offset from PCB centre
GLASS_OFFSET_Y = 0.0       # UNVERIFIED

WINDOW_MARGIN = 0.75       # window = active area + this per side (alignment
                           # slack; bezel still overlaps the glass edges)

# ------------------------------------------------------------- case layout
PANEL_GAP = 3.0            # between the two PCB edges
PANEL_MARGIN = 3.0         # PCB to inner wall face (sides + top)
ZONE_GAP = 3.0             # panel PCB bottoms to stack zone top
STACK_ZONE_H = 38.0        # strip below the panels: Pi stack, battery, button
BOTTOM_MARGIN = 3.0        # stack zone to inner bottom wall face
CORNER_RADIUS = 4.0

# ------------------------------------------------------------ pi + pisugar
PI_W, PI_H = 65.0, 30.0    # Zero footprint, mounted long-side horizontal
PI_HOLE_GRID_W = 58.0      # standard Zero M2.5 grid
PI_HOLE_GRID_H = 23.0
# Stack position: left edge from cavity left, centred vertically in the zone
PI_ZONE_LEFT = 8.0         # UNVERIFIED — placed to keep clear of the button
# Sandwich orientation: battery side forward, Pi header + screen-wire
# housings toward the back plate. The PiSugar's USB-C / buttons / LEDs all
# live on ONE board edge; that edge faces the BOTTOM WALL, so USB access,
# LED glow and the reset pinhole are wall features (below), not front-plate
# features. The battery pouch covers the LEDs from the front when mounted.

# ---------------------------------------------- battery (magnetic pouch)
# MEASURED 2026-07-07: sandwich is 35 deep with the battery on its magnetic
# mount, 23 without (battery face → wire clearance, both incl. clearance).
# 35 would mean a ~51mm assembled case, so the pouch comes off the mount
# and lies flat beside the Pi. Needs retention in its pocket (foam tape or
# a glued steel washer for the pouch's own magnets) + confirm JST lead
# reach; never pinch the pouch.
BATTERY_BESIDE_STACK = True
BATTERY_W = 50.0           # UNVERIFIED — pouch footprint when laid flat
BATTERY_H = 34.0           # UNVERIFIED
BATTERY_GAP = 4.0          # clearance between Pi PCB edge and pouch

# --------------------------------------------------------------- fasteners
M3_CLEAR = 3.4
M25_CLEAR = 2.8
SCREW_HEAD_CLEAR = 6.5     # pass-through for M3/M2.5 heads in the magnet layer

# ------------------------------------------------------------------ button
BUTTON_HOLE = 16.2         # 16 mm threaded bushing + slip
BUTTON_BODY_DIA = 20.0     # keep-out behind the plate (body + solder lugs)
BUTTON_COVER_CLEAR = 18.0  # cover hole when the bushing can't span both layers
# Button centre, from cavity RIGHT edge / zone vertical centre
BUTTON_FROM_RIGHT = 18.0

# ------------------------------------------------------------------- walls
INTERNAL_DEPTH = 24.0      # MEASURED 2026-07-07: batteryless sandwich is
                           # 23.0 incl. wire clearance; +1 breathing room
TAB_W = 12.0
TAB_SLOT_CLEAR = 0.3       # per slot, on top of kerf; locate-only fit
# Bottom-wall features (the PiSugar's USB/button/LED edge faces this wall;
# offsets along the wall are from the Pi stack centre, case x)
USB_CUT_W = 11.0           # PiSugar USB-C
USB_CUT_H = 5.5
USB_FROM_FRONT = 10.0      # UNVERIFIED — connector depth behind front face
USB_OFFSET_X = 0.0         # UNVERIFIED
LED_SLOT_W = 24.0          # UNVERIFIED — glow slot; must span the 4 green
LED_SLOT_H = 3.0           #   + the blue power LED
LED_OFFSET_X = -22.0       # UNVERIFIED — slot centre from stack centre
LED_FROM_FRONT = 10.0      # UNVERIFIED — board-plane depth
RESET_PINHOLE_DIA = 1.8    # side-actuated reset button on the same edge
RESET_OFFSET_X = 18.0      # UNVERIFIED
RESET_FROM_FRONT = 10.0    # UNVERIFIED

# ----------------------------------------------------------------- magnets
MAGNET_DIA = 32.0          # LOVIMAG 32 x 3 discs, flush in 3.2 mm sheet
MAGNET_POCKET_SLIP = 0.3   # pocket diameter over magnet diameter
MAGNET_INSET_X = 22.0      # pocket centre from outline corners
MAGNET_INSET_Y = 22.0      # bottom pair auto-avoids the stack zone (see gen)
