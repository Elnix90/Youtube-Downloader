# Tags & Album Classification System

## Overview

This is a keyword-based tagging and album classification system that automatically categorizes video by analyzing titles and uploader information.

### **Tag Computation** (`compute_tags()`)

Automatically generates tags for a video by:
- Scanning a tags directory containing keyword definition files (`.txt` format)
- Normalizing the video title and uploader name
- Matching content against tag patterns
- Returning a set of applicable tags

**Key Features:**
- Text normalization (removes special characters, extra spaces, etc.)
- Logs debug information for each matched tag
- Returns empty set if tags directory is missing