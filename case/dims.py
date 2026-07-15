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
THICKNESS = 3.5            # MEASURED 2026-07-12 — draftboard (~3.5 everywhere).
                           # Red acrylic measured ~3.25 — split into
                           # per-material constants before the final acrylic cut.
KERF = 0.18                # draftboard starting point; tune after first cut
SHEET_W, SHEET_H = 495.0, 279.0   # usable Glowforge bed

# ------------------------------------------------------------ front stack
# 1 = opaque plate with open bezel windows (original design)
# 2 = full-face Green Glass cover laminated over the windowed mask plate
FRONT_LAYERS = 2           # generate both; decide when the Green Glass is seen
# Button mounts to the OUTER (cover) layer only — dry-fit 2026-07-15 showed
# the bushing's real usable thread is ~7 mm (not the bare-part 18), too short
# for both sheets. The mask gets a CAPTIVE HEX POCKET instead of a round
# hole: drop the nut (+ washer against the cover) into the pocket, stack the
# layers, and screw the button in from the FRONT — no fingers behind the
# plate, and the button stays serviceable without opening the case. With
# FRONT_LAYERS = 1 the mask is the only layer and gets the 16 mm hole itself.

# ------------------------------------------------- panels (portrait, each)
# Waveshare 4.2" B rev 2.2, PCB rotated 90° so native 103.0 x 78.5 stands up.
PANEL_PCB_W = 78.5         # MEASURED 2026-07-12 (both panels; matches wiki)
PANEL_PCB_H = 103.0        # MEASURED 2026-07-12
# Hole insets differ per axis (MEASURED 2026-07-12, far-to-far with 3.0 holes:
# 75.25 across the 78.5 side → 3.125; 100.0 along the 103 side → 3.0).
# Portrait: X = across the 78.5 mm width, Y = along the 103 mm height.
PANEL_HOLE_INSET_X = 3.125
PANEL_HOLE_INSET_Y = 3.0
PANEL_HOLE_DIA = 3.0       # board hole; case uses M3 clearance below

# Published active area (wiki). Measured visible white region is 65.5 x 87 =
# active + the ~1 mm border-electrode ring, so window (active + margin)
# lands almost exactly on the visible area — bezel hides the ring's edge.
ACTIVE_W = 63.6
ACTIVE_H = 84.8
# Active-area centre offset from PCB centre, portrait front view (+x right,
# +y down). MEASURED 2026-07-12 via visible-area margins: L 11.0 / R 2.0
# (sums exactly to 78.5), T/B symmetric 8.0/8.0. Orientation CONFIRMED:
# the wide 11 mm driver border is on the LEFT with the digits upright —
# mount both panels that way up.
ACTIVE_OFFSET_X = 4.5
ACTIVE_OFFSET_Y = 0.0

GLASS_W = 77.0             # published "screen only" outline 91 x 77 x 1.05
GLASS_H = 91.0
GLASS_OFFSET_X = 0.0       # assumed centred; clearance checks pass with room
GLASS_OFFSET_Y = 0.0

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
# Stack position: right edge from cavity right, centred vertically in the
# zone. Zone mirrored 2026-07-12 during first-article assembly: the battery's
# short JST lead only has slack to the LEFT of the PiSugar, so left→right the
# zone reads button, battery, Pi.
PI_ZONE_RIGHT = 8.0
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
BATTERY_W = 59.0           # MEASURED 2026-07-12 — squishy pouch, laid flat;
BATTERY_H = 30.0           # JST leads confirmed to reach from beside the Pi
BATTERY_GAP = 4.0          # clearance between Pi PCB edge and pouch
# Retention: a steel washer glued to the back plate (the pouch's own magnets
# grab it) + three glued rails boxing the pouch, open toward the Pi so the
# JST leads exit. Place rails with the pouch as the jig; never pinch it.
CORRAL_STRIP_W = 4.0
CORRAL_SLACK = 1.5         # rail-to-pouch slack per side

# --------------------------------------------------------------- fasteners
M3_CLEAR = 3.4
M25_CLEAR = 2.8
SCREW_HEAD_CLEAR = 6.5     # pass-through for M3/M2.5 heads in the magnet layer

# ------------------------------------------------------------------ button
BUTTON_HOLE = 16.2         # 16 mm threaded bushing + slip (cover layer)
BUTTON_BODY_DIA = 20.0     # keep-out behind the plate (body + solder lugs)
BUTTON_NUT_FLATS = 19.2    # MEASURED 2026-07-15 — hex nut 18.8 across flats
                           # (~21.5 across points, consistent) + 0.4 slip;
                           # the mask's hex pocket makes the nut captive
# Button centre, from cavity LEFT edge / zone vertical centre
BUTTON_FROM_LEFT = 18.0

