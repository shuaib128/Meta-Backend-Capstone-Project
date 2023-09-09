from django.db import models
from django.contrib.auth.models import User

# The Category model represents the various categories under which menu items can be classified.
# For example, categories like "Starters", "Mains", "Desserts", etc.
class Category(models.Model):
    slug = models.SlugField()  # A unique slug for URL purposes.
    title = models.CharField(max_length=255, db_index=True)  # The name of the category.
    
    def __str__(self):
        return self.title

# MenuItem model represents individual food items or dishes that can be ordered by users.
class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)  # The name of the menu item.
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)  # Price of the item.
    featured = models.BooleanField(db_index=True)  # Indicates if the menu item is featured or special.
    category = models.ForeignKey(Category, on_delete=models.PROTECT)  # Link to the category this item belongs to.
    
    def __str__(self):
        return self.title

# The Cart model holds the items that a user adds to their shopping cart before checkout.
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who owns this cart.
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)  # The menu item added to the cart.
    quantity = models.IntegerField()  # Quantity of the menu item in the cart.
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)  # Price per unit of the menu item.
    price = models.DecimalField(max_digits=6, decimal_places=2)  # Total price (quantity x unit price).

    class Meta():
        unique_together = ('menuitem', 'user')  # Ensuring a user can't add the same item to cart multiple times.
    
    def __str__(self):
        return str(self.user)

# The Order model represents the final order made by the user.
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who placed the order.
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True, limit_choices_to={'groups__name': "Delivery crew"})  # The crew assigned to deliver the order.
    status = models.BooleanField(db_index=True, default=0)  # Order status (0: Not Delivered, 1: Delivered).
    total = models.DecimalField(max_digits=6, decimal_places=2)  # Total price of the order.
    date = models.DateField(db_index=True)  # Date when the order was placed.

    def __str__(self):
        return str(self.id)

# OrderItem model represents individual items within an order.
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Link to the main order.
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)  # The specific menu item.
    quantity = models.SmallIntegerField()  # Quantity of this item in the order.

    # Commented out attributes may have been meant for individual pricing per order item.
    # unit_price = models.DecimalField(max_digits=6, decimal_places=2) 
    # price = models.DecimalField(max_digits=6,decimal_places=2) 

    class Meta():
        unique_together = ('order', 'menuitem')  # Ensuring an item can't be added multiple times to the same order.
