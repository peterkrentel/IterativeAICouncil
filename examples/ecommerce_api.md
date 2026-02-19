# E-Commerce API Design

## Overview
Design for a RESTful API for an e-commerce platform.

## Core Requirements
- User authentication and authorization
- Product catalog management
- Shopping cart functionality
- Order processing
- Payment integration

## API Endpoints

### Authentication
**POST /api/auth/login**
- Authenticate user
- Return JWT token

**POST /api/auth/register**
- Register new user
- Return user ID

### Products
**GET /api/products**
- List all products
- Support pagination and filtering

**GET /api/products/{id}**
- Get product details

**POST /api/products**
- Create new product (admin only)

### Shopping Cart
**GET /api/cart**
- Get current user's cart

**POST /api/cart/items**
- Add item to cart

**DELETE /api/cart/items/{id}**
- Remove item from cart

### Orders
**POST /api/orders**
- Create order from cart
- Process payment
- Return order ID

**GET /api/orders/{id}**
- Get order status

## Data Models

### User
```json
{
  "id": "string",
  "email": "string",
  "name": "string",
  "role": "customer|admin"
}
```

### Product
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "price": "number",
  "inventory": "number"
}
```

### Order
```json
{
  "id": "string",
  "userId": "string",
  "items": "array",
  "total": "number",
  "status": "pending|completed|cancelled"
}
```

## Authentication
JWT-based authentication with Bearer tokens.

## Error Handling
Standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Server Error
