# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import re


class ReSequenceWizard(models.TransientModel):
    _name = 'account.resequence.wizard'
    _description = 'Remake the sequence of Journal Entries.'

    first_name = fields.Char()
    last_name = fields.Char(compute='_compute_last_name', help="This will be the name used for the last item renamed")
    ordering = fields.Selection([('keep', 'Keep current order'), ('date', 'Reorder by accounting date')], required=True, default='keep')
    move_ids = fields.Many2many('account.move')

    @api.model
    def default_get(self, fields):
        res = super(ReSequenceWizard, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        if any(not move.posted_before and (move.name == '/' or not move.name) for move in move_ids):
            raise UserError(_('You can only reorder moves that have been posted or that already have a number'))
        res['move_ids'] = [(6, 0, move_ids.ids)]
        res['first_name'] = min(move_ids.mapped('name'))
        return res

    @api.depends('first_name', 'move_ids')
    def _compute_last_name(self):
        for record in self:
            record.last_name = self._get_list_names()[-1]

    def _get_list_names(self):
        sequence = re.match(r'(?P<prefix>.*?)(?P<seq>\d*)$', self.first_name)
        return [("{prefix}{seq:0%sd}" % len(sequence.group('seq'))).format(
            prefix=sequence.group('prefix'),
            seq=int(sequence.group('seq') or 0) + i,
        ) for i in range(len(self.move_ids))]

    def resequence(self):
        ordered_ids = []
        for move in self.move_ids.sorted(lambda m: m.name if self.ordering == 'keep' else m.date):
            ordered_ids.append((move.id, move.state))

        self.move_ids.state = 'draft'
        for id_state, name in zip(ordered_ids, self._get_list_names()):
            move = self.env['account.move'].browse(id_state[0])
            move.name = name
            move.state = id_state[1]
