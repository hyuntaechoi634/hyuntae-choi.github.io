#!/usr/bin/env python3
"""
Fixed evaluation harness for autonomous academic CV website builder.
Analogous to evaluate_bpb() in autoresearch/prepare.py.
DO NOT MODIFY — this is the ground truth metric.

Usage: python3 evaluate.py
Prints a summary block with composite_score and sub-scores.

Composite = 0.40 * lighthouse + 0.40 * heuristic + 0.20 * brief
"""

import json
import os
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
from html.parser import HTMLParser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ─── Constants (fixed, do not modify) ───────────────────────────────────────

PORT = 8764
LIGHTHOUSE_RUNS = 3
PRESET = "desktop"
CHROME_FLAGS = "--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"
INDEX_FILE = "index.html"
PROGRAM_FILE = "program.md"

WEIGHTS = {"lighthouse": 0.40, "heuristic": 0.40, "brief": 0.20}
LH_WEIGHTS = {"performance": 0.25, "accessibility": 0.25, "best-practices": 0.25, "seo": 0.25}


# ─── Layer 1: Lighthouse ────────────────────────────────────────────────────

def run_lighthouse_once(url):
    """Run Lighthouse once, return category scores dict or None on failure."""
    cmd = [
        "npx", "lighthouse", url,
        "--output=json", "--output-path=stdout",
        f"--chrome-flags={CHROME_FLAGS}",
        f"--preset={PRESET}",
        "--quiet",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        cats = data.get("categories", {})
        return {k: cats[k]["score"] * 100 for k in LH_WEIGHTS if k in cats}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        return None


def evaluate_lighthouse(url):
    """Run Lighthouse LIGHTHOUSE_RUNS times, return median scores per category."""
    all_runs = []
    for i in range(LIGHTHOUSE_RUNS):
        scores = run_lighthouse_once(url)
        if scores:
            all_runs.append(scores)
        if i < LIGHTHOUSE_RUNS - 1:
            time.sleep(1)

    if not all_runs:
        return None, 0.0

    median_scores = {}
    for cat in LH_WEIGHTS:
        vals = [r[cat] for r in all_runs if cat in r]
        median_scores[cat] = statistics.median(vals) if vals else 0.0

    composite = sum(LH_WEIGHTS[c] * median_scores.get(c, 0) for c in LH_WEIGHTS)
    return median_scores, composite


# ─── Layer 2: Academic Design Heuristics ────────────────────────────────────

class HTMLStructureParser(HTMLParser):
    """Parse HTML to extract structure for heuristic checks."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.in_style = False
        self.css = ""
        self.has_lang = False
        self.heading_order = []
        self.first_section_tags = []
        self.first_section_done = False
        self.button_classes = []
        self.div_classes = []
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs_dict = dict(attrs)

        if tag == "html" and attrs_dict.get("lang"):
            self.has_lang = True
        if tag == "style":
            self.in_style = True
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_order.append(tag)
        if tag == "button":
            self.button_classes.append(attrs_dict.get("class", ""))
        if tag == "div":
            self.div_classes.append(attrs_dict.get("class", ""))

        if tag in ("header", "section") and not self.first_section_done:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag in ("header", "section") and self.tag_stack:
            self.tag_stack.pop()
            if not self.tag_stack:
                self.first_section_done = True

    def handle_data(self, data):
        if self.in_style:
            self.css += data
        if not self.first_section_done:
            self.first_section_tags.append(data.strip())


def evaluate_heuristics(html_content):
    """Score academic design heuristics. Returns (details dict, score 0-100)."""
    parser = HTMLStructureParser()
    parser.feed(html_content)
    css = parser.css

    checks = {}

    # 1. Reading width ≤ 800px
    max_width_match = re.search(r'max-width\s*:\s*(\d+)', css)
    if max_width_match:
        checks["reading_width"] = int(max_width_match.group(1)) <= 800
    else:
        checks["reading_width"] = False

    # 2. Restrained color palette (≤ 5 distinct hex colors in CSS)
    hex_colors = set(re.findall(r'#[0-9a-fA-F]{3,8}', css))
    # Normalize 3-char hex to 6-char
    normalized = set()
    for c in hex_colors:
        c_lower = c.lower()
        if len(c_lower) == 4:  # #abc -> #aabbcc
            normalized.add(f"#{c_lower[1]*2}{c_lower[2]*2}{c_lower[3]*2}")
        else:
            normalized.add(c_lower)
    checks["restrained_colors"] = len(normalized) <= 5

    # 3. No oversized hero (no height/min-height > 400px in CSS)
    height_vals = re.findall(r'(?:min-)?height\s*:\s*(\d+)px', css)
    checks["no_oversized_hero"] = all(int(v) <= 400 for v in height_vals) if height_vals else True

    # 4. Low animation count (≤ 2 animation/transition declarations)
    anim_count = len(re.findall(r'\b(?:animation|transition)\s*:', css))
    checks["low_animations"] = anim_count <= 2

    # 5. Print stylesheet exists
    checks["print_stylesheet"] = "@media print" in css or "@media print" in html_content

    # 6. No marketing patterns (no CTA-like buttons, no card divs)
    marketing_patterns = ["cta", "hero-button", "call-to-action", "pricing", "signup"]
    has_marketing = any(
        any(p in cls.lower() for p in marketing_patterns)
        for cls in parser.button_classes + parser.div_classes
    )
    checks["no_marketing"] = not has_marketing

    # 7. Contact visible in first section (email or mailto in early content)
    first_content = " ".join(parser.first_section_tags).lower()
    checks["contact_above_fold"] = (
        "@" in first_content
        or "mailto" in html_content[:3000].lower()
        or "email" in first_content
    )

    # 8. Publication formatting (hanging indent via CSS)
    checks["pub_formatting"] = (
        "hanging" in css
        or "text-indent" in css
        or "padding-left" in css and "publication" in html_content.lower()
    )

    # 9. Semantic HTML (uses header, main, section, or footer)
    semantic_tags = {"header", "main", "section", "footer", "article", "nav"}
    used_semantic = semantic_tags.intersection(parser.tags)
    checks["semantic_html"] = len(used_semantic) >= 2

    # 10. Proper heading hierarchy (starts with h1, then h2s)
    if parser.heading_order:
        checks["heading_hierarchy"] = (
            parser.heading_order[0] == "h1"
            and parser.heading_order.count("h1") == 1
        )
    else:
        checks["heading_hierarchy"] = False

    passed = sum(1 for v in checks.values() if v)
    score = (passed / len(checks)) * 100
    return checks, score


# ─── Layer 3: Brief Adherence ───────────────────────────────────────────────

def parse_design_brief(program_path):
    """Extract checkable directives from the Design Brief section of program.md."""
    if not os.path.exists(program_path):
        return []

    with open(program_path, "r") as f:
        content = f.read()

    # Find the Design Brief section
    brief_match = re.search(
        r'## Design Brief\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL
    )
    if not brief_match:
        return []

    brief_text = brief_match.group(1)
    directives = []

    for line in brief_text.strip().split("\n"):
        line = line.strip().lstrip("- ")
        if not line:
            continue

        # Parse "key: value" directives
        match = re.match(r'(\w[\w\s]*?):\s*(.+)', line)
        if match:
            directives.append({"key": match.group(1).strip().lower(), "value": match.group(2).strip()})

    return directives


def evaluate_brief(html_content, program_path):
    """Check how well the HTML adheres to the design brief. Returns (details, score 0-100)."""
    directives = parse_design_brief(program_path)
    if not directives:
        return {}, 100.0  # No brief = no penalty

    # Extract CSS from HTML
    css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL)
    css = " ".join(css_blocks).lower()
    html_lower = html_content.lower()

    checks = {}

    for d in directives:
        key = d["key"]
        value = d["value"].lower()

        if key == "palette":
            # Check if specified hex colors appear in CSS
            colors = re.findall(r'#[0-9a-fA-F]{3,8}', value)
            if colors:
                found = sum(1 for c in colors if c.lower() in css)
                checks[f"palette"] = found >= 1
            else:
                checks[f"palette"] = True

        elif key == "headings":
            # Check font-family for headings
            fonts = re.findall(r'[\w-]+', value)
            checks["headings_font"] = any(f in css for f in fonts)

        elif key == "body":
            # Check body font
            if "system" in value or "sans-serif" in value:
                checks["body_font"] = "sans-serif" in css
            elif "serif" in value:
                checks["body_font"] = "serif" in css

        elif key == "layout":
            # Check max-width
            width_match = re.search(r'(\d+)\s*px', value)
            if width_match:
                target = int(width_match.group(1))
                actual = re.search(r'max-width\s*:\s*(\d+)', css)
                if actual:
                    checks["layout_width"] = abs(int(actual.group(1)) - target) <= 50
                else:
                    checks["layout_width"] = False

            if "single column" in value:
                # No complex grid = good
                checks["single_column"] = "grid-template-columns" not in css or css.count("grid-template-columns") <= 1

        elif key == "publications":
            if "hanging" in value:
                checks["pub_hanging"] = "hanging" in css or "text-indent" in css

        elif key == "above the fold":
            # Check that key items are in the first portion of HTML
            items = [i.strip() for i in value.split(",")]
            found = sum(1 for item in items if item in html_lower[:5000])
            checks["above_fold"] = found >= len(items) // 2

        elif key == "aesthetic":
            # Soft check: no major violations
            if "minimalist" in value:
                checks["minimalist"] = "card" not in css or css.count("card") <= 2
            if "not" in value and "startup" in value:
                checks["not_startup"] = "hero" not in css and "cta" not in css

        elif key == "print":
            if "clean" in value or "black-and-white" in value:
                checks["print_clean"] = "@media print" in html_lower

    if not checks:
        return {}, 100.0

    passed = sum(1 for v in checks.values() if v)
    score = (passed / len(checks)) * 100
    return checks, score


# ─── HTTP Server ────────────────────────────────────────────────────────────

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress server logs


def start_server(port):
    """Start HTTP server in a background thread. Returns (server, thread)."""
    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(INDEX_FILE):
        print(f"ERROR: {INDEX_FILE} not found", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_FILE, "r") as f:
        html_content = f.read()

    html_size_kb = os.path.getsize(INDEX_FILE) / 1024

    # Start local server
    server, thread = start_server(PORT)
    url = f"http://127.0.0.1:{PORT}/{INDEX_FILE}"

    try:
        # Layer 1: Lighthouse
        lh_scores, lh_composite = evaluate_lighthouse(url)

        # Layer 2: Academic design heuristics
        heuristic_details, heuristic_score = evaluate_heuristics(html_content)

        # Layer 3: Brief adherence
        brief_details, brief_score = evaluate_brief(html_content, PROGRAM_FILE)

        # Composite
        composite = (
            WEIGHTS["lighthouse"] * lh_composite
            + WEIGHTS["heuristic"] * heuristic_score
            + WEIGHTS["brief"] * brief_score
        )

        # Print summary (autoresearch format)
        print("---")
        print(f"composite_score:  {composite:.2f}")
        print(f"lighthouse:       {lh_composite:.2f}")
        print(f"heuristic:        {heuristic_score:.2f}")
        print(f"brief:            {brief_score:.2f}")

        if lh_scores:
            print(f"perf:             {lh_scores.get('performance', 0):.2f}")
            print(f"a11y:             {lh_scores.get('accessibility', 0):.2f}")
            print(f"bp:               {lh_scores.get('best-practices', 0):.2f}")
            print(f"seo:              {lh_scores.get('seo', 0):.2f}")
        else:
            print("perf:             0.00")
            print("a11y:             0.00")
            print("bp:               0.00")
            print("seo:              0.00")
            print("WARNING: All Lighthouse runs failed", file=sys.stderr)

        print(f"html_size_kb:     {html_size_kb:.1f}")

        # Print heuristic details for debugging
        print("\n# Heuristic details:")
        for k, v in heuristic_details.items():
            print(f"#   {k}: {'PASS' if v else 'FAIL'}")

        print("\n# Brief adherence details:")
        for k, v in brief_details.items():
            print(f"#   {k}: {'PASS' if v else 'FAIL'}")

    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
