Current Backend Setup 

-- FastAPI app (main.py)
--- Handles end points like /api/query, /api/session/..., /api/indcies, /api/stats 

-- Dockerised ELK stack 
--- elasticsearch + kibana running locally on 9200 + 5601 

-- NLP Parser (nlp_parser.py)
--- Parses user text -> builds a structured ParsedQuery -> Converts to Elasticsearch DSL query 

-- Elasticsearch Service(elasticsearch_service.py)
--- Executes DSL queries, handles aggregations, counts, and multi-index search.

-- Context Manager 
--- Keeps conversation state, previous query, last entities, filters 