# ------------------------------------------------------------------- walls
INTERNAL_DEPTH = 33.2      # DERIVED 2026-07-13 from the panel-clamp chain,
                           # which must sum exactly to the wall depth:
                           #   30 (20 F-F + 10 M-F standoffs combined)
                           # + 1.6 (panel PCB)
                           # + 1.6 (2 nylon washers — glass-float spacer)
                           # User's standoff kit is 5 mm increments; the Pi
                           # stack (28.2 tall) needs ≥ ~29.7, so 30 is the
                           # smallest workable standoff. Walls are the only
                           # pieces that depend on this value.
TAB_W = 12.0
TAB_SLOT_CLEAR = 0.3       # per slot, on top of kerf; locate-only fit
# Bottom-wall features (the PiSugar's USB/button/LED edge faces this wall;
# offsets along the wall are from the Pi stack centre, case x). Depths are
# measured from the BACK plate — the stack mounts on back-plate standoffs,
# so these numbers survive INTERNAL_DEPTH changes. generate.py converts to
# wall-local depth as INTERNAL_DEPTH - *_FROM_BACK.
# The port face sits ~5-6 mm inside the wall (stack centred in the zone) and
# a USB-C plug has only ~6.5 mm of metal, so the opening must admit the
# cable's plastic overmold through the wall: a NOTCH open to the front edge
# (the port centre is only 4.2 mm behind the front face — no room for a
# closed hole that tall). Sized for typical ≤13.5 x 7 overmolds; front mask
# covers the notch mouth.
USB_NOTCH_W = 16.0
USB_NOTCH_DEPTH = 10.5     # from the wall strip's front edge; must reach
                           # the port plane (INTERNAL_DEPTH - 26.8) + 3.5
                           # overmold half-height (run_checks enforces)
USB_FROM_BACK = 26.8       # MEASURED 2026-07-12 — back plate → USB-C centre:
                           # single standoff + one small standoff, clearing
                           # the F-M right-angle GPIO adapter on the straight
                           # header (soldered right-angle would allow 20.8)
USB_OFFSET_X = -21.25      # MEASURED 2026-07-13: board left end → port left
                           # edge 6.75, +4.5 (half of the ~9 connector) =
                           # centre 11.25 from the left end; 11.25 - 32.5.
# Battery-LED light bar (2026-07-15): a green-glass bar carries the four
# LEDs' light through the wall — green through green transmits, and light
# entering near a lit LED exits near it, so the 1-to-4 count survives. Cut
# from the Eco Glass sheet (3.0 thick, MEASURED 2026-07-15); friction-fits
# the wall slot, flush outside, stopping ~0.5 shy of the board edge. The
# LEDs span 43–53 from the board's left end (MEASURED 2026-07-13).
LED_BAR_W = 13.9           # sized to the as-cut wall's original 14-wide slot
                           # (generously covers the 10 mm LED row); future
                           # walls cut the pocket at bar + slip regardless
LED_BAR_LEN = 10.0         # wall 3.5 + board-edge gap 7.0 − 0.5
LED_BAR_T = 3.0            # sheet thickness = the bar's third dimension
LED_BAR_SLIP = 0.15        # slot over bar, per dimension
LED_OFFSET_X = 15.5        # span centre 48 - 32.5
LED_FROM_BACK = 26.8       # same board plane as the USB-C
# No reset pinhole: reset (and the onboard power/custom buttons) stay
# internal — the front arcade button clones power via pad 10.
# Power/charging light: on the board's RIGHT short edge, facing the right
# wall 8 mm away. 3.0 mm hole for a VCC LFB 3 mm press-fit light pipe
# (trim the TAIL to ~11-12 mm; the cut end faces the LED).
PWRLED_HOLE = 3.0
PWRLED_FROM_GPIO_EDGE = 9.25   # MEASURED 2026-07-13: GPIO-side (top) corner
                               # → LED near side 8.5, +~0.75 to centre
PWRLED_FROM_BACK = 26.8        # board plane, same as the bottom-edge features

# ----------------------------------------------------------------- magnets
# DECIDED 2026-07-13 (as built + magnet-test PASSED): the pocket layer glues
# DIRECTLY onto the back plate's outer face — magnets drop into the pockets
# (facing the whiteboard, ~flush) and bond to the back plate through them
# (E6000 fillet around each rim). Pockets carry the shear mechanically.
# History: through-plate grip failed the slide test 2026-07-12; a separate
# flat cover layer for the magnets to bond to was drawn but proved redundant
# once the layer was glued straight to the plate. Back-screw heads sink into
# the layer's 6.5 mm wells and stay driver-reachable; glue the layer on
# BEFORE the screws go in (wells give access after).
MAGNET_LAYER = True        # False = no pocket layer (magnets bare-glued)
MAGNET_DIA = 32.0          # LOVIMAG 32 x 3 discs, flush in 3.2 mm sheet
MAGNET_POCKET_SLIP = 0.3   # pocket diameter over magnet diameter
MAGNET_INSET_X = 22.0      # pocket centre from outline corners
MAGNET_INSET_Y = 22.0      # bottom pair auto-avoids the stack zone (see gen)
