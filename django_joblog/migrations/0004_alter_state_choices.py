# Generated by Django 2.2 on 2019-04-29 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_joblog', '0003_alter_state_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='joblogmodel',
            name='state',
            field=models.CharField(choices=[('running', '▶ running'), ('finished', '✔ finished'), ('error', '❌ error'), ('blocked', '🖐 blocked'), ('vanished', '⊙ vanished')], db_index=True, default='running', editable=False, max_length=64, verbose_name='state'),
        ),
    ]
