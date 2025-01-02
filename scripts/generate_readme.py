from jinja2 import Environment, FileSystemLoader
from loguru import logger
from check_spotify import check_spotify

import pathlib

current_dir = pathlib.Path(__file__).parent.resolve()


def generate_readme() -> None:
    latest_albums, top_albums = check_spotify()
    template = Environment(loader=FileSystemLoader(current_dir)).get_template(
        "templates/README.md.j2"
    )
    rendered = template.render(
        latest_albums=latest_albums,
        top_albums=top_albums,
    )
    logger.info(rendered)
    with open(current_dir.parent / "README.md", "w") as f:
        f.write(rendered)


if __name__ == "__main__":
    generate_readme()
