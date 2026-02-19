# Sample API Design Document

## Overview
This document outlines the design for a new REST API service.

## Endpoints

### GET /api/users
Retrieve list of users.

**Response:**
```json
{
  "users": [
    {"id": 1, "name": "John"},
    {"id": 2, "name": "Jane"}
  ]
}
```

### POST /api/users
Create a new user.

**Request:**
```json
{
  "name": "New User"
}
```

**Response:**
```json
{
  "id": 3,
  "name": "New User"
}
```

## Authentication
Basic authentication using API keys.

## Error Handling
Standard HTTP status codes will be used.
