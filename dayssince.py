#!/usr/bin/env python3
"""Dev CLI for the DaysSince display.

Examples:
  ./dayssince.py --png /tmp/preview.png --value 42   # layout iteration, no hardware
  ./dayssince.py --png /tmp/preview.png              # render live data to PNG
  ./dayssince.py --panel                             # fetch + flash the panel now
  ./dayssince.py --panel --value 42                  # flash an arbitrary value
  ./dayssince.py --once                              # field-mode work unit: flash only if changed
  ./dayssince.py --watch 60                          # loop --once forever
  ./dayssince.py --clear                             # blank the panel
"""

import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from dayssince import config, display, fetch, render, state


def get_data(args) -> dict:
    if args.value is not None:
        return {
            "daysSince": args.value,
            "lastEvent": datetime.now().astimezone().isoformat(),
            "reporter": args.reporter,
        }
    data = fetch.fetch_days_since()
    if args.reporter:
        data["reporter"] = args.reporter
    return data


def battery_or_none():
    try:
        from dayssince import pisugar
        return pisugar.battery_pct()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--png", metavar="PATH", help="render to a PNG preview instead of the panel")
    parser.add_argument("--panel", action="store_true", help="flash the panel unconditionally")
    parser.add_argument("--once", action="store_true", help="fetch + flash only if value changed (updates state)")
    parser.add_argument("--watch", type=int, nargs="?", const=60, metavar="SECONDS", help="repeat --once forever")
    parser.add_argument("--clear", action="store_true", help="blank the panel")
    parser.add_argument("--value", type=int, help="override daysSince instead of fetching")
    parser.add_argument("--panels", type=int, choices=(1, 2), help="override DAYSSINCE_PANELS")
    parser.add_argument("--layout", choices=render.LAYOUTS, help="override DAYSSINCE_LAYOUT (two-panel)")
    parser.add_argument("--reporter", help="override the reporter name (preview)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.panels is not None:
        config.PANELS = args.panels
    if args.layout is not None:
        config.LAYOUT = args.layout

    if args.clear:
        from dayssince import epd
        panel = epd.EPD()
        try:
            panel.init()
            panel.clear()
            panel.sleep()
        finally:
            panel.close()
        return

    if args.png:
        data = get_data(args)
        if config.PANELS >= 2:
            layers = render.render_pair(data["daysSince"], data.get("lastEvent"),
                                        battery_or_none(), data.get("reporter"),
                                        layout=config.LAYOUT)
            previews = [render.composite(b, r) for b, r in layers]
            gap = 24  # visual stand-in for the two bezels
            from PIL import Image
            sheet = Image.new("RGB", (render.WIDTH * 2 + gap, render.HEIGHT), (90, 90, 90))
            sheet.paste(previews[0], (0, 0))
            sheet.paste(previews[1], (render.WIDTH + gap, 0))
            sheet.save(args.png)
        else:
            black_img, red_img = render.render(
                data["daysSince"], (data.get("lastEvent") or "")[:10] or None, battery_or_none()
            )
            render.composite(black_img, red_img).save(args.png)
        print(f"wrote {args.png} (daysSince={data['daysSince']})")
        return

    if args.panel:
        data = get_data(args)
        display.flash_value(data["daysSince"], data.get("lastEvent"), battery_or_none(),
                            data.get("reporter"))
        return

    if args.once or args.watch is not None:
        import time
        from launcher import update_panel  # same work unit the field mode uses
        st = state.load()
        while True:
            update_panel(st, battery_or_none())
            if args.watch is None:
                return
            time.sleep(args.watch)

    parser.print_help()


if __name__ == "__main__":
    main()
