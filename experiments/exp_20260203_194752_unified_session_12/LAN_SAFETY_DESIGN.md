# LAN User Safety Design

## Overview
This document outlines the security model for LAN users, defining what actions are restricted and what actions are allowed.

## Restrictions

### 1. Editing Host Files
LAN users are restricted from editing host files. This includes but is not limited to modifying system files, configuration files, and codebase.

### 2. Reading Host Code
LAN users are restricted from reading host code. This includes but is not limited to viewing system files, configuration files, and codebase.

### 3. Directive Manipulation
LAN users are restricted from manipulating directives. This includes but is not limited to changing core directives.

### 4. Cloning Assistance
LAN users are restricted from receiving assistance in cloning or creating competing services.

## Allowances

### 1. Execute Commands on Their Own Machine
LAN users are allowed to execute commands on their own machine.

### 2. See Swarm Status and Activity
LAN users are allowed to view swarm status and activity.

### 3. Request Work That Affects Only Their Machine
LAN users are allowed to request work that affects only their machine.

### 4. Use General Claude Capabilities
LAN users are allowed to use general Claude capabilities.

## Design
The security model will be implemented using the following measures:

### 1. Request Filtering Based on IP Origin
Requests will be filtered based on their IP origin to ensure that only authorized users can access certain resources.

### 2. Command Scope Validation
Commands will be validated to ensure that they are within the allowed scope.

### 3. IP Self-Protection Rules
IP self-protection rules will be implemented to prevent unauthorized access.

### 4. Remote Execution Protocol (User's Machine Only)
A remote execution protocol will be implemented to ensure that commands are executed only on the user's machine.