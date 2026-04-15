from datetime import timedelta
from decimal import Decimal

from django.db import migrations
from django.utils import timezone


PRODUCTS = [
    {
        'name': 'Salmon Sushi',
        'description': 'Fresh salmon over seasoned sushi rice.',
        'base_price': Decimal('8.99'),
        'category': 'sushi',
        'image': 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Tuna Nigiri',
        'description': 'Classic tuna nigiri with light wasabi.',
        'base_price': Decimal('9.50'),
        'category': 'sushi',
        'image': 'https://images.pexels.com/photos/357756/pexels-photo-357756.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Dragon Roll',
        'description': 'Eel and cucumber roll topped with avocado.',
        'base_price': Decimal('12.50'),
        'category': 'sushi',
        'image': 'https://cdn.pixabay.com/photo/2016/03/05/19/02/hamburger-1238246_1280.jpg',
    },
    {
        'name': 'Spicy Tuna Roll',
        'description': 'Tuna with chili mayo and crunchy tempura flakes.',
        'base_price': Decimal('10.25'),
        'category': 'sushi',
        'image': 'https://images.unsplash.com/photo-1553621042-f6e147245754?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'California Roll',
        'description': 'Crab, avocado, and cucumber in a soft maki roll.',
        'base_price': Decimal('8.75'),
        'category': 'sushi',
        'image': 'https://images.pexels.com/photos/2098085/pexels-photo-2098085.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Shrimp Tempura Roll',
        'description': 'Crispy shrimp tempura roll with house sauce.',
        'base_price': Decimal('11.50'),
        'category': 'sushi',
        'image': 'https://cdn.pixabay.com/photo/2017/05/07/08/56/pancakes-2291908_1280.jpg',
    },
    {
        'name': 'Ebi Nigiri',
        'description': 'Sweet poached shrimp over hand-pressed rice.',
        'base_price': Decimal('9.25'),
        'category': 'sushi',
        'image': 'https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Unagi Roll',
        'description': 'Grilled eel roll glazed with rich unagi sauce.',
        'base_price': Decimal('13.50'),
        'category': 'sushi',
        'image': 'https://images.pexels.com/photos/8951199/pexels-photo-8951199.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Salmon Avocado Roll',
        'description': 'Buttery salmon and ripe avocado wrapped in nori.',
        'base_price': Decimal('10.75'),
        'category': 'sushi',
        'image': 'https://cdn.pixabay.com/photo/2014/10/22/18/12/sushi-498405_1280.jpg',
    },
    {
        'name': 'Rainbow Roll',
        'description': 'Colorful roll layered with assorted fresh fish.',
        'base_price': Decimal('14.00'),
        'category': 'sushi',
        'image': 'https://images.unsplash.com/photo-1582450871972-ab5ca7f5f1f8?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Teriyaki Chicken Bowl',
        'description': 'Grilled chicken, steamed rice, and teriyaki glaze.',
        'base_price': Decimal('11.25'),
        'category': 'bowls',
        'image': 'https://images.pexels.com/photos/1640774/pexels-photo-1640774.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Poke Bowl',
        'description': 'Ahi tuna poke with edamame, mango, and sesame.',
        'base_price': Decimal('13.75'),
        'category': 'bowls',
        'image': 'https://cdn.pixabay.com/photo/2020/08/03/09/06/salmon-5458895_1280.jpg',
    },
    {
        'name': 'Beef Bulgogi Bowl',
        'description': 'Sweet soy marinated beef with kimchi and rice.',
        'base_price': Decimal('12.95'),
        'category': 'bowls',
        'image': 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Tofu Teriyaki Bowl',
        'description': 'Crispy tofu, stir-fried veggies, and jasmine rice.',
        'base_price': Decimal('10.50'),
        'category': 'bowls',
        'image': 'https://images.pexels.com/photos/674574/pexels-photo-674574.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Spicy Salmon Poke Bowl',
        'description': 'Diced salmon in spicy mayo with cucumber and seaweed.',
        'base_price': Decimal('14.50'),
        'category': 'bowls',
        'image': 'https://cdn.pixabay.com/photo/2016/11/18/15/07/salmon-1839708_1280.jpg',
    },
    {
        'name': 'Katsu Curry Bowl',
        'description': 'Panko chicken cutlet with Japanese curry sauce.',
        'base_price': Decimal('12.25'),
        'category': 'bowls',
        'image': 'https://images.unsplash.com/photo-1604908176997-431f2d5f2f62?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Miso Glazed Salmon Bowl',
        'description': 'Oven glazed salmon with greens and sushi rice.',
        'base_price': Decimal('15.00'),
        'category': 'bowls',
        'image': 'https://images.pexels.com/photos/842571/pexels-photo-842571.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
    {
        'name': 'Veggie Zen Bowl',
        'description': 'Seasonal vegetables, avocado, and sesame dressing.',
        'base_price': Decimal('9.95'),
        'category': 'bowls',
        'image': 'https://cdn.pixabay.com/photo/2017/04/23/15/14/salad-2253970_1280.jpg',
    },
    {
        'name': 'Shrimp Yakisoba Bowl',
        'description': 'Wok-tossed noodles with shrimp and mixed vegetables.',
        'base_price': Decimal('13.25'),
        'category': 'bowls',
        'image': 'https://images.unsplash.com/photo-1617191519507-0b89f8310db7?auto=format&fit=crop&w=1200&q=80',
    },
    {
        'name': 'Kimchi Fried Rice Bowl',
        'description': 'Savory fried rice with kimchi, egg, and scallions.',
        'base_price': Decimal('10.95'),
        'category': 'bowls',
        'image': 'https://images.pexels.com/photos/2338407/pexels-photo-2338407.jpeg?auto=compress&cs=tinysrgb&w=1200',
    },
]


def seed_products(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')

    category_map = {
        'sushi': Category.objects.get_or_create(name='sushi')[0],
        'bowls': Category.objects.get_or_create(name='bowls')[0],
    }

    now = timezone.now()
    for index, item in enumerate(PRODUCTS):
        product, created = Product.objects.get_or_create(
            name=item['name'],
            defaults={
                'description': item['description'],
                'base_price': item['base_price'],
                'category': category_map[item['category']],
                'image': item['image'],
                'option_type': 'none',
                'options': '',
                'is_available': True,
            },
        )

        if created:
            Product.objects.filter(pk=product.pk).update(
                created_at=now - timedelta(days=(index + 1) * 2)
            )


def unseed_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    product_names = [item['name'] for item in PRODUCTS]
    Product.objects.filter(name__in=product_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_created_at'),
    ]

    operations = [
        migrations.RunPython(seed_products, unseed_products),
    ]
