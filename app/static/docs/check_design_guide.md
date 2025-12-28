# Netaudit Check – Detailed Design & Implementation Guide

This document provides an **in-depth explanation** of how Netaudit network audit checks work, with a special focus on **reserved keyword variables**, their **data types**, how they **interact with the main program**, and a **step-by-step procedure** for creating a new check using a real example.

---

## Table of Contents
1. [What Is a Netaudit Check?](#1-what-is-a-netaudit-check)
2. [Reserved Keyword Variables (Core Contract)](#2-reserved-keyword-variables-core-contract)
3. [Metadata Variables](#3-metadata-variables)
4. [Runtime Variables](#4-runtime-variables)
5. [REQUESTS – Command Execution Contract](#5-requests--command-execution-contract)
6. [RESULTS – Output Contract](#6-results--output-contract)
7. [Handlers](#7-handlers)
8. [Step-by-Step: Creating a New Check (Using Example)](#8-step-by-step-creating-a-new-check-using-example)
9. [Key Design Principles](#9-key-design-principles)
10. [Summary](#10-summary)

---

## 1. What Is a Netaudit Check?

A Netaudit check is a **self-contained Python module** that:
- Executes one or more CLI commands on a network device
- Parses the output
- Produces a structured, machine-readable result
- Provides **human-readable remediation guidance**

Each check follows a **strict contract** so the Netaudit engine can:
- Discover checks dynamically
- Execute them safely
- Collect results consistently

---

## 2. Reserved Keyword Variables (Core Contract)

These variables are **mandatory** and are treated as **reserved keywords** by the Netaudit engine.

### 2.1 `CHECK_CLASS`

**Type:** `class reference`  
**Purpose:** Entry point for the check

```python
CHECK_CLASS = DeviceVersionCheck
```

#### How it interacts with the main program
- The main program imports the module
- Looks for a variable named `CHECK_CLASS`
- Instantiates it dynamically

```python
check = module.CHECK_CLASS(device, context)
```

If this variable is missing, the check **will not load**.

---

## 3. Metadata Variables

Metadata variables describe the check and are read **before execution**.

### 3.1 `NAME`

```python
NAME = "Version Check"
```

- **Type:** `str`
- **Purpose:** Human-readable check name
- Used in UI, reports, logs

### 3.2 `VERSION`

```python
VERSION = "1.0.0"
```

- **Type:** `str`
- **Purpose:** Track check evolution
- Uses semantic versioning

Increment when:
- Logic changes
- Parsing improves
- New conditions are added

### 3.3 `AUTHOR`

```python
AUTHOR = "Sanjeev Krishna"
```

- **Type:** `str`
- **Purpose:** Ownership and traceability

### 3.4 `TAGS`

```python
TAGS = ["Device", "Version", "Compliance"]
```

- **Type:** `list[str]`
- **Purpose:** Classification and filtering
- Used by:
  - UI filters
  - Reporting
  - Group execution

**Examples:**
- `"Security"`
- `"Routing"`
- `"BGP"`
- `"BestPractice"`

### 3.5 `DESCRIPTION`

```python
DESCRIPTION = "Verifies that the network device is running version 9.3(8) using 'show version'."
```

- **Type:** `str`
- **Purpose:**
  - Explains *what* is being validated
  - Helps infer CLI command
  - Appears in reports

**Must Answer:**
- What is checked?
- Why it matters?
- How it is validated?

### 3.6 `COMPLEXITY`

```python
COMPLEXITY = 1
```

- **Type:** `int` (1–5)
- **Purpose:** Execution complexity indicator

| Value | Meaning |
|-----|--------|
| 1 | Single command, single handler |
| 2 | Multiple parsing steps |
| 3 | Multiple commands |
| 4 | Conditional branching |
| 5 | Multi-stage or API-based |

Used for:
- Scheduling
- Performance planning
- UI indicators

---

## 4. Runtime Variables

These variables drive execution.

### 4.1 `device`

```python
self.device = device
```

- **Type:** `str`
- **Purpose:** Target device identifier
- Passed once during initialization
- Reused for all commands

The main program **never modifies this**.


### 4.2 `context`

```python
self.context = context or {}
```

- **Type:** `dict`
- **Purpose:** Shared execution context

May contain:
- Credentials
- API clients
- Site metadata
- Inventory details

**Optional but powerful**.

---

## 5. REQUESTS – Command Execution Contract

### 5.1 Structure

```python
self.REQUESTS = {
    "device": self.device,
    "command": "show version",
    "handler": "handle_initial"
}
```

**Type:** `dict | None`


### 5.2 Field Breakdown

| Key | Type | Description |
|----|-----|-------------|
| device | str | Target device |
| command | str | CLI command |
| handler | str | Method name |


### 5.3 How REQUESTS Interacts with Main Program

1. Main program reads `REQUESTS`
2. Executes `command` on `device`
3. Captures output
4. Calls handler dynamically

```python
handler = getattr(check, REQUESTS["handler"])
handler(device, command, output)
```


### 5.4 Clearing REQUESTS

```python
self.REQUESTS = None
```

- Signals completion
- Prevents re-execution
- Mandatory at end of check

---

## 6. RESULTS – Output Contract

### 6.1 Structure

```python
self.RESULTS = {
    "status": 0,
    "observation": "",
    "comments": []
}
```


### 6.2 Field Breakdown

| Field | Type | Purpose |
|-----|-----|--------|
| status | int | Outcome code |
| observation | str | Executive summary |
| comments | list[str] | Evidence + remediation |


### 6.3 Status Codes

| Code | Meaning      | Description                | When to Use |
|----|--------------|----------------------------|-------------|
| 0 | NOT RUN      | Check has not executed yet | Default state immediately after check initialization, before any CLI command has been executed.|
| 1 | PASS         | Check conditions fully satisfied | Use when the device configuration or state fully meets the expected requirement or policy. No action required.|
| 2 | FAIL         | Check conditions violated | Use when the device clearly violates a mandatory requirement, compliance rule, or expected configuration. Immediate remediation is usually required.|
| 3 | WARN         | Partial compliance, risk detected, or best-practice deviation | Use when the device is functional but deviates from best practices, has a potential risk, or is partially compliant. Not an outright failure, but attention is recommended.|
| 4 | INFO         | Informational check (no pass/fail semantics) | Use for informational checks that collect data or facts without enforcing compliance (e.g., inventory, feature detection, capacity reporting).|
| 5 | ERROR        | Execution/parsing error, command failed, unexpected output | Use when the check could not execute properly due to CLI failure, permission issues, unexpected output format, or internal parsing errors. Indicates a problem with execution, not device compliance.|
| 6 | INCONCLUSIVE | Output insufficient or ambiguous | Use when the command executed successfully, but the output does not provide enough information to reach a definitive conclusion (e.g., missing fields, truncated output, unsupported platform).|

---

## 7. Handlers

### 7.1 Signature

```python
def handle_initial(self, device, command, output):
    # Parse output
    pass
```

- **device:** `str`
- **command:** `str`
- **output:** `str` (raw CLI output)

Handlers:
- Parse output
- Update RESULTS
- Optionally set next REQUESTS

---

## 8. Step-by-Step: Creating a New Check (Using Example)

### Step 1: Identify the Audit Requirement
> Ensure NX-OS devices run approved firmware


### Step 2: Choose CLI Command
```text
show version
```


### Step 3: Define Metadata

```python
NAME = "NX-OS Firmware Version Compliance Check"
TAGS = ["NXOS", "Firmware", "Compliance"]
DESCRIPTION = "Validates that the device runs an approved NX-OS version."
COMPLEXITY = 1
```

### Step 4: Initialize REQUESTS and RESULTS

```python
self.REQUESTS = {
    "device": self.device,
    "command": "show version",
    "handler": "handle_initial"
}
```

### Step 5: Parse Output Using Regex

```python
version_pattern = r"NXOS: version (\S+)"
```

### Step 6: Determine Status

- Match → PASS or FAIL
- No match → INCONCLUSIVE

### Step 7: Add Actionable Comments

✔ Evidence  
✔ Why it matters  
✔ Clear remediation  
✔ References

### Step 8: Clear REQUESTS

```python
self.REQUESTS = None
```

---

## 9. Key Design Principles

- Deterministic execution
- Stateless main engine
- Self-contained checks
- Machine-readable + human-readable output
- Safe failure handling

---

## 10. Summary

Netaudit checks are:
- Plug-and-play
- Predictable
- Safe
- Auditable
- Scalable

Following this design ensures every check integrates seamlessly with the Netaudit framework.
