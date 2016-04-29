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
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..unit.mapper import DatabaseRowImportMapper
from ..backend import database_backend
from ..unit.binder import database_bound
from ..unit.import_synchronizer import (DirectBatchDatabaseSynchronizer,
                                        DelayedBatchDatabaseSynchronizer,
                                        DatabaseSynchronizer)
from ..unit.database_adapter import DatabaseAdapter
from openerp.osv import orm, fields


class test_code_a(orm.Model):
    """Dummy model only used for sychronization tests"""

    _name = "database.connector.test.code.a"
    _description = """Dummy model only used for test"""
    _columns = {'code': fields.char('Code', required=True,
                                    select=True),
                'name': fields.char('Name', required=True),
                'active': fields.boolean('Active'),
                'desc': fields.text('Desc.'),
                'test_date': fields.date('Date'),
                'test_datetime': fields.datetime('Date time'),
                }

    _defaults = {'active': True}


@database_bound
class database_code_a(orm.Model):
    """Test model"""
    _inherit = "database.string.server.binding"
    _inherits = {'database.connector.test.code.a': 'openerp_id'}
    _name = "database.data.connector.test.code.a"
    _description = """external table into database.connector.test.code.a"""

    _columns = {'openerp_id': fields.many2one('database.connector.test.code.a',
                                              'Test code',
                                              required=True,
                                              ondelete='restrict')}

    _sql_contraints = [
        ('database_uniq', 'unique(backend_id, database_code)',
         'A test code with same Database data code already exists')
    ]


@database_backend
class TestCodeDatabaseSynchronizer(DatabaseSynchronizer):
    _model_name = "database.data.connector.test.code.a"


@database_backend
class TestCodeDirectBatchDatabaseSynchronizer(DirectBatchDatabaseSynchronizer):
    _model_name = "database.data.connector.test.code.a"


@database_backend
class TestCodeDelayedBatchDatabaseSynchronizer(DelayedBatchDatabaseSynchronizer):
    _model_name = "database.data.connector.test.code.a"


@database_backend
class CustomerDatabaseObjectAdapter(DatabaseAdapter):
    _table_name = "mega_code_table"
    _model_name = "database.data.connector.test.code.a"

    def get_date_columns(self):
        return ("mg_createTime", "mg_modifyTime")

    def get_unique_key_column(self):
        return "mg_code"

    def get_sql_conditions(self, *args):
        return "WHERE status = ?", ['Active']


@database_backend
class CustomerMapper(DatabaseRowImportMapper):
    _model_name = "database.data.connector.test.code.a"
    direct = [('mg_name', 'name'),
              ('mg_code', 'code'),
              ('mg_desc', 'desc')]

    @only_create
    @mapping
    def database_code(self, record):
        return {'database_code': record.mg_code}

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @only_create
    @mapping
    def date_datetime(self, record):
        # database return real date datetime object
        return {'test_date': str(record.x_date),
                'test_datetime': str(record.x_datetime)}
