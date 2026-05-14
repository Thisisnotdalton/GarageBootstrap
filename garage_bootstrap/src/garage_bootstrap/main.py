import garage_admin_sdk
import typer
from garage_bootstrap.settings import get_settings

app = typer.Typer()
settings = get_settings()


@app.command()
def generate_keys(configuration_file_path: str):
    print(f"Generating API keys for {configuration_file_path}")


if __name__ == "__main__":
    app()
