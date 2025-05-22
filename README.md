# Walmart Scraper

A Python project to scrape subcategories and product details from Walmart and store it in a MySQL database.

## Database Schema

### Subcategories Table
```sql
CREATE TABLE subcategories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(1000) NOT NULL,
    category_url VARCHAR(1000) NOT NULL,
    subcategory_name VARCHAR(1000) NOT NULL,
    subcategory_url VARCHAR(1000) NOT NULL,
    STATUS ENUM('pending', 'done') NOT NULL DEFAULT 'pending'
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(64),
    upc VARCHAR(64),
    product_id VARCHAR(64),
    url TEXT,
    NAME VARCHAR(1000),
    categories JSON,
    image TEXT,
    store_id VARCHAR(64),
    store_location VARCHAR(255),
    price VARCHAR(64),
    mrp VARCHAR(64),
    discount VARCHAR(32),
    availability VARCHAR(32),
    keyword VARCHAR(255),
    size VARCHAR(64)
);
```

## Setup Instructions

Clone the repository:
```
git clone https://github.com/arvind-actowiz/walmart.git
cd walmart
```

Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Create a .env file based on .env.example and configure your database connection:
```
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Set up your MySQL database with the provided schema.
