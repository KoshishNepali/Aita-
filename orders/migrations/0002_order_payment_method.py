# Generated migration for adding payment_method to Order model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('esewa', 'eSewa'), ('cod', 'Cash on Delivery')],
                default='esewa',
                max_length=20
            ),
        ),
    ]
