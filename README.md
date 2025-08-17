# Flask Distribution API

A RESTful API built with **Flask** and **MySQL** for managing customers, items, order guides, and orders.  
Originally designed for a distribution company, this API connects directly to a MySQL database and integrates with external vendor APIs for token-based authentication and order posting.  

## Features

- **Customer Management**
  - Retrieve customer master records
  - Fetch accounts receivable (AR) details
  - Search customer orders with filtering by date

- **Item Management**
  - Retrieve item master data
  - Keyword-based item search with ranking
  - Get on-hand inventory and stock status

- **Order Guides**
  - Retrieve customer-specific order guides
  - Post new order guides with items
  - Manage item pricing per customer

- **Orders**
  - Post new customer orders
  - Fetch existing orders with filters
  - Delete orders
  - Retrieve real-time order status
  - Track customer order velocity

- **Logging**
  - Log customer searches and selected items for auditing

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** MySQL
- **Server:** Waitress WSGI
- **Auth:** External vendor API token generation
- **CORS:** Enabled via Flask-CORS


## Notes

-This project has been scrubbed of sensitive information.
-Original deployment included vendor API integration for order posting and validation.
-Can be extended for any distribution or inventory-based business.
