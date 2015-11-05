# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0008_add_briefing_text_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactPerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, verbose_name='name')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('facility', models.ForeignKey(related_name='+', verbose_name='facility', to='organizations.Facility')),
                ('member', models.ForeignKey(related_name='+', verbose_name='member', blank=True, to='organizations.FacilityMembership', null=True)),
            ],
            options={
                'ordering': ('facility', 'name', 'email'),
                'verbose_name': 'contact person',
                'verbose_name_plural': 'contact persons',
            },
        ),
        migrations.AddField(
            model_name='facility',
            name='shift_contact',
            field=models.ForeignKey(related_name='+', blank=True, to='organizations.ContactPerson', help_text='Contact person to share with shift helpers.', null=True, verbose_name='contact person'),
        ),
        migrations.AddField(
            model_name='task',
            name='shift_contact',
            field=models.ForeignKey(related_name='+', blank=True, to='organizations.ContactPerson', help_text='Contact person to share with shift helpers.', null=True, verbose_name='contact person'),
        ),
        migrations.AddField(
            model_name='workplace',
            name='shift_contact',
            field=models.ForeignKey(related_name='+', blank=True, to='organizations.ContactPerson', help_text='Contact person to share with shift helpers.', null=True, verbose_name='contact person'),
        ),
        migrations.AlterUniqueTogether(
            name='contactperson',
            unique_together=set([('facility', 'email'), ('facility', 'member')]),
        ),
    ]
