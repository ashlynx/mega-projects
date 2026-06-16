#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全国メガプロジェクト・マップ ビルダー
  - マスターデータ(MASTER) から data/mega_projects.json / .csv を生成
  - templates/*.template.html に埋め込み、index.html / search.html を再生成
cron 例:  scripts/build.py を実行 → git push  (refresh.sh 参照)
"""
import json, csv, os, datetime, io, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TPL  = os.path.join(ROOT, "templates")
UPDATED = datetime.date.today().isoformat()

# ---- 分野カテゴリ（配色は可視化マップ凡例に一致） -------------------------
CATS = {
    "transit":  {"ja": "交通・インフラ",     "c": "#3fa3ff"},
    "industry": {"ja": "産業・テクノロジー",  "c": "#c45cf0"},
    "energy":   {"ja": "エネルギー・環境",    "c": "#34d39a"},
    "tourism":  {"ja": "観光・地域活性化",    "c": "#f7a83a"},
}

# ---- 路線（交通系ポリライン） ---------------------------------------------
ROUTES = {
    "linear":      [[35.628, 139.738], [35.66, 138.57], [35.18, 136.90]],
    "hokkaido":    [[41.907, 140.647], [42.32, 140.55], [43.063, 141.347]],
    "hokuriku":    [[36.578, 136.648], [35.79, 136.22], [35.645, 136.066]],
    "nishikyushu": [[33.194, 130.020], [32.75, 129.873]],
    "hvdc":        [[43.06, 141.30], [41.5, 140.0], [39.0, 139.6], [37.9, 138.9]],
}

# ---- 案件マスター ----------------------------------------------------------
# url 直リンク（live 確認済 / 403・503 は WAF だが実在）。確証の無いものは search=True で公式検索に。
M = [
 # ===== 交通・インフラ =====
 dict(cat="transit", name="リニア中央新幹線", status="建設・実施中", bud="約9兆円", budN=9,
   tl="2027年以降（名古屋開業）、2037年（大阪延伸予定）", pr="東海旅客鉄道（JR東海）、国土交通省",
   desc="東京（品川）〜名古屋〜大阪を超電導リニアで結ぶ超高速鉄道。三大都市圏の一体化を図る、極めて社会的インパクトの大きいプロジェクト。",
   tags=["リニア","超高速鉄道","三大都市圏","メガプロジェクト"], at=[35.18,136.90], route="linear",
   url="https://linear-chuo-shinkansen.jr-central.co.jp/"),
 dict(cat="transit", name="北海道新幹線延伸（新函館北斗〜札幌）", status="建設・実施中", bud="約2.3兆円", budN=2.3,
   tl="2030年度末頃（一部延期の可能性あり）", pr="鉄道・運輸機構（JRTT）、JR北海道",
   desc="新函館北斗から札幌を結ぶ新幹線延伸計画。札幌〜東京間の陸路アクセスを劇的に変える一大インフラ事業。",
   tags=["新幹線","北海道","札幌"], at=[43.063,141.347], route="hokkaido",
   url="https://www.jrtt.go.jp/"),
 dict(cat="transit", name="北陸新幹線延伸（金沢〜敦賀〜新大阪）", status="一部運用中", bud="敦賀以西区間で約2.1兆円以上（試算）", budN=2.1,
   tl="敦賀開業：2024年3月、新大阪延伸：構想中（環境影響評価手続き中）", pr="鉄道・運輸機構（JRTT）、国土交通省、JR西日本",
   desc="北陸地方を経由して東京と大阪を結ぶ新幹線路線。敦賀〜新大阪間の未着工区間の着工・開業が待たれる。",
   tags=["新幹線","高速鉄道","北陸","関西"], at=[35.645,136.066], route="hokuriku",
   url="https://www.jrtt.go.jp/"),
 dict(cat="transit", name="西九州新幹線（武雄温泉〜長崎）", status="一部運用中", bud="数千億円規模", budN=0.6,
   tl="2022年開業、全線フル規格化は協議中", pr="鉄道・運輸機構（JRTT）、JR九州",
   desc="武雄温泉〜長崎間が先行開業。新鳥栖までのフル規格化が積み残しの課題として残る。",
   tags=["新幹線","九州","長崎"], at=[32.75,129.873], route="nishikyushu",
   url="https://www.jrkyushu.co.jp/"),
 dict(cat="transit", name="なにわ筋線", status="建設・実施中", bud="約3,300億円", budN=0.33,
   tl="2031年春 開業目標", pr="JR西日本、南海電鉄、大阪市",
   desc="新大阪・梅田と難波・関西空港方面を直結する大阪都心の新線。所要時間短縮と新たな南北軸を形成。",
   tags=["大阪","新線","空港アクセス"], at=[34.690,135.498],
   url="https://www.westjr.co.jp/"),
 dict(cat="transit", name="羽田空港アクセス線", status="建設・実施中", bud="約3,000億円", budN=0.3,
   tl="2031年度 開業目標", pr="JR東日本",
   desc="東京・上野方面から羽田空港へ直結する新ルート。都心〜空港アクセスを大幅に短縮する。",
   tags=["羽田","空港アクセス","東京"], at=[35.549,139.784],
   url="https://www.jreast.co.jp/"),
 dict(cat="transit", name="東京メトロ 有楽町線・南北線 延伸", status="建設・実施中", bud="約2,690億円", budN=0.27,
   tl="2030年代 開業目標", pr="東京地下鉄（東京メトロ）",
   desc="有楽町線（豊洲〜住吉）と南北線（品川方面）の延伸事業。都心の鉄道ネットワークを強化する。",
   tags=["地下鉄","東京","延伸"], at=[35.655,139.795],
   url="https://www.tokyometro.jp/"),

 # ===== 産業・テクノロジー =====
 dict(cat="industry", name="TSMC熊本（JASM 第1・第2工場）", status="建設・実施中", bud="約3.5兆円", budN=3.5,
   tl="第1工場 量産入り、第2工場 建設中", pr="JASM（TSMC・ソニー・デンソー・トヨタ）",
   desc="日本最大級の半導体投資。第1工場は量産入りし、第2工場が建設中。関連サプライヤーが九州一円に集積する。",
   tags=["半導体","TSMC","九州","ファウンドリ"], at=[32.886,130.784],
   url="https://www.jasm.co.jp/"),
 dict(cat="industry", name="Rapidus 次世代半導体製造拠点（千歳）", status="建設・実施中", bud="約5兆円", budN=5,
   tl="2025年 試作ライン稼働、2027年 量産開始予定", pr="Rapidus 株式会社",
   desc="北海道千歳市における2nm以下の最先端ロジック半導体の量産拠点整備。日本の半導体産業復活とサプライチェーン再構築の中核。",
   tags=["半導体","2nm","北海道","国策"], at=[42.793,141.690],
   url="https://www.rapidus.inc/"),
 dict(cat="industry", name="Micron 広島（先端DRAM）", status="投資拡大中", bud="数千億円規模", budN=0.8,
   tl="EUV導入、次世代メモリの量産", pr="マイクロンメモリジャパン",
   desc="DRAMの最先端プロセス拠点。EUV露光を導入し、次世代メモリの主力供給拠点となる。",
   tags=["半導体","DRAM","広島"], at=[34.370,132.743],
   url="https://jp.micron.com/"),
 dict(cat="industry", name="キオクシア 北上工場（3D NAND）", status="増設進行", bud="兆円規模", budN=1.2,
   tl="段階的に増設", pr="キオクシア、Western Digital",
   desc="3D NANDフラッシュメモリの中核工場。四日市と並ぶ二大拠点として段階的な増設が続く。",
   tags=["半導体","フラッシュメモリ","岩手"], at=[39.286,141.113],
   url="https://www.kioxia.com/ja-jp/top.html"),
 dict(cat="industry", name="ソニー半導体 熊本（イメージセンサ）", status="新棟建設", bud="数千億円", budN=0.6,
   tl="CMOSイメージセンサの増産", pr="ソニーセミコンダクタソリューションズ",
   desc="スマホ向けCMOSイメージセンサの一大供給拠点。TSMC熊本と隣接し、九州の半導体集積を厚くする。",
   tags=["半導体","イメージセンサ","熊本"], at=[32.870,130.770],
   url="https://www.sony-semicon.com/ja/"),
 dict(cat="industry", name="印西データセンター・クラスター", status="拡大継続", bud="兆円規模の集積", budN=2,
   tl="クラウド大手が集積、増床が継続", pr="国内外クラウド事業者",
   desc="国内最大のデータセンター集積地。クラウド大手のリージョンが集中し、AI需要で電力需要が急増している。",
   tags=["データセンター","クラウド","千葉","AI"], at=[35.832,140.146], search=True),
 dict(cat="industry", name="トヨタ Woven City（裾野）", status="第1期 開所", bud="数千億円規模", budN=0.5,
   tl="2024年〜 段階的に稼働", pr="トヨタ自動車、ウーブン・バイ・トヨタ",
   desc="富士山麓に建設された実証実験都市。モビリティ・エネルギー・AIを街全体で検証する“動く実験場”。",
   tags=["実証都市","モビリティ","静岡","スマートシティ"], at=[35.183,138.910],
   url="https://www.woven-city.global/"),
 dict(cat="industry", name="石狩 AI/GPUデータセンター", status="拡張中", bud="数百億円〜", budN=0.3,
   tl="再エネ立地でGPU基盤を増床", pr="さくらインターネット ほか",
   desc="冷涼な気候と再エネを活かしたグリーンDC拠点。生成AI向けGPUクラウド基盤として増床が続く。",
   tags=["データセンター","AI","GPU","北海道"], at=[43.200,141.300],
   url="https://www.sakura.ad.jp/"),
 dict(cat="industry", name="大阪 クラウドDCリージョン", status="拡大中", bud="数千億円規模", budN=0.6,
   tl="クラウド大手がリージョンを拡張", pr="国内外クラウド事業者",
   desc="西日本のクラウド中核。大手各社がリージョンを拡張し、冗長性とレイテンシ改善を図る。",
   tags=["データセンター","クラウド","大阪"], at=[34.700,135.500], search=True),

 # ===== エネルギー・環境 =====
 dict(cat="energy", name="秋田県沖 洋上風力発電プロジェクト", status="一部運用中", bud="数千億円〜1兆円規模（全体投資額）", budN=1,
   tl="順次運転開始（一部商用運転中）", pr="各事業コンソーシアム",
   desc="能代市・三種町・男鹿市沖および秋田市・潟上市沖における、国内最大規模の商業用洋上風力発電事業。グリーン電源の主力化を担う。",
   tags=["洋上風力","再エネ","秋田","脱炭素"], at=[40.00,139.95], search=True),
 dict(cat="energy", name="銚子沖 洋上風力", status="建設・運開", bud="数千億円", budN=0.4,
   tl="首都圏向け大型洋上風力", pr="事業コンソーシアム",
   desc="関東圏に近い大型洋上風力。首都圏向けの再エネ電源として期待される海域。",
   tags=["洋上風力","千葉","再エネ"], at=[35.76,140.92], search=True),
 dict(cat="energy", name="五島沖 浮体式洋上風力", status="商業運転", bud="数千億円", budN=0.3,
   tl="国内初の商用浮体式", pr="戸田建設 ほか",
   desc="国内初の商用浮体式洋上風力。水深の深い日本沿岸での展開モデルケースとなる。",
   tags=["浮体式","洋上風力","長崎"], at=[32.70,128.80],
   url="https://www.toda.co.jp/"),
 dict(cat="energy", name="柏崎刈羽 原子力発電所 再稼働", status="再稼働手続き", bud="巨大既存資産", budN=1.5,
   tl="再稼働の可否を協議", pr="東京電力ホールディングス",
   desc="世界最大級の原子力サイト。再稼働の可否が、国内の電力需給と電力価格に大きく影響する。",
   tags=["原子力","新潟","電力"], at=[37.428,138.602],
   url="https://www.tepco.co.jp/"),
 dict(cat="energy", name="福島水素エネルギー研究フィールド（FH2R）", status="実証・拡大", bud="数百億円〜", budN=0.2,
   tl="再エネ由来水素の製造実証", pr="NEDO、東芝 ほか",
   desc="世界最大級の再エネ由来水素製造実証拠点。脱炭素サプライチェーンの起点となる。",
   tags=["水素","脱炭素","福島"], at=[37.492,141.00],
   url="https://www.nedo.go.jp/"),
 dict(cat="energy", name="九州 系統用蓄電池（BESS）集積", status="開発加速", bud="数百億円〜", budN=0.5,
   tl="需給調整・容量市場収益を狙い増加", pr="各開発事業者",
   desc="出力制御の多い九州で系統用蓄電池が急増。需給調整市場・容量市場での収益を狙う案件が集積している。",
   tags=["蓄電池","BESS","九州","系統"], at=[32.98,130.79], search=True),
 dict(cat="energy", name="北海道〜本州 海底直流送電（日本海ルートHVDC）", status="計画・調査", bud="数千億円〜兆円規模", budN=1.5,
   tl="2030年代の運用開始を想定", pr="OCCTO、電源開発（J-POWER）ほか",
   desc="北海道の再エネ大量導入を本州へ送るための大容量海底直流送電。全国規模の系統増強（マスタープラン）の目玉。",
   tags=["HVDC","系統増強","再エネ","北海道"], at=[39.0,139.6], route="hvdc", search=True),
 dict(cat="energy", name="神戸・川崎 水素サプライチェーン", status="実証〜商用化", bud="数千億円規模", budN=0.4,
   tl="液化水素の輸入・受入を実証", pr="HySTRA、ENEOS ほか",
   desc="海外から液化水素を輸入・受入する世界初級のサプライチェーン実証。発電・産業用の脱炭素燃料を狙う。",
   tags=["水素","液化水素","輸入","脱炭素"], at=[34.68,135.20], search=True),

 # ===== 観光・地域活性化 =====
 dict(cat="tourism", name="大阪・夢洲 統合型リゾート（IR）構想", status="計画決定", bud="初期投資額 約1兆8,000億円", budN=1.8,
   tl="2030年秋頃 開業予定", pr="大阪IR株式会社（MGM・オリックス等）",
   desc="大阪湾の人工島「夢洲」における日本初のカジノを含む統合型リゾート（IR）の整備計画。関西圏への観光客誘致の起爆剤として期待。",
   tags=["IR","カジノ","大阪","夢洲"], at=[34.65,135.39], search=True),
 dict(cat="tourism", name="うめきた（グラングリーン大阪）", status="段階開業", bud="約2,700億円", budN=0.27,
   tl="2024年 先行まちびらき、2027年 全体開業", pr="開発事業者連合",
   desc="大阪駅北・最後の一等地。約4.5haの都市公園を中核に、職・住・遊が融合する新拠点を形成する。",
   tags=["再開発","大阪","みどり"], at=[34.703,135.494], search=True),
 dict(cat="tourism", name="天神ビッグバン", status="進行中", bud="経済効果 数兆円試算", budN=1,
   tl="ビル建替えを一斉に促進", pr="福岡市、民間事業者",
   desc="航空法の規制緩和を機に、天神エリアのビル建替えを一斉に促進。福岡都心の容積と機能を大きく更新する。",
   tags=["再開発","福岡","都心"], at=[33.591,130.399], search=True),
 dict(cat="tourism", name="麻布台ヒルズ", status="開業済み", bud="約5,800億円", budN=0.58,
   tl="2023年 開業", pr="森ビル",
   desc="日本一の超高層（約330m）を中核とする複合再開発。住・職・商・文化を一体化した「緑に包まれた街」。",
   tags=["再開発","東京","超高層"], at=[35.660,139.740],
   url="https://www.azabudai-hills.com/"),
 dict(cat="tourism", name="JUNGLIA OKINAWA（沖縄・名護）", status="開業", bud="約700億円", budN=0.07,
   tl="2025年7月 開業", pr="ジャパンエンターテイメント",
   desc="沖縄本島北部やんばるの森に開業した大型テーマパーク。自然と最新アトラクションを融合し、沖縄観光の新たな核に。",
   tags=["テーマパーク","沖縄","観光"], at=[26.69,128.00],
   url="https://junglia.jp/"),
 dict(cat="tourism", name="北海道ボールパーク Fビレッジ（エスコンフィールド）", status="開業済み", bud="約600億円", budN=0.06,
   tl="2023年 開業", pr="ファイターズ スポーツ&エンターテイメント",
   desc="日本ハムの新球場を核とした複合まちづくり。スタジアムを中心に居住・商業・宿泊が広がる地域活性化モデル。",
   tags=["ボールパーク","北海道","地域活性化"], at=[42.994,141.573], search=True),
 dict(cat="tourism", name="ジブリパーク（愛知・長久手）", status="全エリア開業", bud="数百億円規模", budN=0.05,
   tl="2022年〜2024年 順次開業", pr="愛知県、スタジオジブリ",
   desc="愛・地球博記念公園内に整備されたジブリ世界のテーマパーク。中部圏のインバウンド・観光需要を牽引する。",
   tags=["テーマパーク","愛知","インバウンド"], at=[35.183,137.080],
   url="https://ghibli-park.jp/"),
]

def org_short(pr):
    return pr.split("、")[0].split("（")[0].split("(")[0]

def main():
    os.makedirs(DATA, exist_ok=True)
    projects = []
    for p in M:
        direct = "url" in p and not p.get("search")
        link = p["url"] if direct else ("https://www.google.com/search?q=" +
                urllib.parse.quote(p["name"] + " " + p["pr"] + " 公式"))
        projects.append({
            "cat": p["cat"], "category_ja": CATS[p["cat"]]["ja"],
            "name": p["name"], "status": p["status"],
            "bud": p["bud"], "budget": p["bud"],
            "budN": p["budN"], "budget_tn_yen": p["budN"],
            "tl": p["tl"], "timeline": p["tl"],
            "pr": p["pr"], "proponent": p["pr"], "desc": p["desc"],
            "tags": p["tags"], "at": [p["at"][0], p["at"][1]],
            "lat": p["at"][0], "lng": p["at"][1],
            "route": p.get("route"), "link": link, "link_direct": direct,
            "link_label": org_short(p["pr"]) + ("公式サイト" if direct else "公式情報を検索"),
        })

    payload = {"updated": UPDATED, "count": len(projects),
               "total_tn_yen": round(sum(p["budget_tn_yen"] for p in projects)),
               "categories": CATS, "routes": ROUTES, "projects": projects}

    # ---- data/mega_projects.json ----
    with open(os.path.join(DATA, "mega_projects.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---- data/mega_projects.csv ----
    cols = ["category_ja","name","status","budget","budget_tn_yen","timeline","proponent",
            "tags","lat","lng","link"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for p in projects:
        w.writerow([p["category_ja"],p["name"],p["status"],p["budget"],p["budget_tn_yen"],
                    p["timeline"],p["proponent"],"|".join(p["tags"]),p["lat"],p["lng"],p["link"]])
    with open(os.path.join(DATA, "mega_projects.csv"), "w", encoding="utf-8-sig") as f:
        f.write(buf.getvalue())

    # ---- data/japan.geojson (copy from source) ----
    src_geo = os.path.join(os.path.dirname(__file__), "japan.geojson")
    with open(src_geo, encoding="utf-8") as f:
        geo = f.read().strip()
    with open(os.path.join(DATA, "japan.geojson"), "w", encoding="utf-8") as f:
        f.write(geo)

    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    # ---- render templates ----
    for tpl_name, out_name in [("index.template.html","index.html"),
                               ("search.template.html","search.html")]:
        with open(os.path.join(TPL, tpl_name), encoding="utf-8") as f:
            html = f.read()
        html = (html.replace("__UPDATED__", UPDATED)
                    .replace("__DATA_JSON__", data_json)
                    .replace("__GEO_JSON__", geo))
        with open(os.path.join(ROOT, out_name), "w", encoding="utf-8") as f:
            f.write(html)

    print(f"[build] {len(projects)} projects · total ≈{payload['total_tn_yen']}兆円 · updated {UPDATED}")
    print(f"[build] wrote data/mega_projects.json, .csv, japan.geojson, index.html, search.html")

if __name__ == "__main__":
    main()
