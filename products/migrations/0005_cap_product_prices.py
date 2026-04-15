from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def cap_product_prices(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(base_price__gt=Decimal('300.00')).update(base_price=Decimal('300.00'))


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_fix_seed_image_urls'),
    ]

    operations = [
        migrations.RunPython(cap_product_prices, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='base_price',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=8,
                validators=[MinValueValidator(0), MaxValueValidator(300)],
            ),
        ),
    ]
