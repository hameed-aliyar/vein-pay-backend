# VeinPay: Biometric Payment API

A Django REST Framework backend for a point-of-sale payment system using digital wallets, powered by biometric (face) authentication. This project serves as the complete server-side logic for a multi-frontend application (e.g., a Flutter app for customers and a React dashboard for shops).

## Features

* Digital Wallet System: Customers and shops have wallets with balance management.
* Role-Based Access: Distinct API endpoints and permissions for Customers and Shop Owners.
* Biometric Payment Flow: A secure payment process authenticated via facial recognition instead of a PIN.
* Modular Authentication: Includes a working proof-of-concept using OpenCV/Haar Cascades, with stubs for future integration of vein scanning or other methods.
* Token-Based Authentication: Uses JWT (JSON Web Tokens) for secure, stateless API communication.

## Tech Stack

* Backend: Django, Django REST Framework
* Database: PostgreSQL
* Authentication: SimpleJWT (JSON Web Tokens)
* Computer Vision: OpenCV
* Environment Management: python-decouple

## Project Setup

Instructions for a new developer to get the project running locally.

### 1. Prerequisites

* Python 3.10+
* PostgreSQL
* Git

### 2. Clone the Repository

```bash
git clone https://github.com/hameed-aliyar/vein-pay-backend.git
cd vein-pay-backend
```

### 3. Set Up the Environment

```bash
# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Configure the Database

Create a new PostgreSQL database and a user with login privileges.
Create a `.env` file in the project root by copying the `.env.example` file.
Fill in your database credentials and a new Django SECRET_KEY in the `.env` file.

```env
SECRET_KEY=your_secret_key
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### 5. Run Migrations & Start the Server

```bash
# Apply database migrations
python manage.py migrate

# Create a superuser for the admin panel
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

The API is now running at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## API Reference Guide

### Authentication

**Login (Get Token)**
Endpoint: `POST /api/auth/login/`
Body:

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response: access and refresh tokens.

---

### Customer API (Authorization: Bearer <Customer_Token>)

* **Get Wallet Details**
  Endpoint: `GET /api/wallet/`

* **Add Funds to Wallet**
  Endpoint: `POST /api/wallet/add/`
  Body:

```json
{
    "amount": "100.50"
}
```

---

### Shop Owner API (Authorization: Bearer <Shop_Owner_Token>)

* **List/Create Customers**

  * Endpoint: `GET /api/shop/customers/` (to list)
  * Endpoint: `POST /api/shop/customers/` (to create)
    Body (for POST, multipart/form-data):

  ```text
  username: new_customer_name
  password: new_password
  biometric_type: FACE
  face_template: (File Upload)
  ```

* **List/Create Bills**

  * Endpoint: `GET /api/shop/bills/` (to list)
  * Endpoint: `POST /api/shop/bills/` (to create)
    Body (for POST):

  ```json
  {
      "customer": 12,
      "amount": "99.99"
  }
  ```

* **Mark Bill as Paid in Cash**
  Endpoint: `PUT /api/shop/bills/<id>/pay-cash/`

---

### Payment API (Authorization: Bearer <Shop_Owner_Token>)

* **Process Biometric Payment**
  Endpoint: `POST /api/pay/`
  Body (multipart/form-data):

  ```text
  bill_id: 1
  live_image: (File Upload of captured face)
  ```

Response: Success or failure message.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Customer as Customer (Flutter App)
    participant ShopOwner as Shop Owner (React App)
    participant Backend as Django Backend
    participant DB as Database

    Note over Customer, ShopOwner: Both login to get an Access & Refresh Token
    Customer->>Backend: POST /api/auth/login/
    activate Backend
    Backend->>DB: Verify credentials
    activate DB
    DB-->>Backend: User OK
    deactivate DB
    Backend-->>Customer: Returns Tokens
    deactivate Backend

    ShopOwner->>Backend: POST /api/auth/login/
    activate Backend
    Backend->>DB: Verify credentials
    activate DB
    DB-->>Backend: Shop Owner OK
    deactivate DB
    Backend-->>ShopOwner: Returns Tokens
    deactivate Backend

    Note over Backend, Customer: (Token refresh happens as needed)
    Customer->>Backend: POST /api/auth/token/refresh/
    activate Backend
    Backend->>DB: Verify refresh token
    activate DB
    DB-->>Backend: Token OK
    deactivate DB
    Backend-->>Customer: New Access Token
    deactivate Backend

    Note over Customer: Customer manages their wallet
    Customer->>Backend: GET /api/wallet/
    activate Backend
    Backend->>DB: SELECT wallet for user
    activate DB
    DB-->>Backend: Wallet data
    deactivate DB
    Backend-->>Customer: Wallet details
    deactivate Backend

    Customer->>Backend: POST /api/wallet/add/ (with amount)
    activate Backend
    Backend->>DB: UPDATE wallet balance
    activate DB
    DB-->>Backend: Update OK
    deactivate DB
    Backend-->>Customer: Updated wallet details
    deactivate Backend

    Customer->>Backend: GET /api/wallet/transactions/
    activate Backend
    Backend->>DB: SELECT transactions for user
    activate DB
    DB-->>Backend: Transaction list
    deactivate DB
    Backend-->>Customer: List of transactions
    deactivate Backend

    Note over ShopOwner: Shop Owner manages their dashboard
    ShopOwner->>Backend: POST /api/shop/customers/ (user data + image)
    activate Backend
    Backend->>DB: CREATE User, Wallet, BiometricData
    activate DB
    DB-->>Backend: Creation OK
    deactivate DB
    Backend-->>ShopOwner: 201 Created
    deactivate Backend

    ShopOwner->>Backend: GET /api/shop/customers/
    activate Backend
    Backend->>DB: SELECT all customers
    activate DB
    DB-->>Backend: Customer List
    deactivate DB
    Backend-->>ShopOwner: List of all customers
    deactivate Backend

    ShopOwner->>Backend: POST /api/shop/bills/ (with data)
    activate Backend
    Backend->>DB: CREATE Bill
    activate DB
    DB-->>Backend: Bill Created
    deactivate DB
    Backend-->>ShopOwner: Bill Created
    deactivate Backend

    ShopOwner->>Backend: GET /api/shop/bills/
    activate Backend
    Backend->>DB: SELECT all bills for shop
    activate DB
    DB-->>Backend: Bill List
    deactivate DB
    Backend-->>ShopOwner: List of all bills
    deactivate Backend

    Note over ShopOwner, Backend: Shop Owner chooses a payment method for a bill

    alt Pay with Cash
        ShopOwner->>Backend: PUT /api/shop/bills/X/pay-cash/
        activate Backend
        Backend->>DB: UPDATE bill status to 'PAID_CASH'
        activate DB
        DB-->>Backend: Update OK
        deactivate DB
        Backend-->>ShopOwner: Success message
        deactivate Backend
    end

    alt Pay with Biometrics
        Note over ShopOwner: Captures live biometric via Webcam/Pi
        ShopOwner->>Backend: POST /api/pay/ (with bill_id, live_image)
        activate Backend
        Backend->>DB: Fetch stored biometric template for user
        activate DB
        DB-->>Backend: Template data
        deactivate DB
        
        Note over Backend: Compares biometrics... (Match is found)
        
        Backend->>DB: Perform atomic wallet transfer (Debit/Credit)
        activate DB
        DB-->>Backend: Transaction OK
        deactivate DB
        Backend-->>ShopOwner: 200 OK (Payment Successful)
        deactivate Backend
    end
```

