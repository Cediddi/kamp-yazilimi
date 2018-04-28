
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mudur', '0009_auto_20160817_1429'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='needs_document',
            field=models.BooleanField(default=True, verbose_name='Site requires document'),
        ),
    ]
