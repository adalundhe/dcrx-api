import click
import uvicorn
from dcrx_api.app import app


@click.group(help='Commands to manage the DCRX server.')
def server():
    pass


@server.command(help='Run the DCRX server.')
@click.option(
    '--host',
    default='0.0.0.0',
    help='Host address to run the DCRX server on.'
)
@click.option(
    '--port',
    default=8000,
    help='Port to run the DCRX server on.'
)
@click.option(
    '--reload',
    default=False,
    is_flag=True,
    help='Enable hot reload.'
)
def run(
    host: str,
    port: int,
    reload: bool
):
    if reload:
        uvicorn.run(
            "dcrx_api.app:app",
            host=host,
            port=port,
            reload=True
        )

    else:
        uvicorn.run(
            app, 
            host=host,
            port=port
        )