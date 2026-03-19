# VladX Learning Hub

An educational XBlock that demonstrates the full XBlock API surface -- fields, scopes, views, handlers, children, services, grading, XML serialization, validation, and Studio integration.

Built for learning purposes as part of an Open edX XBlock Individual Development Plan.

## Features Demonstrated

| Feature | What's shown |
|---------|-------------|
| **Field types** | String, Integer, Boolean, Float, List, Dict, DateTime, Any |
| **All 6 scopes** | content, settings, user_state, user_state_summary, preferences, user_info |
| **Views** | student_view, studio_view, author_view, fallback_view |
| **Handlers** | @XBlock.json_handler (6 endpoints), @XBlock.handler (raw) |
| **Fragment API** | HTML + CSS + JS, initialize_js, add_frag_resources |
| **Children** | has_children, render_child, nested OLX scenarios |
| **Services** | @XBlock.needs('i18n'), @XBlock.wants('settings', 'user') |
| **Grading** | has_score, runtime.publish('grade'), custom analytics events |
| **XML/OLX** | Custom parse_xml / add_xml_to_node with xml_node field |
| **Validation** | validate() with ValidationMessage |
| **Studio** | studio_view with save/cancel via runtime.notify |
| **Search** | index_dictionary for platform search indexing |
| **Entry points** | xblock.v1 plugin registration in setup.py |

## What It Does

A mini-quiz block where:
- Instructors set a question and correct answer via Studio
- Students submit answers and get graded
- Students can vote (thumbs up/down) on the question
- Display mode toggles between compact and full (Scope.preferences)
- Child blocks can be nested inside

## Project Structure

```
vladx/
├── setup.py                          # Package config with xblock.v1 entry point
├── vladx/
│   ├── __init__.py
│   ├── vladx.py                      # Main XBlock class
│   └── static/
│       ├── html/
│       │   ├── vladx.html            # Student view template
│       │   └── vladx_studio.html     # Studio editor template
│       ├── js/src/
│       │   ├── vladx.js              # Student-side JS
│       │   └── vladx_studio.js       # Studio-side JS
│       └── css/
│           └── vladx.css             # Styles for all views
├── xblock_questions.md               # 20 self-check questions on XBlock API
└── xblock_runtime.md                 # Explanation of XBlock runtime architecture
```

## Setup

### Prerequisites

- Python 3.11+
- [XBlock SDK](https://github.com/openedx/xblock-sdk) cloned and installed

### Install

```bash
# Activate the xblock-sdk virtualenv
source /path/to/xblock-sdk/bin/activate

# Install vladx in development mode
pip install -e vladx/

# Create/update the database (first time only)
python xblock-sdk/manage.py migrate

# Run the workbench
python xblock-sdk/manage.py runserver
```

Open http://localhost:8000 -- you should see VladX scenarios in the list.

### Workbench Scenarios

| Scenario | Description |
|----------|-------------|
| VladX -- Basic | Single block with default settings |
| VladX -- Custom settings | Custom question, 5 attempts, weight 2.0 |
| VladX -- Multiple blocks | Three blocks in a vertical container |
| VladX -- With children | Block with nested html_demo child |

## Key Concepts for XBlock Developers

### Scopes

```
Scope.content            = DEFINITION + NONE   → shared content (question text)
Scope.settings           = USAGE + NONE        → per-instance config (max attempts)
Scope.user_state         = USAGE + ONE         → per-student data (answer, score)
Scope.user_state_summary = USAGE + ALL         → aggregated data (vote counts)
Scope.preferences        = TYPE + ONE          → per-student, all instances (display mode)
Scope.user_info          = ALL + ONE           → per-student, all blocks (language)
```

### Request Flow

```
Browser                          Server
───────                          ──────
JS: runtime.handlerUrl()    →    generates URL
JS: $.ajax POST to URL      →    runtime routes to handler
                             ←    @json_handler returns dict
JS: updates DOM with response
```

### Fragment Lifecycle

```python
def student_view(self, context=None):
    html = self.resource_string("static/html/vladx.html")
    frag = Fragment(html.format(self=self))       # 1. HTML content
    frag.add_css(self.resource_string("..."))      # 2. CSS
    frag.add_javascript(self.resource_string("..."))  # 3. JS
    frag.initialize_js('VladXBlock')               # 4. Init function name
    return frag
```

## License

AGPL v3
