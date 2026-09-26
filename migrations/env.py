"""Print the database URL for goose. Used by the justfile/start.sh to set GOOSE_DBSTRING."""

from app.config import load


def main() -> None:
    config = load("database")
    print(config.database.goose_url)


if __name__ == "__main__":
    main()
