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
KERF = 0.27                # CALIBRATED 2026-07-15 — draftboard: the 3.2-drawn
                           # test rod finished 3.11 (0.09 under) at KERF 0.18,
                           # so real kerf ≈ 0.27. This tightened the loose
                           # LED-bar/USB fits. NB acrylic kerf differs — re-
                           # calibrate for the black-acrylic walls.
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
INTERNAL_DEPTH = 35.0      # EMPIRICAL — 34.0 no grip, 34.5 held but a light
                           # tap dislodged it, LEDs at the rightmost aren't
                           # crowding the button; user jumped to 35.0 for a
                           # firm press. Walls drawn uncompensated finish
                           # ~kerf small; the back plate absorbs the ~1.3
                           # excess over the ~33.7 gap (screens stay clamped).
                           # Safe: the combined standoff is threaded BOTH ends,
                           # so the screen clamp is a self-contained FRONT joint
                           # (front screw → plate → washers → PCB → standoff
                           # front face); excess wall pushes the BACK PLATE a
                           # hair proud (back screw bridges it), screens stay
                           # clamped. Keep overshoot ≲2. If still loose, → 35.
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
# CLOSED hole again (2026-07-15) — the deeper 34.0 cavity puts the port
# 7.2 back from the front, leaving a ~2.7 mm bridge to the front edge, so
# the head no longer needs the front-edge notch it did at 31 mm depth.
# Sized to the MEASURED magnetic cable head: 13 wide (along the wall length)
# x 8.25 tall (front-to-back into the case).
USB_HOLE_W = 14.5          # head 13 + 0.75/side
USB_HOLE_H = 9.0           # head 8.25 + 0.375/side; centred at the port plane
                           # (INTERNAL_DEPTH - USB_FROM_BACK); run_checks keeps
                           # a ≥2 mm bridge to the front edge (else use a notch)
USB_FROM_BACK = 25.8       # CORRECTED 2026-07-15 — the closed-hole test cut
                           # showed the port sitting ~1 mm toward the back of
                           # the hole, i.e. 1 mm closer to the back plate than
                           # the 26.8 measurement (board plane was off). LED +
                           # power share this plane, so both moved with it.
USB_OFFSET_X = -20.5       # the +1.0 move (−21.25→−20.25) slightly over-
                           # centred toward the Pi; backed off 0.25. Direction
                           # confirmed correct (over-, not wrong-way).
# Battery-LED light bar (2026-07-15): a green-glass bar carries the four
# LEDs' light through the wall — green through green transmits, and light
# entering near a lit LED exits near it, so the 1-to-4 count survives. Cut
# from the Eco Glass sheet (3.0 thick, MEASURED 2026-07-15); friction-fits
# the wall slot, flush outside, stopping ~0.5 shy of the board edge. The
# LEDs span 43–53 from the board's left end (MEASURED 2026-07-13).
LED_BAR_W = 11.0           # NARROWED 2026-07-15 — the 14-wide slot also showed
                           # the power button; 11 just covers the 10 mm LED
                           # row (+0.5/side). Recutting the wall anyway.
LED_BAR_LEN = 10.0         # wall 3.5 + board-edge gap 7.0 − 0.5
LED_BAR_T = 3.0            # sheet thickness = the bar's third dimension
LED_BAR_SLIP = 0.05        # TIGHTENED 2026-07-15 — was 0.15 + wrong kerf =
                           # fell out; 0.05 + the KERF fix gives a friction fit
LED_OFFSET_X = 13.5        # shifted 2 toward the LEDs / away from the power
                           # button (was 15.5; button still showed). Verify all
                           # 4 LEDs stay covered — the button sits close to the
                           # rightmost LED, so a sliver clip may be the tradeoff
LED_FROM_BACK = 25.8       # same board plane as the USB-C (corrected -1)
# No reset pinhole: reset (and the onboard power/custom buttons) stay
# internal — the front arcade button clones power via pad 10.
# Power/charging light: on the board's RIGHT short edge, facing the right
# wall 8 mm away. DECIDED 2026-07-15: a blue-acrylic square rod (matches the
# battery light bar's treatment; blue-through-blue transmits and filters the
# interior green bleed). Fallback if the VCC pipes win on looks: set
# PWRLED_STYLE = "pipe" and recut just the right wall (3.0 round crush-rib
# hole; trim the pipe TAIL to ~11-12, cut end toward the LED).
PWRLED_STYLE = "rod"           # "rod" (square pocket) | "pipe" (round hole)
PWRLED_ROD_T = 2.65            # MEASURED 2026-07-15 — blue sheet is 2.65 bare;
                               # cut the rod this wide so its section is square
                               # (2.65 x 2.65). NB kerf ran ~0.09 wide on the
                               # test rod (3.2 drawn → 3.11) — watch on walls.
PWRLED_ROD_LEN = 11.0          # wall 3.5 + right-edge gap 8.0 − 0.5
PWRLED_SLIP = 0.15             # pocket over rod, per dimension
PWRLED_PIPE_HOLE = 3.0         # the pipe fallback's hole
PWRLED_FROM_GPIO_EDGE = 9.25   # MEASURED 2026-07-13: GPIO-side (top) corner
                               # → LED near side 8.5, +~0.75 to centre
PWRLED_FROM_BACK = 25.8        # board plane, same as the bottom-edge features
                               # (corrected -1 with the USB; verify on recut)

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
