import click
from flask.cli import with_appcontext
from sqlalchemy import MetaData

from app import create_app, db
from rosemary.commands.clear_uploads import clear_uploads


@click.command("db:nuke", help="Drops all tables in the database to start fresh.")
@click.option("-y", "--yes", is_flag=True, help="Confirm the operation without prompting.")
@with_appcontext
def db_nuke(yes):
    app = create_app()
    with app.app_context():
        if not yes and not click.confirm(
            "WARNING: This will DROP ALL TABLES and clear uploads. This is destructive. Are you sure?",
            abort=True,
        ):
            return

        try:
            meta = MetaData()
            meta.reflect(bind=db.engine)
            meta.drop_all(bind=db.engine)
            click.echo(click.style("All tables dropped successfully.", fg="yellow"))

            # Clear Elasticsearch index
            try:
                from core.services.SearchService import SearchService

                search_service = SearchService()
                if search_service.enabled:
                    search_service.es.options(ignore_status=[400, 404]).indices.delete(index="datasets")
                    click.echo(click.style("Elasticsearch index cleared.", fg="yellow"))
            except Exception as e:
                click.echo(click.style(f"Error clearing Elasticsearch index: {e}", fg="red"))

        except Exception as e:
            click.echo(click.style(f"Error dropping tables: {e}", fg="red"))
            return

        # Delete the uploads folder
        ctx = click.get_current_context()
        ctx.invoke(clear_uploads)

        click.echo(click.style("Database nuked successfully.", fg="green"))
