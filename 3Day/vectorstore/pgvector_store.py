import psycopg2
from pgvector.psycopg2 import register_vector


class PGVectorStore:

    def __init__(

            self,

            host,

            database,

            user,

            password,

            port=5432

    ):

        self.conn = psycopg2.connect(

            host=host,

            database=database,

            user=user,

            password=password,

            port=port

        )

        register_vector(self.conn)