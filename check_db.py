from app.crud.database import db

def check_nodes():
    with db.get_session() as session:
        # すべてのノードを取得
        result = session.run("MATCH (n) RETURN n LIMIT 25")
        nodes = list(result)

        print(f"\n=== データベース内のノード数: {len(nodes)} ===\n")

        for i, record in enumerate(nodes, 1):
            node = record["n"]
            print(f"{i}. ラベル: {list(node.labels)}")
            print(f"   プロパティ: {dict(node)}")
            print()

        # ラベルの一覧を取得
        label_result = session.run("CALL db.labels()")
        labels = [record[0] for record in label_result]
        print(f"=== 使用されているラベル: {labels} ===\n")

        # 各ラベルのノード数をカウント
        for label in labels:
            count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = count_result.single()["count"]
            print(f"{label}: {count}個のノード")

if __name__ == "__main__":
    check_nodes()