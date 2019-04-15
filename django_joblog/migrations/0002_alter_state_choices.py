# Generated by Django 2.2 on 2019-04-15 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_joblog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='joblogmodel',
            name='state',
            field=models.CharField(choices=[('running', '▶ running'), ('finished', '✔ finished'), ('error', '❌ error'), ('halted', '❎ halted')], db_index=True, default='running', editable=False, max_length=64, verbose_name='state'),
        ),
    ]
