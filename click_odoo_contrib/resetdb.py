#!/usr/bin/env python
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
import click_odoo

from ._dbutils import (
    db_exists,
    reset_config_parameters,
)


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=True,
)
@click.option(
    "--if-exists",
    is_flag=True,
    help="Execute only if database exists",
)
@click.option(
    "--reset-config/--no-reset-config",
    is_flag=True,
    default=True,
    help="Reset the system configuration",
)
@click.option(
    "--set-password",
    metavar="P",
    help="Set the password P on all users",
)
@click.option(
    "--disable-cron",
    is_flag=True,
    help="Disable all CRON jobs",
)
@click.option(
    "--disable-mail",
    is_flag=True,
    help="Disable all mail servers",
)
@click.argument("dest", required=True)
def main(
    env,
    dest,
    if_exists,
    reset_config,
    set_password,
    disable_cron,
    disable_mail,
):
    """Reset an Odoo database ID and options.

    This script resets system paramters of the given database.
    """
    dbname = dest
    if not db_exists(dbname):
        msg = "Database does not exist: {}".format(dbname)
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    # reset common parameters
    if reset_config:
        reset_config_parameters(dbname)
    # additional changes
    with click_odoo.OdooEnvironment(dbname) as env:
        if reset_config:
            env.cr.execute("""
            DELETE FROM ir_attachment
            WHERE name like '%.assets_%' AND public = true;

            DO $$
            BEGIN
                UPDATE auth_oauth_provider SET enabled = false;
            EXCEPTION WHEN undefined_table THEN
            END;
            $$
            """)
        if disable_cron:
            env.cr.execute("""
            UPDATE ir_cron SET active = false;
            UPDATE ir_cron SET active = true
            WHERE id IN (
                SELECT res_id
                FROM ir_model_data
                WHERE model = 'ir.cron'
                AND (
                    (module = 'base' AND name = 'autovacuum_job')
                )
            );
            """)
        if disable_mail:
            env.cr.execute("""
            DO $$
            BEGIN
                UPDATE ir_mail_server SET active = false;
                UPDATE mail_template SET mail_server_id = NULL;
            EXCEPTION WHEN undefined_table THEN
            END;
            $$
            """)
        if set_password:
            # odoo will encrypt the password later on
            password_value = set_password
            env.cr.execute("""
            UPDATE res_users SET password = '{}';
            """.format(password_value.replace("'", "''")))
    msg = "Database is reset: {}".format(dbname)
    click.echo(click.style(msg))


if __name__ == "__main__":  # pragma: no cover
    main()
