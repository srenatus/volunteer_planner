# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0007_auto_20151023_2129'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='email_briefing',
            field=models.TextField(default='', help_text='Additional information, which is sent to users enrolling for a shift.', verbose_name='email briefing', blank=True),
        ),
        migrations.AddField(
            model_name='task',
            name='email_briefing',
            field=models.TextField(default='', help_text='Additional information, which is sent to users enrolling for a shift.', verbose_name='email briefing', blank=True),
        ),
        migrations.AddField(
            model_name='workplace',
            name='email_briefing',
            field=models.TextField(default='', help_text='Additional information, which is sent to users enrolling for a shift.', verbose_name='email briefing', blank=True),
        ),
    ]
