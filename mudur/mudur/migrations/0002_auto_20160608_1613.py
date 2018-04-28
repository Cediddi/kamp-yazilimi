
from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('mudur', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='event_end_date',
            field=models.DateField(default=datetime.datetime.now, verbose_name='Event End Date'),
        ),
        migrations.AddField(
            model_name='site',
            name='event_start_date',
            field=models.DateField(default=datetime.datetime.now, verbose_name='Event Start Date'),
        ),
    ]
