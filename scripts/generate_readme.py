import pathlib

from check_hardcover import check_hardcover
from check_spotify import check_spotify
from jinja2 import Environment, FileSystemLoader
from loguru import logger

current_dir = pathlib.Path(__file__).parent.resolve()


def generate_readme() -> None:
    latest_albums, top_albums = check_spotify()
    last_read, currently_reading, goal = check_hardcover()
    template = Environment(loader=FileSystemLoader(current_dir)).get_template(
        "templates/README.md.j2"
    )
    rendered = template.render(
        latest_albums=latest_albums,
        top_albums=top_albums,
        last_read=last_read,
        currently_reading=currently_reading,
        goal=goal,
    )
    logger.info(rendered)
    with open(current_dir.parent / "README.md", "w") as f:
        f.write(rendered)


if __name__ == "__main__":
    generate_readme()
