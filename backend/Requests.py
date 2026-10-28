try:
    from .database import init_databases
except ImportError:
    from database import init_databases


if __name__ == "__main__":
    init_databases()
    print("Request database is ready.")