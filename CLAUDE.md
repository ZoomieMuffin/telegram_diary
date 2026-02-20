# Claude Code 利用について

このプロジェクトは [Claude Code](https://claude.ai/claude-code) を使って開発しています。

## 利用モデル

| 用途 | モデル |
|------|--------|
| 通常の実装・テスト・リファクタ | Claude Opus 4.6 |
| 複雑な設計判断・デバッグ | Claude Opus 4.6 |

## Claude を使っている範囲

- プロジェクト設計・仕様策定
- 実装（TDD: テスト作成 → 実装）
- CI/CD ワークフロー構成
- コードレビュー補助

## コミット

Claude が作成したコミットには以下のトレーラーが付きます。

```
Co-Authored-By: Claude <81847+claude@users.noreply.github.com>
```

## GitHub Actions での Claude 自動修正

PR コメントに `@claude` とメンションすると Claude が起動してレビュー内容を元に修正コミットを push します。

**セキュリティ:** リポジトリオーナー（ZoomieMuffin）のコメントのみ有効。外部ユーザーの `@claude` メンションは無視されます。

## プロジェクト管理

- タスク管理: [Linear](https://linear.app) (PRV-13〜)
- 仕様: [spec.md](doc/spec.md)

## イシュー実装ワークフロー

ユーザーが「PRV-XX を実装して」と指示したら、Claude は以下の手順で進める。

### 1. イシュー確認
Linear から対象イシュー（PRV-XX）の内容・説明・マイルストーンを取得して把握する。

### 2. ブランチ作成
Linear が提示するブランチ名規約に従う。

```
feature/PRV-XX-短い説明   # 新機能
fix/PRV-XX-短い説明       # バグ修正
```

### 3. 実装
- TDD 対象コンポーネントはテストを先に書く（Red → Green → Refactor）
- コミットメッセージに Linear イシュー番号を含める

```
feat: Add state_store (PRV-23)

Co-Authored-By: Claude <81847+claude@users.noreply.github.com>
```

### 4. PR 作成
PR タイトル・本文に Linear イシュー番号を記載し、Linear と自動連動させる。

```
タイトル: feat: Add state_store (PRV-23)
本文: Closes PRV-23
```

GitHub PR の URL を Linear イシューにも貼り付ける。

### 5. Linear イシューのステータス更新
- 実装開始時: `In Progress`
- PR 作成時: Linear に GitHub PR の URL をコメントまたはリンクとして追加
- マージ後: `Done`
