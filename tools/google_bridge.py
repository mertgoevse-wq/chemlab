"""ChemLab Google bridge — drive Gemini's web app as a real browser session.

This exists because there is no Gemini API key in the project. It uses a
dedicated Chrome profile, not your daily browser profile: Chrome locks its
default profile while running, and copying a multi-gigabyte profile is worse
than signing in once.

    python tools/google_bridge.py --check              # is the session signed in?
    python tools/google_bridge.py --login              # opens a window; sign in by hand
    python tools/google_bridge.py --prompt "seamless dark epoxy lab floor, ..." \
        --out game/assets/textures/T_floor_epoxy_BC.png
    python tools/google_bridge.py --prompt "..." --out out.png --headless

Caveats, stated plainly:
- Automating the Gemini web app is not a supported interface. Layout changes
  break selectors, and Google's terms restrict automated access. The supported
  path is an API key (https://aistudio.google.com/apikey); this bridge is the
  offline-friendly fallback the project asked for.
- It never handles your password: sign-in happens in the visible browser and
  the session lives in .cache/chrome-profile (git-ignored).
- Image extraction saves the displayed render. For textures above ~1k, use the
  "download" affordance in the Gemini UI, or prefer the API path.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(ROOT, ".cache", "chrome-profile")
GEMINI = "https://gemini.google.com/app"

COMPOSER_SELECTORS = [
    "div[contenteditable='true'][role='textbox']",
    "rich-textarea div[contenteditable='true']",
    "div[contenteditable='true']",
]
SEND_SELECTORS = [
    "button[aria-label*='Send' i]",
    "button[aria-label*='Senden' i]",
    "button.send-button",
]
IMAGE_SELECTORS = [
    "img[src^='blob:']",
    "img[src*='googleusercontent.com']",
    "single-image img",
    "generated-image img",
]


def _launch(headless: bool):
    from playwright.sync_api import sync_playwright

    os.makedirs(PROFILE, exist_ok=True)
    pw = sync_playwright().start()
    context = pw.chromium.launch_persistent_context(
        PROFILE,
        channel="chrome",
        headless=headless,
        viewport={"width": 1440, "height": 1000},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else context.new_page()
    return pw, context, page


def _signed_in(page) -> bool:
    """A guest composer is visible too, so presence of the composer proves nothing.

    Require an account control and the absence of the sign-in affordance.
    """
    avatar = page.query_selector('a[aria-label*="Google Account" i]')
    sign_in = page.query_selector(
        'a:has-text("Sign in"), a:has-text("Anmelden"), button:has-text("Sign in"), '
        'button:has-text("Anmelden")'
    )
    return avatar is not None and sign_in is None


def _first(page, selectors, timeout: int = 15000):
    deadline = timeout
    step = 500
    for _ in range(max(1, deadline // step)):
        for sel in selectors:
            try:
                handle = page.query_selector(sel)
            except Exception:
                handle = None
            if handle and handle.is_visible():
                return handle
        page.wait_for_timeout(step)
    return None


def cmd_check(headless: bool) -> int:
    pw, context, page = _launch(headless)
    try:
        page.goto(GEMINI, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        signed_in = _signed_in(page)
        print("SIGNED_IN" if signed_in else "SIGNED_OUT")
        if not signed_in:
            print("Run: python tools/google_bridge.py --login")
        return 0 if signed_in else 1
    finally:
        context.close()
        pw.stop()


def cmd_login() -> int:
    pw, context, page = _launch(headless=False)
    try:
        page.goto(GEMINI, wait_until="domcontentloaded", timeout=60000)
        print("A Chrome window is open. Sign in, then press Enter here.")
        try:
            input()
        except EOFError:
            page.wait_for_timeout(120000)
        ready = _signed_in(page)
        print("SESSION_READY" if ready else "SESSION_NOT_READY")
        return 0 if ready else 1
    finally:
        context.close()
        pw.stop()


def cmd_generate(prompt: str, out_path: str, headless: bool, timeout_s: int) -> int:
    pw, context, page = _launch(headless)
    try:
        page.goto(GEMINI, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        if not _signed_in(page):
            raise SystemExit("Not signed in. Run: python tools/google_bridge.py --login")
        composer = _first(page, COMPOSER_SELECTORS, 20000)
        if composer is None:
            raise SystemExit("Composer not found; the web UI may have changed.")

        composer.click()
        composer.type(prompt, delay=8)
        send = _first(page, SEND_SELECTORS, 5000)
        if send is not None:
            send.click()
        else:
            composer.press("Enter")

        img = _first(page, IMAGE_SELECTORS, timeout_s * 1000)
        if img is None:
            raise SystemExit(
                "No image appeared. The web UI likely changed selectors, or the "
                "prompt was refused. Run without --headless to watch it."
            )
        page.wait_for_timeout(1500)

        # Pull the bytes through fetch so blob: URLs work without a new tab.
        data_url = img.evaluate(
            """async (el) => {
                const r = await fetch(el.currentSrc || el.src);
                const b = await r.blob();
                return await new Promise(res => {
                    const fr = new FileReader();
                    fr.onload = () => res(fr.result);
                    fr.readAsDataURL(b);
                });
            }"""
        )
        if not isinstance(data_url, str) or "," not in data_url:
            raise SystemExit("Image element returned no data.")

        raw = base64.b64decode(data_url.split(",", 1)[1])
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "wb") as fh:
            fh.write(raw)
        print(f"WROTE {out_path} ({len(raw)} bytes)")
        return 0
    finally:
        context.close()
        pw.stop()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--prompt")
    ap.add_argument("--out")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    if args.login:
        return cmd_login()
    if args.check:
        return cmd_check(args.headless)
    if args.prompt and args.out:
        return cmd_generate(args.prompt, args.out, args.headless, args.timeout)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
