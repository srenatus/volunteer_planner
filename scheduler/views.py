# coding: utf-8

import HTMLParser
import itertools
import json
import logging
from datetime import date

from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import date as date_filter, striptags
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, FormView, DetailView

from accounts.models import UserAccount
from organizations.models import Facility
from organizations.views import get_facility_details
from scheduler.models import Shift
from scheduler.models import ShiftHelper
from volunteer_planner.utils import LoginRequiredMixin
from .forms import RegisterForShiftForm

logger = logging.getLogger(__name__)

import re

a_nodes = re.compile(r'(<a\s.*href\s*=\s*.*>.*<\s*/\s*a\s*>)', re.IGNORECASE)
href_value = re.compile(r'.*href\s*=\s*[\'"](?:[a-z]+\:\s*)?([^\'" >]+)',
                        re.IGNORECASE)


def replace_links(string, raise_errors=False):
    """
    Returns new string with all occurences of HTML a href tags replaced with the
    value of the href attribute.
    """
    links = a_nodes.findall(string)

    result = u'{}'.format(string)
    for link in links:
        try:
            hrefs = href_value.findall(link)
            if hrefs:
                result = result.replace(link, hrefs[0])
        except:
            if raise_errors:
                raise
    return result


def get_open_shifts():
    shifts = Shift.open_shifts.all()
    shifts = shifts.select_related('facility',
                                   'facility__place',
                                   'facility__place__area',
                                   'facility__place__area__region',
                                   'facility__place__area__region__country',
                                   )

    shifts = shifts.order_by('facility__place__area__region__country',
                             'facility__place__area__region',
                             'facility__place__area',
                             'facility__place',
                             'facility',
                             'starting_time',
                             )
    return shifts


class HelpDesk(LoginRequiredMixin, TemplateView):
    """
    Facility overview. First view that a volunteer gets redirected to when they log in.
    """
    template_name = "helpdesk.html"

    @staticmethod
    def serialize_news(news_entries):
        return [dict(title=news_entry.title,
                     date=news_entry.creation_date,
                     text=news_entry.text) for news_entry in news_entries]

    def get_context_data(self, **kwargs):
        context = super(HelpDesk, self).get_context_data(**kwargs)
        open_shifts = get_open_shifts()
        shifts_by_facility = itertools.groupby(open_shifts,
                                               lambda s: s.facility)

        facility_list = []
        used_places = set()

        for facility, shifts_at_facility in shifts_by_facility:
            used_places.add(facility.place.area)
            facility_list.append(
                get_facility_details(facility, shifts_at_facility))

        context['areas_json'] = json.dumps(
            [{'slug': area.slug, 'name': area.name} for area in
             sorted(used_places, key=lambda p: p.name)])
        context['facility_json'] = json.dumps(facility_list,
                                              cls=DjangoJSONEncoder)
        context['shifts'] = open_shifts
        return context


class GeographicHelpdeskView(DetailView):
    template_name = 'geographic_helpdesk.html'
    context_object_name = 'geographical_unit'

    @staticmethod
    def make_breadcrumps_dict(country, region=None, area=None,
                              place=None):

        result = dict(country=country, flattened=[country, ])

        for k, v in zip(('region', 'area', 'place'), (region, area, place)):
            if v:
                result[k] = v
                result['flattened'].append(v)

        return result

    def get_queryset(self):
        return super(GeographicHelpdeskView,
                     self).get_queryset().select_related(
            *self.model.get_select_related_list())

    def get_context_data(self, **kwargs):
        context = super(GeographicHelpdeskView, self).get_context_data(**kwargs)
        place = self.object
        context['breadcrumps'] = self.make_breadcrumps_dict(*place.breadcrumps)
        context['shifts'] = get_open_shifts().by_geography(place)
        return context


