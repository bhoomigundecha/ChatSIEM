from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=[{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
    headers={
        'Accept': 'application/vnd.elasticsearch+json; compatible-with=8',
        'Content-Type': 'application/vnd.elasticsearch+json; compatible-with=8'
    }
)

try:
    info = es.info()
    print(f"✅ Connected! Cluster: {info['cluster_name']}")
    print(f"   Version: {info['version']['number']}")
except Exception as e:
    print(f"❌ Connection failed: {e}")