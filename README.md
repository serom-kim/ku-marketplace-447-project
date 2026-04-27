# Student Marketplace MVP

A simple Facebook Marketplace-style web app for a database class project.

## Features

- User registration and login using Flask sessions
- MySQL database with normalized relational tables
- Create, view, update, and delete listings
- Seller-only permissions for editing/deleting/marking sold
- Search listings by keyword, category, price, and seller
- View listing details and seller contact info
- Send messages to sellers
- Save/unsave listings
- Mark listings as sold and create transaction records
- Homepage is already populated with sample available products

## Setup

```bash
pip install -r requirements.txt
mysql -u root -p < schema.sql
cp .env.example .env
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Demo accounts

Both demo accounts use:

```text
password123
```

- serom@ku.edu
- meg@ku.edu

## Running Serom and Meg at the same time

Two normal tabs in the same browser usually share the same Flask session, so they will not stay logged in as different users.

Use one of these:

```text
Window 1: normal browser window logged in as Serom
Window 2: incognito/private browser window logged in as Meg
```

or:

```text
Window 1: Chrome logged in as Serom
Window 2: Edge/Firefox logged in as Meg
```

## Good demo flow

1. Open the homepage and show that listings already exist.
2. Log in as Serom in a normal browser window.
3. Log in as Meg in an incognito/private window or another browser.
4. As Meg, browse/search listings.
5. As Meg, open one of Serom's listings.
6. As Meg, save the listing and message Serom.
7. As Serom, open Messages and show Meg's message.
8. As Serom, open My Listings.
9. As Serom, edit one listing.
10. As Serom, mark one listing as sold to Meg.
11. Open Transactions and show that the purchase was recorded.
