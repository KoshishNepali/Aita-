from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):

    OPTION_TYPE_CHOICES = [
        ('none', 'No Option'),
        ('quantity', 'Quantity'),
        ('size', 'Size'),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
    )

    option_type = models.CharField(
        max_length=20,
        choices=OPTION_TYPE_CHOICES,
        default='none'
    )

    options = models.TextField(
        blank=True,
        help_text="Example: 6pcs:500,12pcs:900 OR Small:400,Medium:600"
    )

    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def image_src(self):
        if not self.image:
            return ''
        value = str(self.image)
        if value.startswith('http://') or value.startswith('https://'):
            return value
        return self.image.url

    def __str__(self):
        return self.name