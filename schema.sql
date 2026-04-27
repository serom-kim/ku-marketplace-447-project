DROP DATABASE IF EXISTS student_marketplace;
CREATE DATABASE student_marketplace;
USE student_marketplace;

CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    ContactInfo VARCHAR(255)
);

CREATE TABLE Categories (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE Listings (
    ListingID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(150) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL CHECK (Price >= 0),
    ItemCondition VARCHAR(50),
    Status ENUM('available', 'sold') NOT NULL DEFAULT 'available',
    SellerID INT NOT NULL,
    CategoryID INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SellerID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE RESTRICT
);

CREATE TABLE Messages (
    MessageID INT AUTO_INCREMENT PRIMARY KEY,
    BuyerID INT NOT NULL,
    SellerID INT NOT NULL,
    ListingID INT NOT NULL,
    MessageContent TEXT NOT NULL,
    SentAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (BuyerID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (SellerID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ListingID) REFERENCES Listings(ListingID) ON DELETE CASCADE
);

CREATE TABLE Transactions (
    TransactionID INT AUTO_INCREMENT PRIMARY KEY,
    ListingID INT NOT NULL UNIQUE,
    BuyerID INT NOT NULL,
    PurchaseDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FinalPrice DECIMAL(10,2) NOT NULL CHECK (FinalPrice >= 0),
    FOREIGN KEY (ListingID) REFERENCES Listings(ListingID) ON DELETE CASCADE,
    FOREIGN KEY (BuyerID) REFERENCES Users(UserID) ON DELETE CASCADE
);

CREATE TABLE Listing_Images (
    ImageID INT AUTO_INCREMENT PRIMARY KEY,
    ListingID INT NOT NULL,
    ImageURL VARCHAR(500) NOT NULL,
    FOREIGN KEY (ListingID) REFERENCES Listings(ListingID) ON DELETE CASCADE
);

CREATE TABLE Saved (
    UserID INT NOT NULL,
    ListingID INT NOT NULL,
    SavedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (UserID, ListingID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ListingID) REFERENCES Listings(ListingID) ON DELETE CASCADE
);

INSERT INTO Categories (CategoryName) VALUES
('Furniture'),
('Technology'),
('School Supplies'),
('Clothing'),
('Home'),
('Other');

-- Demo password for both users is: pass
INSERT INTO Users (Name, Email, PasswordHash, ContactInfo) VALUES
('Serom Kim', 'serom@ku.edu', 'scrypt:32768:8:1$FZJn2rhHkRhxxuQ4$6bb696c102e6d9313e4ebc2eed3c88755e2a51bf54acc3e43a4e3be78623e2bec05526ea80125c0a02694e759a615fc2303c0f1958c92fa3e02fa2b3811dc16', 'serom@ku.edu'),
('Meg Taggart', 'meg@ku.edu', 'scrypt:32768:8:1$FZJn2rhHkRhxxuQ4$6bb696c102e6d9313e4ebc2eed3c88755e2a51bf54acc3e43a4e3be78623e2bec05526ea80125c0a02694e759a615fc2303c0f1958c92fa3e02fa2b3811dc16', 'meg@ku.edu');

INSERT INTO Listings (Title, Description, Price, ItemCondition, Status, SellerID, CategoryID) VALUES
('Matcha Whisk and Bowl', 'Beautiful matcha whisk and ceramic bowl for at home use.', 45.00, 'Good', 'available', 1, 5),
('Candle', 'Used candle. Smells good. Still a little bit of wax left.', 10.00, 'Used', 'available', 2, 5),
('Billiards Clock', 'Vintage billiards clock. Requires battery.', 25.00, 'Good', 'available', 1, 5),
('Leather Jacket', 'Mens XS brown leather jacket from Abercrombie. Cropped/boxy fit.', 50.00, 'Good', 'available', 2, 4),
('Snoopy squishmallow', 'Cute snoopy plushie.', 10.00, 'Good', 'available', 1, 6),
('Toilet paper', 'Half of the roll is gone but great quality TP.', 3.00, 'Like New', 'available', 2, 5),
('Vintage Lamp', 'Handmade vintage-style stained glass lamp. Originally paid $350.', 200.00, 'Good', 'available', 1, 1),
('Dog', 'Cute dog up for grabs! She is very silly and friendly and charming.', 100.00, 'Good', 'available', 2, 6),
('Vintage hot wheel toy', 'Got it from a garage sale. Unopened.', 12.00, 'Good', 'available', 1, 6);

INSERT INTO Listing_Images (ListingID, ImageURL) VALUES
(1, '/static/uploads/matcha_set.JPG'),
(2, '/static/uploads/candle.JPG'),
(3, '/static/uploads/clock.JPG'),
(4, '/static/uploads/leather_jacket.JPG'),
(5, '/static/uploads/squishmallow.JPG'),
(6, '/static/uploads/toilet_paper.JPG'),
(7, '/static/uploads/lamp.JPG'),
(8, '/static/uploads/dog.jpg'),
(9, '/static/uploads/hot_wheel.JPG');