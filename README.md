# KIBS IMS — Backend

Backend service for KIBS, an inventory management system, built with Flask and deployed on PythonAnywhere.

## Features
- REST API for inventory records
- JWT-based authentication middleware
- MySQL-backed persistence, with schema migration scripts
- Deployment tooling for PythonAnywhere (WSGI configuration, dependency management)

## Status: in progress
Core CRUD and authentication are functional and deployed. Ongoing work: consolidating the deployment scripts/packages accumulated during setup, and moving deployment credentials out of tracked files entirely (in progress as of this update).

## Stack
Python, Flask, MySQL, JWT
