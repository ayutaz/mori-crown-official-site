# MORI CROWN! サイト技術調査（GitHub Pages前提）

最終更新: 2026-02-14

## 1. 目的

- `docs/site-spec.md` の情報設計を実装できる技術を決める
- デプロイ先は GitHub Pages 固定
- 今後の更新（ニュース追加、タレント追加）を運用しやすくする

## 2. GitHub Pages の前提（一次情報ベース）

- GitHub Pages は `HTML/CSS/JavaScript` を公開する静的ホスティング
- プロジェクトサイトの公開URLは基本 `https://<owner>.github.io/<repositoryname>`
- GitHub Actions を使ったカスタムワークフローでのデプロイが可能
- 利用上限として、公開サイト 1GB、デプロイ 10分タイムアウト、帯域 100GB/月（ソフト制限）

補足（設計判断）:

- GitHub Pages が静的ホスティングであるため、`/contact` の送信処理は外部サービス連携（例: フォームSaaS、Google Forms、スプレッドシート連携API）またはメール送信導線で実装する

## 3. 候補技術の比較

| 候補 | GitHub Pages適合 | 更新運用（ニュース/タレント追加） | 初期実装速度 | 長期保守 | 総評 |
| --- | --- | --- | --- | --- | --- |
| 素のHTML/CSS/JS（現行維持） | 高い | 低い（ページ複製が増える） | 高い | 低い | 小規模LP向き。今回のページ数では運用負債が出やすい |
| Vite + UIフレームワーク | 高い（`base`設定 + Actions） | 中（自前でデータ設計が必要） | 中 | 中 | UI実装は強いが、コンテンツ運用レイヤーを別途作る必要あり |
| **Astro + Content Collections** | **高い（公式Actionあり）** | **高い（Markdown/JSON + スキーマ管理）** | 中 | **高い** | **今回要件に最適** |

## 4. 採用提案

採用候補: **Astro（静的出力） + Content Collections**

採用理由:

- ファイルベースルーティングで `docs/site-spec.md` のURL構成をそのまま実装しやすい
- Content Collections により、ニュース・タレント情報を型付きで管理できる
- GitHub Pages へのデプロイに公式の `withastro/action` があり、運用が安定しやすい

## 5. 推奨構成（初期）

```text
/
├─ src/
│  ├─ pages/
│  │  ├─ index.astro
│  │  ├─ news/index.astro
│  │  ├─ news/[slug].astro
│  │  ├─ talents/index.astro
│  │  ├─ talents/[slug].astro
│  │  ├─ schedule.astro
│  │  ├─ shop.astro
│  │  ├─ audition.astro
│  │  ├─ fan-works.astro
│  │  ├─ company.astro
│  │  ├─ contact/index.astro
│  │  └─ contact/thanks.astro
│  ├─ components/
│  ├─ layouts/
│  ├─ content/
│  │  ├─ news/*.md
│  │  └─ talents/*.md
│  ├─ data/
│  │  └─ schedule.json
│  └─ content.config.ts
├─ public/
│  └─ assets/
├─ astro.config.mjs
└─ .github/workflows/deploy.yml
```

## 6. GitHub Pages デプロイ設計

- GitHub Settings -> Pages の Source は `GitHub Actions` を選択
- ワークフローは Astro 公式推奨の `withastro/action@v5` + `actions/deploy-pages@v4`
- `permissions` は `pages: write` と `id-token: write` を含める
- `astro.config.mjs` で以下を設定
  - `site`: `https://<username>.github.io`
  - `base`: プロジェクトサイトなら `/<repository-name>`
  - ただし `<username>.github.io` リポジトリ名なら `base` は通常不要

## 7. 実装時の注意点

- 画像資産が増えるため、公開サイズ1GB制限を超えないように最適化（WebP/AVIF化、不要画像削除）
- リポジトリ名が確定するまで `base` 設定を暫定化し、ローカル確認で崩れをチェック
- `contact` は静的サイト制約があるため、送信機能はMVPで「外部フォーム遷移」から開始する

## 8. 次フェーズ（実装開始順）

1. Astroプロジェクト初期化と GitHub Pages workflow 作成
2. 共通レイアウト（ヘッダー/フッター/ナビ）実装
3. `news` と `talents` の content collection 化
4. MVPページを `docs/site-spec.md` の優先順で実装
5. 画像最適化・アクセシビリティ調整・公開

## 参考リンク

- GitHub Docs: What is GitHub Pages?
  - https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- GitHub Docs: GitHub Pages limits
  - https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- GitHub Docs: Using custom workflows with GitHub Pages
  - https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Astro Docs: Deploy your Astro Site to GitHub Pages
  - https://docs.astro.build/en/guides/deploy/github/
- Astro Docs: Content collections
  - https://docs.astro.build/en/guides/content-collections/
- Astro Docs: Configuration `base`
  - https://docs.astro.build/en/reference/configuration-reference/#base
- Vite Docs: Deploying a Static Site
  - https://vite.dev/guide/static-deploy.html
