# CLAUDE.md - Atlas Interactive Anatomy Viewer

## Project Overview

Atlas is a lightweight, interactive human anatomy diagram viewer built with vanilla JavaScript and jQuery. Users can hover over and click body regions to see tooltips and navigate to external resources. The application is configuration-driven and supports both desktop and mobile devices.

**Version:** 2.6 (beta)
**Type:** Static web application (no build system required)

## File Structure

```
atlas/
├── index.html          # Main HTML file with embedded SVG overlay
├── anatomy-config.js   # Configuration for all body regions
├── anatomy-script.js   # Interactive logic and event handling
├── anatomy-style.css   # Styling and responsive breakpoints
├── jquery.min.js       # jQuery library (minified)
└── modela.png          # Human anatomy diagram image (800x1360px)
```

## Technologies

- **HTML5** - Page structure with inline SVG
- **CSS3** - Styling with responsive media queries
- **JavaScript (ES6+)** - Application logic
- **jQuery** - DOM manipulation and event handling
- **SVG** - Interactive clickable regions overlay

## Development Workflow

### Running Locally
No build process required. Simply:
1. Open `index.html` in a web browser
2. Or serve with any static file server

### Making Changes
1. **Tooltips/Links:** Edit `anatomy-config.js`
2. **Interaction Logic:** Edit `anatomy-script.js`
3. **Styling:** Edit `anatomy-style.css`
4. **Structure:** Edit `index.html`

Refresh the browser to see changes immediately.

## Configuration Guide

### anatomy-config.js Structure

Each body region (basic_1 through basic_9) has four properties:

```javascript
"basic_1": {
    "hover": "Tooltip text displayed on hover",
    "url": "https://example.com/destination",
    "target": "_blank",  // "_blank", "_self", or "none"
    "active": true       // Show/hide the region
}
```

### Body Region IDs
| ID | Body Part |
|----|-----------|
| basic_1 | Head |
| basic_2 | Neck |
| basic_3 | Chest |
| basic_4 | Abdomen |
| basic_5 | Pelvis |
| basic_6 | Right Arm |
| basic_7 | Left Arm |
| basic_8 | Right Leg |
| basic_9 | Left Leg |

## Code Conventions

### JavaScript
- IIFE pattern with jQuery: `(function($) { "use strict"; ... })(jQuery);`
- CamelCase for variables: `isTouchEnabled`, `basicanatomytipw`
- jQuery objects prefixed with `$`: `$basicatip`
- Use `let`/`const` (ES6+), not `var`

### CSS
- Mobile-first responsive design
- Vendor prefixes for compatibility: `-webkit-`, `-moz-`, `-ms-`
- Media query breakpoints: 320px, 400px, 480px, 568px, 685px, 767px, 768px+

### HTML/SVG
- SVG viewBox: 800x1360
- Region IDs follow pattern: `basic_N` where N is 1-9
- SVG paths use `vector-effect="non-scaling-stroke"`

## Key Patterns for AI Assistants

### When Modifying Configuration
- Only edit `anatomy-config.js` for tooltip/URL changes
- Keep `"active": true` unless intentionally hiding a region
- Use `"target": "none"` to disable click navigation

### When Modifying Interactions
- Preserve dual support for touch AND mouse events
- Maintain tooltip boundary checking logic
- Keep the IIFE and strict mode wrapper

### When Modifying Styles
- Test all responsive breakpoints (320px to 768px+)
- Maintain vendor prefixes for cross-browser support
- Keep tooltip z-index high (currently 99999)

### Files to Never Modify
- `jquery.min.js` - Third-party minified library
- `modela.png` - Source image asset (unless replacing the anatomy diagram)

### Testing Checklist
- [ ] Hover tooltips appear correctly on desktop
- [ ] Touch interactions work on mobile
- [ ] Tooltips stay within viewport bounds
- [ ] Click navigation opens correct URLs
- [ ] Responsive layout works at all breakpoints

## Git Workflow

- Main development happens on feature branches prefixed with `claude/`
- Commit messages should be descriptive of changes made
- No CI/CD pipeline - manual deployment of static files
