# ！ /usr/bin/env  python
# _*_ encoding:utf8 _*_
# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ConnectorRelevance(models.Model):
    _name = "connector.relevance"
    _description = u"模型对应关系"
    _order = 'id'

    name = fields.Char(u'模型说明', index=True, required=True, readonly=True, related="relevance_model_id.model",
                       store=True)
    relevance_model_id = fields.Many2one('ir.model', u'模型名称')
    connector_conf_ids = fields.Many2many('connector.conf', string=u'接口地址', help=u'对应url地址')
    relevance_field_ids = fields.One2many('connector.relevance.field', 'relevance_model_id', string=u'模型对应字段',
                                          required=True)
    form_id = fields.Char(u'对端模型名称')

    @api.model
    def create(self, values):
        if values.get('relevance_model_id'):
            if self.env['connector.relevance'].search(
                    [('relevance_model_id', '=', values.get('relevance_model_id')),
                     ('connector_conf_ids', 'in', values.get('connector_conf_ids'))]):
                raise UserError(_("Template category relevance_model_id already exists!"))
            models_name = self.env['ir.model'].search([('id', '=', values.get('relevance_model_id'))]).name
            values['name'] = models_name
        return super(ConnectorRelevance, self).create(values)
