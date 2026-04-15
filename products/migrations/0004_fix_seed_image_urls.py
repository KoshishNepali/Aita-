from django.db import migrations


BROKEN_IMAGE_REPLACEMENTS = {
    'Salmon Avocado Roll': 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=1200&q=80',
    'Rainbow Roll': 'https://images.pexels.com/photos/357756/pexels-photo-357756.jpeg?auto=compress&cs=tinysrgb&w=1200',
    'Poke Bowl': 'https://images.pexels.com/photos/674574/pexels-photo-674574.jpeg?auto=compress&cs=tinysrgb&w=1200',
    'Spicy Salmon Poke Bowl': 'https://images.unsplash.com/photo-1553621042-f6e147245754?auto=format&fit=crop&w=1200&q=80',
    'Katsu Curry Bowl': 'https://images.pexels.com/photos/842571/pexels-photo-842571.jpeg?auto=compress&cs=tinysrgb&w=1200',
    'Veggie Zen Bowl': 'https://images.pexels.com/photos/1640774/pexels-photo-1640774.jpeg?auto=compress&cs=tinysrgb&w=1200',
    'Shrimp Yakisoba Bowl': 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?auto=format&fit=crop&w=1200&q=80',
}


def fix_product_images(apps, schema_editor):
    Product = apps.get_model('products', 'Product')

    for product_name, replacement_url in BROKEN_IMAGE_REPLACEMENTS.items():
        Product.objects.filter(name=product_name).update(image=replacement_url)


def revert_product_images(apps, schema_editor):
    # No-op reverse to avoid reintroducing known broken external image links.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_seed_products'),
    ]

    operations = [
        migrations.RunPython(fix_product_images, revert_product_images),
    ]
