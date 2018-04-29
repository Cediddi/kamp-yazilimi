
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mudur', '0007_auto_20160815_1457'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('operation_name', models.CharField(unique=True, max_length=200, verbose_name='Fonksiyon ismi')),
                ('subject', models.CharField(max_length=300, verbose_name='Konu')),
                ('body_html', models.TextField(max_length=2000, verbose_name='HTML E-posta Govdesi')),
                ('site', models.ForeignKey(to='mudur.Site')),
            ],
            options={
                'verbose_name': 'E-posta sablonu',
                'verbose_name_plural': 'E-posta sablonlari',
            },
        ),
    ]
