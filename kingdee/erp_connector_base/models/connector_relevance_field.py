# ！ /usr/bin/env  python
# _*_ encoding:utf8 _*_
# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ConnectorRelevanceFiled(models.Model):
    _name = "connector.relevance.field"
    _description = "关系对应字段表"
    _order = 'id'

    relevance_model_id = fields.Many2one('connector.relevance', string='模型对应关系', required=True, index=True,
                                         ondelete='cascade', help="The model this field belongs to")

    fields_name = fields.Char(u'字段名称')
    fields_relevance_name = fields.Char(u'关联字段名称')
    fields_state = fields.Boolean(u'启用')

    def sql_splice_fields(self, relevance_model_id):
        if relevance_model_id:
            fields_data = self.search([('relevance_model_id', '=', relevance_model_id)])
            sql_splice = ",".join([vals.fields_relevance_name for vals in fields_data if vals.fields_state])
            return sql_splice
        else:
            raise UserError(_('You can only debit posted moves.'))