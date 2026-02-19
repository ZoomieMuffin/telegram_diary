# Claude Code 利用について

このプロジェクトは [Claude Code](https://claude.ai/claude-code) を使って開発しています。

## 利用モデル

| 用途 | モデル |
|------|--------|
| 通常の実装・テスト・リファクタ | Claude Sonnet 4.6 |
| 複雑な設計判断・デバッグ | Claude Opus 4.6 |

## Claude を使っている範囲

- プロジェクト設計・仕様策定
- 実装（TDD: テスト作成 → 実装）
- CI/CD ワークフロー構成
- コードレビュー補助

## コミット

Claude が作成したコミットには以下のトレーラーが付きます。

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

## プロジェクト管理

- タスク管理: [Linear](https://linear.app) (PRV-13〜)
- 仕様: [spec.md](doc/spec.md)
