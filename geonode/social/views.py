# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import logging

from actstream.models import Action
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied

from geonode.utils import resolve_object
from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


class RecentActivity(ListView):
    """
    Returns recent public activity.
    """
    model = Action
    template_name = 'social/activity_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)

        def _filter_actions(action, request):
            if action == 'all':
                _actions = Action.objects.filter(public=True)[:1000]
            else:
                _actions = Action.objects.filter(
                    public=True, action_object_content_type__model=action)[:1000]
            _filtered_actions = []
            for _action in _actions:
                try:
                    resolve_object(
                        request,
                        ResourceBase,
                        {
                            'id': _action.action_object_object_id
                        },
                        'base.view_resourcebase')
                    _filtered_actions.append(_action.id)
                except ResourceBase.DoesNotExist:
                    _filtered_actions.append(_action.id)
                except (PermissionDenied, Exception) as e:
                    logging.debug(e)
                    pass
            return _filtered_actions

        context['action_list'] = Action.objects.filter(
            id__in=_filter_actions('all', self.request))[:15]
        context['action_list_layers'] = Action.objects.filter(
            id__in=_filter_actions('layer', self.request))[:15]
        context['action_list_maps'] = Action.objects.filter(
            id__in=_filter_actions('map', self.request))[:15]
        context['action_list_documents'] = Action.objects.filter(
            id__in=_filter_actions('document', self.request))[:15]
        context['action_list_comments'] = Action.objects.filter(
            id__in=_filter_actions('comment', self.request))[:15]
        return context


class UserActivity(ListView):
    """
    Returns recent user activity.
    """
    context_object_name = 'action_list'
    template_name = 'actstream/actor.html'

    def get_queryset(self):
        # There's no generic foreign key for 'actor', so can't filter directly
        # Hence the code below is essentially applying the filter afterwards
        return [x for x in Action.objects.filter(public=True)[:15]
                if x and x.actor and x.actor.username == self.kwargs['actor']]

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)
        context['actor'] = self.kwargs['actor']
        return context
