# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re

class SequenceMixin(models.AbstractModel):
    _name = 'sequence.mixin'
    _description = "Automatic sequence"

    def _get_previous_sequence_domain(self, relaxed=False):
        self.ensure_one()
        return [], {}

    def _get_starting_sequence(self):
        self.ensure_one()
        return "00000000"

    def _get_previous_sequence(self, field_name, relaxed=False):
        self.ensure_one()
        where_string, param = self._get_previous_sequence_domain(relaxed)
        if self.id or self.id.origin:
            where_string += " AND id != %(id)s "
            param['id'] = self.id or self.id.origin
        query = "SELECT {field} FROM {table} {where_string} ORDER BY {field} DESC LIMIT 1 FOR UPDATE".format(table=self._table, where_string=where_string, field=field_name)
        self.flush([field_name])
        self.env.cr.execute(query, param)
        return (self.env.cr.fetchone() or [None])[0]

    def _set_next_sequence(self, field_name):
        self.ensure_one()
        last_sequence = self._get_previous_sequence(field_name) or self._get_starting_sequence()

        sequence = re.match(r'(?P<prefix>.*?)(?P<seq>\d*)$', last_sequence)
        value = ("{prefix}{seq:0%sd}" % len(sequence.group('seq'))).format(
            prefix=sequence.group('prefix'),
            seq=int(sequence.group('seq') or 0) + 1,
        )
        self[field_name] = value
        self.flush([field_name])
