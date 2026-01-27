# CLAUDE.md

## Overview

Interactive SVG-based visualization with clickable regions. Static site using jQuery.

## Files

- `index.html` - Main page with embedded SVG paths
- `anatomy-config.js` - Region configuration (labels, URLs, active state)
- `anatomy-script.js` - Mouse/touch event handling
- `anatomy-style.css` - Responsive styles, tooltip styling
- `jquery.min.js` - jQuery (bundled)

## Development

No build system. Open `index.html` in browser or use any static server.

## Key Points

- jQuery-based (`$` syntax throughout)
- Config uses global `basic_config` object
- SVG path IDs match config keys (`basic_1`, `basic_2`, etc.)
- Supports both mouse and touch events