def send_briefing_mail(shift_helper):
    shift = shift_helper.shift
    user = shift_helper.user_account.user
    if user.email:
        subject = _(
            u'Your shift on {}'.format(
                date_filter(shift.starting_time.date)))

        username = user.first_name or user.username
        no_details_placeholder = u'--- {} ---'.format(
            _(u'No further details available'))

        html_parser = HTMLParser.HTMLParser()
        facility_briefing, \
        task_briefing, \
        workplace_briefing = [
            (mark_safe(striptags(obj.email_briefing
                                 or replace_links(obj.description)).strip())
             or no_details_placeholder)
            if obj else no_details_placeholder
            for obj in (shift.facility, shift.task, shift.workplace)
            ]

        shift_url = 'https://{domain}{shift_url}#{shift_id}'.format(
            domain=Site.objects.get_current().domain,
            shift_url=shift.get_absolute_url(),
            shift_id=shift.id
        )

        shift_contact = shift.get_shift_contact()
        reply_to = []
        if shift_contact:
            reply_to.append(shift_contact.email)

        context = {
            'username': username.strip(),
            'facility': shift.facility.name.strip(),
            'facility_address': shift.facility.address_line.strip(),
            'organization': shift.facility.organization.name.strip(),
            'task': shift.task.name.strip(),
            'workplace': shift.workplace.name.strip(),
            'shift_date': date_filter(shift.starting_time),
            'shift_starting_time': date_filter(shift.starting_time, 'H:i'),
            'shift_ending_time': date_filter(shift.ending_time, 'H:i'),
            'shift_url': shift_url,
            'general_facility_briefing': facility_briefing,
            'task_briefing': task_briefing,
            'workplace_briefing': workplace_briefing,
            'shift_contact': shift_contact or _(
                u'Your volunteer-planner.org team')
        }
        message = html_parser.unescape(
            render_to_string('emails/shift_briefing.txt', context=context))

        from_email = "Volunteer-Planner <support@volunteer-planner.org>"

        # addresses = [shift_helper.user_account.user.email]
        to = [
            '{username} <{to_email}>'.format(
                username=user.get_full_name() or username,
                to_email=user.email
            )
        ]
        mail = EmailMessage(subject=subject,
                            body=message,
                            to=to,
                            from_email=from_email,
                            reply_to=reply_to)
        mail.send()


class PlannerView(LoginRequiredMixin, FormView):
    """
    View that gets shown to volunteers when they browse a specific day.
    It'll show all the available shifts, and they can add and remove
    themselves from shifts.
    """
    template_name = "helpdesk_single.html"
    form_class = RegisterForShiftForm

    def get_context_data(self, **kwargs):
        context = super(PlannerView, self).get_context_data(**kwargs)

        facility = get_object_or_404(Facility, pk=self.kwargs['pk'])

        try:
            schedule_date = date(int(self.kwargs['year']),
                                 int(self.kwargs['month']),
                                 int(self.kwargs['day']))
        except:
            raise Http404(_(u"Invalid date {}".format(self.kwargs)))

        shifts = Shift.objects.filter(facility=facility)
        shifts = shifts.on_shiftdate(schedule_date)
        shifts = shifts.annotate(volunteer_count=Count('helpers'))
        shifts = shifts.order_by('task', 'workplace', 'ending_time')
        shifts = shifts.select_related('task', 'workplace', 'facility')
        shifts = shifts.prefetch_related('helpers', 'helpers__user')

        context['shifts'] = shifts
        context['facility'] = facility
        context['schedule_date'] = schedule_date
        return context

    def form_invalid(self, form):
        messages.warning(self.request, _(u'The submitted data was invalid.'))
        return super(PlannerView, self).form_invalid(form)

    def form_valid(self, form):
        try:
            user_account = self.request.user.account
        except UserAccount.DoesNotExist:
            messages.warning(self.request, _(u'User account does not exist.'))
            return super(PlannerView, self).form_valid(form)

        shift_to_join = form.cleaned_data.get("join_shift")
        shift_to_leave = form.cleaned_data.get("leave_shift")

        if shift_to_join:

            conflicts = ShiftHelper.objects.conflicting(shift_to_join,
                                                        user_account=user_account)
            conflicted_shifts = [shift_helper.shift for shift_helper in
                                 conflicts]

            if conflicted_shifts:
                error_message = _(
                    u'We can\'t add you to this shift because you\'ve already agreed to other shifts at the same time:')
                message_list = u'<ul>{}</ul>'.format('\n'.join(
                    [u'<li>{}</li>'.format(conflict) for conflict in
                     conflicted_shifts]))
                messages.warning(self.request,
                                 mark_safe(u'{}<br/>{}'.format(error_message,
                                                               message_list)))
            else:
                shift_helper, created = ShiftHelper.objects.get_or_create(
                    user_account=user_account, shift=shift_to_join)
                if created:
                    messages.success(self.request, _(
                        u'You were successfully added to this shift.'))
                    send_briefing_mail(shift_helper)
                else:
                    messages.warning(self.request, _(
                        u'You already signed up for this shift at {date_time}.').format(
                        date_time=shift_helper.joined_shift_at))
        elif shift_to_leave:
            try:
                ShiftHelper.objects.get(user_account=user_account,
                                        shift=shift_to_leave).delete()
            except ShiftHelper.DoesNotExist:
                # just catch the exception,
                # user seems not to have signed up for this shift
                pass
            messages.success(self.request, _(
                u'You successfully left this shift.'))

        user_account.save()
        return super(PlannerView, self).form_valid(form)

    def get_success_url(self):
        """
        Redirect to the same page.
        """
        return reverse('planner_by_facility', kwargs=self.kwargs)
