# ！ /usr/bin/env python
# _*_ encoding:utf8 _*_
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ConnectorProduct(models.Model):
    _name = "connector.product"
    _description = "产品资料列表"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id'

    name = fields.Char('Name', index=True, required=True, translate=True)
    get_code = fields.Char(u'获取端编号')
    post_code = fields.Char(u'推送端编号')
    sequence = fields.Integer('Sequence', default=1, help='Gives the sequence order when displaying a product list')
    description = fields.Text('Description', translate=True)
    description_purchase = fields.Text('Purchase Description', translate=True)
    description_sale = fields.Text('Sales Description', translate=True,
                                   help="A description of the Product that you want to communicate to your customers. "
                                        "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")
    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default='consu', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
    categ_id = fields.Char('Product Category',
                           help="Select category for the current product")

    # price fields
    # price: total template price, context dependent (partner, pricelist, quantity)
    price = fields.Float('Price')
    # list_price: catalog price, user defined
    list_price = fields.Float('Sales Price', default=1.0,
                              help="Price at which the product is sold to customers.")
    # lst_price: catalog price for template, but including extra for variants

    standard_price = fields.Float('Cost', groups="base.group_user",
                                  help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")

    weight = fields.Float('Weight', help='产品重量')
    weight_uom_name = fields.Char(string='Weight unit of measure label')

    sale_ok = fields.Boolean('Can be Sold', default=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True)

    uom_name = fields.Char(string='Unit of Measure Name', readonly=True)
    uom_sell_name = fields.Char('sell Unit of Measure',
                                help="Default unit of measure used for sell orders. It must be in the same category as the default unit of measure.")
    uom_po_name = fields.Char('Purchase Unit of Measure',
                              help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.")
    company_id = fields.Char('Company')

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the product without removing it.")
    color = fields.Integer('Color Index')

    # product_variant_ids = fields.One2many('product.product', 'product_tmpl_id', 'Products', required=True)
    # performance: product_variant_id provides prefetching on the first product variant only

    # related to display product product information if is_product_variant
    barcode = fields.Char('Barcode')
    default_code = fields.Char('Internal Reference')

    # all image fields are base64 encoded and PIL-supported

    # all image_variant fields are technical and should not be displayed to the user
    image_variant_1920 = fields.Image("Variant Image", max_width=1920, max_height=1920)

    # resized fields stored (as attachment) for performance
    image_variant_1024 = fields.Image("Variant Image 1024", related="image_variant_1920", max_width=1024,
                                      max_height=1024, store=True)
    image_variant_512 = fields.Image("Variant Image 512", related="image_variant_1920", max_width=512, max_height=512,
                                     store=True)
    image_variant_256 = fields.Image("Variant Image 256", related="image_variant_1920", max_width=256, max_height=256,
                                     store=True)
    image_variant_128 = fields.Image("Variant Image 128", related="image_variant_1920", max_width=128, max_height=128,
                                     store=True)
    can_image_variant_1024_be_zoomed = fields.Boolean("Can Variant Image 1024 be zoomed",
                                                      compute='_compute_can_image_variant_1024_be_zoomed', store=True)

    # Computed fields that are used to create a fallback to the template if
    # necessary, it's recommended to display those fields to the user.
    image_1920 = fields.Image("Image", compute='_compute_image_1920', inverse='_set_image_1920')
    image_1024 = fields.Image("Image 1024", compute='_compute_image_1024')
    image_512 = fields.Image("Image 512", compute='_compute_image_512')
    image_256 = fields.Image("Image 256", compute='_compute_image_256')
    image_128 = fields.Image("Image 128", compute='_compute_image_128')
    can_image_1024_be_zoomed = fields.Boolean("Can Image 1024 be zoomed", compute='_compute_can_image_1024_be_zoomed',
                                              store=True)

    @api.depends('image_variant_1920', 'image_variant_1024')
    def _compute_can_image_variant_1024_be_zoomed(self):
        for record in self:
            record.can_image_variant_1024_be_zoomed = record.image_variant_1920 and tools.is_image_size_above(
                record.image_variant_1920, record.image_variant_1024)

    def _compute_image_1920(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_1920 = record.image_variant_1920

    def _set_image_1920(self):
        for record in self:
            if (
                    # We are trying to remove an image even though it is already
                    # not set, remove it from the template instead.
                    not record.image_1920 and not record.image_variant_1920 or
                    # We are trying to add an image, but the template image is
                    # not set, write on the template instead.
                    record.image_1920
                    # There is only one variant, always write on the template.

            ):
                record.image_variant_1920 = False
            else:
                record.image_variant_1920 = record.image_1920

    def _compute_image_1024(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_1024 = record.image_variant_1024

    def _compute_image_512(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_512 = record.image_variant_512

    def _compute_image_256(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_256 = record.image_variant_256

    def _compute_image_128(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_128 = record.image_variant_128

    def _compute_can_image_1024_be_zoomed(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            # if record.image_variant_1920 else record.can_image_1024_be_zoomed
            record.can_image_1024_be_zoomed = record.can_image_variant_1024_be_zoomed
