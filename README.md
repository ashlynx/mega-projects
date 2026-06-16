# 全国メガプロジェクト・マップ (mega-projects)

シン電力 内部資料。全国の大型プロジェクト（半導体・交通・エネルギー・観光）を
Leaflet ダークマップ上に可視化し、統合検索・JSON/CSV 配布に対応する静的サイト。

## 構成
```
index.html              地図 (生成物)
search.html             統合検索 (生成物)
data/
  mega_projects.json    案件データ (生成物・一次ソース)
  mega_projects.csv     CSV (生成物)
  japan.geojson         都道府県境界 (生成物)
scripts/
  build.py              マスターデータ + ジェネレータ
  japan.geojson         境界ソース
templates/
  index.template.html   地図テンプレート
  search.template.html  検索テンプレート
refresh.sh              cron 用: build → git push --force
```

## 更新フロー
1. `scripts/build.py` 内の `M`（案件マスター）を編集
2. `./refresh.sh` 実行 → `data/*` と `index.html` / `search.html` を再生成し push
3. GitHub Pages が自動反映

`index.html` / `search.html` は `data/mega_projects.json` を fetch し、
取得失敗時はビルド時に埋め込んだフォールバックを使用（ローカル file:// でも表示可）。

## cron 例
```
0 6 * * * /root/mega-projects/refresh.sh >> /var/log/mega-projects.log 2>&1
```

データ出典: 各事業者・公表資料を基にした概算。投資規模は概算・相対指標。
