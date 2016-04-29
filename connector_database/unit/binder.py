# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from __future__ import absolute_import
from openerp import fields
from openerp.osv import orm
from openerp.addons.connector.connector import Binder
from openerp.addons.connector_database.backend import database_backend


@database_backend
class DatabaseBinder(Binder):
    """ Manage bindings between Models identifier and Database identifier"""
    _model_name = []

    def to_openerp(self, mysql_code, unwrap=False, browse=False):
        """Returns the Odoo id for an external ID""

        :param database_code: Database row unique idenifier
        :param unwrap: if True, returns the normal record (the one
                       inherits'ed), else return the binding record
        :param browse: if True, returns a recordset
        :return: a recordset or id of one record, depending on the value of
                 unwrap and browse, or None or an empty recordset if no
                 binding is found
        :rtype: recordset
        """
        bindings = self.env[self.model._name].search(
            [('database_code', '=', database_code),
             ('backend_id', '=', self.backend_record.id)]
        )

        if not bindings:
            return self.model.browse() if browse else None
        assert len(bindings) == 1, "Several records found: %s" % (bindings,)
        if unwrap:
            return bindings.openerp_id if browse else bindings.openerp_id.id
        else:
            return bindings if browse else bindings.id

    def to_backend(self, binding_id):
        """Return the external code for a given binding model id

        :param binding_id: id of a binding model
        :type binding_id: int

        :return: external code of `binding_id`
        """
        database_record = self.env[self.model._name].browse(binding_id)
        assert database_record, 'No corresponding binding found'
        return database_record['database_code']

    @classmethod
    def register_external_binding(cls, binding_class):
        """ Register a binding model that inherits from external.binding
        :param binding_class: class to register
        """
        if not issubclass(binding_class, orm.Model):
            raise TypeError('You try to bind a non orm.Model subclass')

        #  We have no pooler access at class level
        def get_class(name):
            classes = orm.Model.__subclasses__()
            classes.extend(orm.AbstractModel.__subclasses__())
            for x in classes:
                if x._name == name:
                    return x
            return

        def parent_model(container, look_class):
            """ Return parent model list in orm.Model way"""
            inherit = getattr(look_class, '_inherit', None)
            if inherit:
                container.append(inherit)
                return parent_model(container, get_class(inherit))
            else:
                return container

        parents = parent_model([], binding_class)
        if "external.binding" not in parents:
            raise TypeError('You try to bin a model that does'
                            ' not inherit from external.binding')

        class_name = binding_class._name
        if class_name not in cls._model_name:
            cls._model_name.append(class_name)

    def bind(self, external_id, binding_id):
        """ Create the link between an external id and an Odoo row and
        by updating the last synchronization date and the external code.

        :param external_id: Database unique identifier
        :param binding_id: Binding record id
        :type binding_id: int
        """
        # avoid to trigger the export when we modify the `database code`
        now_fmt = fields.Datetime.now()
        with self.session.change_context(connector_no_export=True):
            binding_id.write({'database_code': external_id, 'sync_date': now_fmt})

    def create_binding_from_record(self, external_id, internal_id):
        """Create a binding record for a exsiting Odoo record

        :param external_id: Database unique identifier
        :param internal_id: Odoo record id
        :type internal_id: int

        """
        now_fmt = fields.Datetime.now()
        return self.environment.model.create(
            {'database_code': external_id,
             'sync_date': now_fmt,
             'openerp_id': internal_id,
             'backend_id': self.backend_record.id}
        )


def database_bound(cls):
    """ Register a binding model that inherits from external.binding
    :param cls: class to register
    """
    DatabaseBinder.register_external_binding(cls)
    return cls
