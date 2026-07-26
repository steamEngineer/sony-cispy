# Reference Implementations

This folder contains the original reference implementations that were merged to create the `sony-cisip2` library.

## Contents

### `bravia-quad-homeassistant/`
The Home Assistant custom integration for Sony Bravia Quad home theater systems. This implementation provided:
- Robust connection handling with command ID tracking
- JSON stream decoding
- Timeout management
- Notification callbacks
- Modern async/await patterns

### `python_sonycisip2-0.2.5/`
The original unmaintained Python library for Sony CIS-IP2 protocol. This implementation provided:
- Universal `get_feature()`/`set_feature()` API
- Partial CIS-IP2 command dictionary
- Variable placeholders
- Library structure

## Purpose

These reference implementations were used during development to merge the best aspects of both:
- The universal API from the old library
- The robust connection handling from the bravia-quad integration

The merged result is in the `src/sony_cisip2/` directory.

## Git Exclusion

bravia-quad-homeassistant is excluded. Please go to the github repository to see it's codebase

## Note

If you need to reference these implementations:
1. They are kept locally for historical reference
2. The merge is documented in `MERGE_SUMMARY.md` in the root directory
3. The current library (`src/sony_cisip2/`) contains all the merged functionality

