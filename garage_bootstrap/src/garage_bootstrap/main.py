import typer
from garage_bootstrap.garage import apply_configuration
from garage_bootstrap.models import GarageConfiguration

app = typer.Typer()


@app.command()
def apply(configuration_file_path: str, output_directory: str):
    print(f"Applying configuration from {configuration_file_path}")
    with open(configuration_file_path, 'r') as f:
        configuration = GarageConfiguration.model_validate_json(f.read())
    apply_configuration(configuration, output_directory)


if __name__ == "__main__":
    app()
