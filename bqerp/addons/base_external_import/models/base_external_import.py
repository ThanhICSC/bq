# -*- coding: utf-8 -*-
# Copyright (C) 2011 - Daniel Reis
# Copyright (C) 2018 - Liu Jianyun
# Copyright (C) 2018 - Henry Zhou
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, models, fields, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_loglvl = _logger.getEffectiveLevel()
SEP = '|'


class Log(models.Model):
    _name = "base.external.import.log"
    _description = 'Log'
    _rec_name = 'import_id'
    _order = 'last_run desc'

    import_id = fields.Many2one('base.external.import.task', string='Import task')
    start_run = fields.Datetime(string='Time started', readonly=True)
    last_run = fields.Datetime(string='Time ended', readonly=True)
    last_record_count = fields.Integer(string='Last record count', readonly=True)
    last_error_count = fields.Integer(string='Last error count', readonly=True)
    last_warn_count = fields.Integer(string='Last warning count', readonly=True)
    last_log = fields.Text(string='Last run log', readonly=True)


class Task(models.Model):
    _name = "base.external.import.task"
    _description = 'Task'
    _order = 'exec_order'

    name = fields.Char(required=True, string='Task name', size=64)
    enabled = fields.Boolean(string='Execution enabled', default=True)
    dbsource_id = fields.Many2one('base.external.dbsource', string='Data source', required=True)
    sql_source = fields.Text(string='SQL', required=True, help='Column names must be valid "import_data" columns.')
    model_target = fields.Many2one('ir.model', string='Target object', required=True)
    exec_order = fields.Integer(string='Execution order', help="Defines the order to perform the import", default=10)
    last_sync = fields.Datetime(string='Last sync time', help="Datetime for the last successful sync. \nLater changes \
                                on the source may not be replicated on the destination")
    start_run = fields.Datetime(string='Time started', readonly=True)
    last_run = fields.Datetime(string='Time ended', readonly=True)
    last_record_count = fields.Integer(string='Last record count', readonly=True)
    last_error_count = fields.Integer(string='Last error count', readonly=True)
    last_warn_count = fields.Integer(string='Last warning count', readonly=True)
    last_log = fields.Text(string='Last run log', readonly=True)

    @staticmethod
    def append_to_log(log, level, obj_id='', msg='', rel_id=''):
        if '_id_' in obj_id:
            obj_id = ('.'.join(obj_id.split('_')[:-2]) + ': ' +
                      obj_id.split('_')[-1])
        if ': .' in msg and not rel_id:
            rel_id = msg[msg.find(': .') + 3:]
            if '_id_' in rel_id:
                rel_id = ('.'.join(rel_id.split('_')[:-2]) +
                          ': ' + rel_id.split('_')[-1])
                msg = msg[:msg.find(': .')]
        log['last_log'].append('%s|%s\t|%s\t|%s' % (level.ljust(5), obj_id, rel_id, msg))

    def _import_data(self, flds, data, target_model, log):
        _logger.debug(data)
        errmsg = str()
        try:
            import_result = self.env[target_model].with_context(import_file=True).load(flds, [data])
            if len(import_result['messages']) != 0:
                res_type = import_result['messages'][0]['type']
                if res_type == 'error':
                    self.append_to_log(log, 'ERROR', data, import_result['messages'][0]['message'])
                    log['last_error_count'] += 1
                elif res_type == 'warning':
                    log['last_warn_count'] += 1
        except Exception as error:
            errmsg = error

        if errmsg:
            self.append_to_log(log, 'ERROR', data, errmsg)
            log['last_error_count'] += 1
            return False

        return True

    def _update_data(self, data_has_importkey, key_col_name, target_model, log):
        _logger.debug(data_has_importkey)

        try:
            for data_row in data_has_importkey:
                target_rec = self.env[target_model].search([(key_col_name, '=', data_row[key_col_name])])
                if target_rec:
                    for rec in target_rec:
                        for col_name in data_row:
                            if col_name != key_col_name:
                                rec[col_name] = data_row[col_name]
        except Exception as error:
            self.append_to_log(log, 'ERROR', data_has_importkey, error)
            log['last_error_count'] += 1
            return False

        return True

    def import_run(self, ids=None):
        external_db_model = self.pool.get('base.external.dbsource')

        if isinstance(ids, dict):
            task_ids = self.ids
        else:
            task_ids = ids

        if task_ids is None:
            tasks = self.search([('enabled', '=', True)])
        else:
            tasks = self.browse(task_ids)

        tasks.sorted(key=lambda k: (k['exec_order'], k['id']))

        import_key = '[import_key]'
        import_key_length = len(import_key)

        # Consider each task:
        for task in tasks:
            # task = self.browse(action_ref['id'])
            if not task.enabled:
                continue

            _logger.setLevel(_loglvl)
            _logger.debug('Importing %s...' % task.name)

            target_model_name = task.model_target.model
            log = {'start_run': datetime.now().replace(microsecond=0),
                   'last_run': None,
                   'last_record_count': 0,
                   'last_error_count': 0,
                   'last_warn_count': 0,
                   'last_log': list()}
            task.write(log)

            if task.last_sync:
                last_sync_time = datetime.strptime(task.last_sync, "%Y-%m-%d %H:%M:%S")
            else:
                last_sync_time = datetime(1900, 1, 1, 0, 0, 0)
            params = {'sync': last_sync_time}
            external_recs = external_db_model.execute(self.env['base.external.dbsource'].browse(task.dbsource_id.id),
                                                      task.sql_source, params, metadata=True)

            col_index = ([i for i, x in enumerate(external_recs['cols'])])
            col_names = ([x for i, x in enumerate(external_recs['cols'])])

            self._cr.execute('SAVEPOINT external_import')
            try:
                # Import each row:
                for row in external_recs['rows']:
                    # Build data row;
                    # import only columns present in the "col_names" list
                    has_importkey = False
                    data_has_importkey = []
                    key_col_name = ''

                    temp_rec = {}
                    data = list()
                    for i in col_index:
                        value = row[i]
                        if isinstance(value, str):
                            value = value.strip()
                        col_name = col_names[i]
                        if import_key in col_name:
                            if has_importkey:
                                raise UserError('Only support one import key column.')
                            else:
                                has_importkey = True

                            col_name = col_name[import_key_length:]
                            key_col_name = col_name
                        else:
                            data.append(value)

                        temp_rec[col_name] = value

                    data_has_importkey.append(temp_rec)

                    log['last_record_count'] += 1
                    if has_importkey:
                        self._update_data(data_has_importkey, key_col_name, task.model_target.model, log)
                    else:
                        self._import_data(col_names, data, task.model_target.model, log)
                    if log['last_record_count'] % 500 == 0:
                        _logger.info('...%s rows processed...' % (log['last_record_count']))
            except Exception:
                self._cr.execute('ROLLBACK TO SAVEPOINT external_import')
                raise
            else:
                self._cr.execute('RELEASE SAVEPOINT external_import')

            # Finished importing all rows
            # If no errors, write new sync date
            if not (log['last_error_count'] or log['last_warn_count']):
                log['last_sync'] = log['start_run']
            level = logging.DEBUG
            if log['last_warn_count']:
                level = logging.WARN
            if log['last_error_count']:
                level = logging.ERROR
            _logger.log(level,
                        'Imported %s , %d rows, %d errors, %d warnings.' %
                        (target_model_name, log['last_record_count'],
                         log['last_error_count'],
                         log['last_warn_count']))
            # Write run log, either if the table import is active or inactive
            if log['last_log']:
                log['last_log'].insert(0, 'LEVEL|== Line ==|== Relationship ==|== Message ==')
            log.update({'last_log': '\n'.join(log['last_log'])})
            log.update({'last_run': datetime.now().replace(microsecond=0)})
            task.write(log)
            import_logs = {
                'import_id': task.id,
                'start_run': log['start_run'],
                'last_run': log['last_run'],
                'last_record_count': log['last_record_count'],
                'last_error_count': log['last_error_count'],
                'last_warn_count': log['last_warn_count'],
                'last_log': log['last_log']
            }
            self.env['base.external.import.log'].create(import_logs)

        # Finished
        _logger.debug('Import job FINISHED.')
        return True

    def import_schedule(self):
        action_server_obj = self.env['ir.actions.server']
        new_action = action_server_obj.create({
            'name': self.name,
            'type': 'ir.actions.server',
            'usage': 'ir_cron',
            'state': 'code',
            'model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1).id,
            'code': 'model.import_run(%s)' % str(self.id)
        })
        cron_obj = self.env['ir.cron']
        new_cron = cron_obj.create({
            'ir_actions_server_id': new_action.id,
            'interval_type': 'days',
            'numbercall': -1,
            'doall': False,
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.cron',
            'res_id': new_cron.id,
            'type': 'ir.actions.act_window',
        }
