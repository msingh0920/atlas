# CLAUDE.md - AI Assistant Guide for Atlas

## Project Overview

**Atlas** is an interactive human anatomy visualization web application. It displays an SVG-based body diagram with clickable/hoverable regions that show tooltips and can link to external resources.

## Tech Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES5)
- **Dependencies**: jQuery (bundled as `jquery.min.js`)
- **No build system**: Static files served directly

## Codebase Structure

```
atlas/
├── index.html           # Main HTML page with SVG anatomy paths
├── anatomy-config.js    # Configuration for body regions (labels, URLs, targets)
├── anatomy-script.js    # Core interaction logic (hover, click, touch events)
├── anatomy-style.css    # Responsive styles and tooltip styling
├── jquery.min.js        # jQuery library (minified)
├── modela.png           # Background anatomy image
└── CLAUDE.md            # This file
```

## Key Files Explained

### `index.html`
- Contains an embedded SVG with 9 path elements (`basic_1` through `basic_9`)
- Each path corresponds to a body region: head, neck, chest, abdomen, pelvis, right arm, left arm, right leg, left leg
- Paths are transparent with stroke outlines for hover detection
- References `modela.png` as the background image

### `anatomy-config.js`
- Exports `basic_config` object with settings for each body region
- Configuration options per region:
  - `hover`: Tooltip text displayed on mouseover
  - `url`: Link destination when clicked
  - `target`: `"_blank"` (new tab), `"_self"` (same window), or `"none"` (no navigation)
  - `active`: `true`/`false` to show/hide the region

### `anatomy-script.js`
- IIFE pattern with jQuery dependency
- Key functions:
  - `isTouchEnabled()`: Detects touch device capability
  - `addEvent(id)`: Binds mouse and touch events to SVG paths
- Event handling:
  - Mouseenter/mouseleave: Show/hide tooltips
  - Click/touch: Navigate to configured URL
  - Hover state: Red fill highlight (`rgba(255, 0, 0, 0.3)`)

### `anatomy-style.css`
- Responsive breakpoints from 320px to 768px+
- Tooltip (`#tip-basic`) positioning and styling
- User-select disabled for better touch interaction

## Development Workflow

### Local Development
1. Open `index.html` directly in a browser, or
2. Use a local server:
   ```bash
   python -m http.server 8000
   # or
   npx serve .
   ```

### Making Changes

**To modify body region labels/links:**
1. Edit `anatomy-config.js`
2. Update the `hover`, `url`, or `target` properties

**To modify interaction behavior:**
1. Edit `anatomy-script.js`
2. Color values are in `addEvent()` function

**To modify styling:**
1. Edit `anatomy-style.css`
2. Tooltip styles are under `#tip-basic`
3. Responsive breakpoints are at the bottom of the file

### No Build/Test Commands
This project has no build process or test suite. Changes can be verified by refreshing the browser.

## Code Conventions

- **JavaScript**: ES5 syntax with jQuery, strict mode enabled
- **CSS**: Standard CSS3 with vendor prefixes for older browsers
- **Naming**: SVG paths use `basic_N` IDs matching config keys
- **Comments**: Inline comments in config file indicate body part names

## Body Region Mapping

| ID       | CSS Class | Body Part   |
|----------|-----------|-------------|
| basic_1  | .head     | Head        |
| basic_2  | .neck     | Neck        |
| basic_3  | .chest    | Chest       |
| basic_4  | .abdomen  | Abdomen     |
| basic_5  | .pelvis   | Pelvis      |
| basic_6  | .arm-rt   | Right Arm   |
| basic_7  | .arm-lt   | Left Arm    |
| basic_8  | .leg-rt   | Right Leg   |
| basic_9  | .leg-lt   | Left Leg    |

## Important Notes for AI Assistants

1. **No package manager**: Do not suggest `npm install` or similar - this is a static site
2. **jQuery required**: All DOM manipulation uses jQuery (`$` syntax)
3. **SVG paths are complex**: The path `d` attributes contain precise coordinates - modify with care
4. **Configuration is global**: `basic_config` is a global variable accessed by the script
5. **Touch support**: The code handles both mouse and touch events separately
6. **Browser compatibility**: Code includes vendor prefixes suggesting older browser support requirements
