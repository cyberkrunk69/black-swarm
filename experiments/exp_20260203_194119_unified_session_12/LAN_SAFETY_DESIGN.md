# LAN User Safety Design

## Overview
This document outlines the security model for LAN users, restricting them from certain actions while allowing others.

## Restrictions

### 1. Editing Host Files
LAN users are restricted from editing host files. This includes modifying any files on the swarm host machine.

### 2. Reading Host Code
LAN users are restricted from reading host code. This includes accessing the codebase or learning how it works.

### 3. Directive Manipulation
LAN users are restricted from manipulating directives. This includes giving instructions to change core directives.

### 4. Cloning Assistance
LAN users are restricted from receiving assistance in cloning or creating competing services.

## Allowances

### 1. Remote Execution
LAN users are allowed to execute commands on their own machine.

### 2. Swarm Status and Activity
LAN users are allowed to see swarm status and activity.

### 3. Request Work
LAN users are allowed to request work that affects only their machine.

### 4. General Claude Capabilities
LAN users are allowed to use general Claude capabilities.

## Design
The security model will be implemented using the following measures:

### 1. Request Filtering
Requests will be filtered based on IP origin to ensure that only authorized users can access certain resources.

### 2. Command Scope Validation
Commands will be validated to ensure they are within the allowed scope for the user's machine.

### 3. IP Self-Protection Rules
IP self-protection rules will be implemented to prevent unauthorized access.

### 4. Remote Execution Protocol
A remote execution protocol will be established to ensure that users can only execute commands on their own machine.

## Conclusion
The LAN user safety design aims to provide a secure environment for users while restricting them from certain actions that could compromise the system.