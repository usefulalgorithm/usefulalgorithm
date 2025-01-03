from datetime import datetime
import os
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.httpx import HTTPXAsyncTransport
from loguru import logger
from pydantic import BaseModel, TypeAdapter


class Author(BaseModel):
    name: str


class Contribution(BaseModel):
    author: Author


class Book(BaseModel):
    slug: str
    title: str
    contributions: List[Contribution]


class UserBook(BaseModel):
    rating: Optional[float]
    last_read_date: Optional[datetime]
    book: Book

    @property
    def link(self) -> str:
        return f"https://hardcover.app/books/{self.book.slug}"

    @property
    def authors(self) -> List[str]:
        if len(self.book.contributions) < 3:
            return [c.author.name for c in self.book.contributions]
        return [c.author.name for c in self.book.contributions[:2]] + ["and friends"]

    @property
    def verdict(self) -> str:
        if self.rating is None:
            return "Dunno how I feel about this one."
        if self.rating < 1:
            return "It's trash."
        if self.rating < 2:
            return "It's kinda bad."
        if self.rating < 3:
            return "It's just meh."
        if self.rating < 4:
            return "It's OK I guess."
        if self.rating < 5:
            return "It's a good book."
        return "AHHHH everyone should read this book"
        

class Goal(BaseModel):
    goal: int
    progress: int
    end_date: datetime


get_books_query = gql(
    """
query getBooks($status: Int!, $order_by: [user_books_order_by!]!, $limit: Int) {
  me {
    user_books(
      where: {status_id: {_eq: $status}}
      order_by: $order_by
      limit: $limit
    ) {
      rating
      last_read_date
      book {
        slug
        title
        contributions {
          author {
            name
          }
        }
      }
    }
  }
}
    """
)

get_goals_query = gql(
    """
query getGoal {
  me {
    goals(
      where: {archived: {_eq: false}}
      order_by: {end_date: desc_nulls_last}
      limit: 1
    ) {
      goal
      progress
      end_date
    }
  }
}
    """
)

def _get_books(
    client: Client, status: int, order_by: str, limit: Optional[int]
) -> List[UserBook]:
    resp = client.execute(
        get_books_query,
        {
            "status": status,
            "order_by": {order_by: "desc_nulls_last"},
            "limit": limit,
        },
    )
    return TypeAdapter(List[UserBook]).validate_python(resp["me"][0]["user_books"])


def check_hardcover() -> Tuple[UserBook, List[UserBook], Goal]:
    """
    Returns the last read book, the books I'm currently reading, and the current goal.
    """
    # Check env variables, load from env file if any of these do not exist
    variable_keys = [
        "HARDCOVER_AUTHORIZATION",
    ]
    if any(k not in os.environ for k in variable_keys):
        load_dotenv()

    transport = HTTPXAsyncTransport(
        url="https://api.hardcover.app/v1/graphql",
        headers={
            "authorization": os.environ["HARDCOVER_AUTHORIZATION"],
        },
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    last_read = _get_books(client, 3, "last_read_date", 1)[0]
    logger.debug(last_read)

    currently_reading = _get_books(client, 2, "updated_at", None)
    logger.debug(currently_reading)

    goal = Goal.model_validate(client.execute(get_goals_query)["me"][0]["goals"][0])
    logger.debug(goal)

    return last_read, currently_reading, goal
