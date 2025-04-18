from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jDatabase:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "docker")
        self.driver = None

    def connect(self):
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    def get_session(self):
        if not self.driver:
            self.connect()
        return self.driver.session()


db = Neo4jDatabase()
