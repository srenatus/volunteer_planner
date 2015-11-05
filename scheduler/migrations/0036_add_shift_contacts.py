# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0009_add_shift_contacts'),
        ('scheduler', '0035_delete_topics_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='shift_contact',
            field=models.ForeignKey(related_name='+', blank=True, to='organizations.ContactPerson', help_text='Contact person to share with shift helpers.', null=True, verbose_name='contact person'),
        ),
    ]
