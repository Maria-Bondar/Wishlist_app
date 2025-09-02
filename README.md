# 🎁 Wishlist App

A small Django application for creating wishlists that can be shared with friends.
Users can register, create profiles, add their own preferences (likes and dislikes), and manage gift lists.
---

## 🚀 Functionality

### 🔐 Users and accounts
- Registration with confirmation via email.
- Login/logout using email and password.
- Also project includes the ability to log in using a Google account (OAuth 2.0).
- Personal profile with the ability to edit:
  - upload an avatar;
  - add "likes" 🎁 and "dislikes" 🚫 (with automatic emojis);
- View the profiles of other users.

### 📋 Wishlists
- Create, edit and delete wishlists.
- Ability to add a cover to the list.
- View your own wishlists on the main page.
- Public access to the list via a unique code (share link).

### 🎁 Items
- Adding products manually or via a link to the store:
  - automatic parsing of the name, price and photo from the site 🛍️;
- Editing and deleting products;
- Viewing detailed information about the gift;
- Ability reservation of gifts.

### 👥 Friends
- Automatically save wishlists shared by friends.
- Separate page for viewing friends lists.
- Reservation of gifts by friends secretly (owner can't see who reserve gift) with the ability to cancel.

---

## 🖼️ Скріншоти

- **Registration page**
  ![Registration screenshot](wishlist_app/screenshots/register.png)

- **All wishlists / main page**
  ![Wishlists screenshot](wishlist_app/screenshots/my_wishlists.png)

- **User profile**
  ![Profile screenshot](wishlist_app/screenshots/profile.png)

- **Wishlist example**
  ![One wishlist screenshot](wishlist_app/screenshots/wishlist.png)

- **Adding new item to wishlist**
  ![Add item screenshot](wishlist_app/screenshots/adding_item.png)

- **Friends wishlists**
  ![Friends wishlist screenshot](wishlist_app/screenshots/friends_wishlists.png)

- **Wishlist with reserved gifts**
  ![Reserved items screenshot](wishlist_app/screenshots/reserved_gifts.png)
---
