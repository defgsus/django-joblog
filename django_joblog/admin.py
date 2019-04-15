# encoding=utf-8
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import mark_safe, escape
from django.utils.translation import ugettext_lazy as _

from .models import JobLogModel, JobLogStates


class JobLogModelAdmin(admin.ModelAdmin):
    exclude = tuple()
    list_display = (
        "id_decorator", "name", "count",
        "date_started_decorator", "date_ended_decorator", "duration",
        "state_decorator", "log_decorator", "error_log_decorator"
    )
    search_fields = ("name", "log_text", "error_text")
    list_filter = ("name",)

    def id_decorator(self, model):
        return "#%s" % model.id
    id_decorator.short_description = _("ID")

    def date_started_decorator(self, model):
        return model.date_started.strftime("%Y/%m/%d %H:%M:%S")
    date_started_decorator.short_description = _("started")

    def date_ended_decorator(self, model):
        if model.date_ended is None:
            return "-"
        return model.date_ended.strftime("%Y/%m/%d %H:%M:%S")
    date_ended_decorator.short_description = _("ended")

    def state_decorator(self, model):
        state = getattr(JobLogStates, model.state, None)
        if state:
            state = state.value
        else:
            state = model.state
        return mark_safe('<span style="white-space: nowrap">%s</span>' % state)
    state_decorator.short_description = _("state")

    def log_decorator(self, model):
        return _linebreaks(model.log_text, False)
    log_decorator.short_description = _("log")

    def error_log_decorator(self, model):
        return _linebreaks(model.error_text)
    error_log_decorator.short_description = _("error log")


admin.site.register(JobLogModel, JobLogModelAdmin)


def _linebreaks(text, wrap_lines=True):
    if not text:
        return "-"
    lines = []
    for line in text.split("\n"):
        # make html-compatible
        line = escape(line)
        # keep leading whitespace
        for i, c in enumerate(line):
            if not c.isspace() and i:
                line = line[:i].replace(" ", "&nbsp;").replace("\t", "&nbsp;&nbsp;") + line[i:]
                break
        if not wrap_lines:
            line = '<span style="white-space: nowrap">%s</span>' % line
        lines.append(line)
    return mark_safe("<br>".join(lines))
