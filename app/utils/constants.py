"""
This module defines general constants used across the Netaudit application.
"""

# Mapping of user actions to their associated display attributes.
USER_ACTIONS = {
    "No Action": {"icon": "fa-circle-minus", "color": "secondary"},
    "False Positive": {"icon": "fa-check-circle", "color": "success"},
    "Mitigated": {"icon": "fa-tools", "color": "warning"},
    "Accepted Risk": {"icon": "fa-exclamation-triangle", "color": "danger"},
}

"""
Status Code	Meaning	When to Use
0	NOT_RUN	Check has not executed yet
1	PASS	Check conditions fully satisfied
2	FAIL	Check conditions violated
3	WARN	Partial compliance, risk detected, or best-practice deviation
4	INFO	Informational check (no pass/fail semantics)
5	ERROR	Execution/parsing error, command failed, unexpected output
6	INCONCLUSIVE	Output insufficient or ambiguous

"""

# Status codes for audit checks.
AUDIT_STATUS_CODES = {
    0: {"label": "NOT RUN",
        "icon": "fa-circle-minus",
        "description": "Check has not executed yet",
        "excel_color": "#D9D9D9",
        },
    1: {"label": "PASS",
        "icon": "fa-check-circle",
        "description": "Check conditions fully satisfied",
        "excel_color": "#C6EFCE",
        },
    2: {"label": "FAIL",
        "icon": "fa-xmark-circle",
        "description": "Check conditions violated",
        "excel_color": "#FFC7CE",
        },
    3: {"label": "WARN",
        "icon": "fa-triangle-exclamation",
        "description": "Partial compliance, risk detected, or best-practice deviation",
        "excel_color": "#FFEBAB",
        },
    4: {"label": "INFO",
        "icon": "fa-info-circle",
        "description": "Informational check (no pass/fail semantics)",
        "excel_color": "#9ED9EC",
        },
    5: {"label": "ERROR",
        "icon": "fa-bug",
        "description": "Execution/parsing error, command failed, unexpected output",
        "excel_color": "#F99D9D",
        },
    6: {"label": "INCONCLUSIVE",
        "icon": "fa-question-circle",
        "description": "Output insufficient or ambiguous",
        "excel_color": "#A7D8E3",
        },
}

# Font Awesome icons for different device views.
VIEW_ICONS = [
    "fa fa-network-wired",
    "fa fa-globe",
    "fa fa-server",
    "fa fa-cloud",
    "fa fa-database",
    "fa fa-sitemap",
]

# Endpoints that do not require user authentication.
EXEMPT_ENDPOINTS = {
    "login",
    "register",
    "logout",
    "static",
    "root",
}