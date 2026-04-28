# Samples — 検証用モック Excel

架空の SI 案件「ABC 社 受注管理システム」を題材にした、AI レビュー検証用のモックデータです。

## ファイル一覧

| ファイル | 種別 | サイズ | 概要 |
|---|---|---|---|
| `sample_UI_機能概要書.xlsx` | UI 機能概要書 | ~17KB | 顧客向け画面定義書。曖昧表現・必須項目漏れを意図的に混入 |
| `sample_SS_構造設計書.xlsx` | SS 構造設計書 | ~12KB | PG/PT 向け処理設計書。条件分岐漏れ・PT 観点漏れを意図的に混入 |
| `sample_観点_UI.xlsx` | 観点ファイル (UI) | ~6KB | PM が定義する UI レビュー観点 |
| `sample_観点_SS.xlsx` | 観点ファイル (SS) | ~6KB | PM が定義する SS レビュー観点 |
| `sample_観点_整合性.xlsx` | 観点ファイル (横断) | ~6KB | UI×SS 整合性チェック観点 |
| `generate_mock_excels.py` | 生成スクリプト | - | 上記 5 ファイルを再生成する Python スクリプト |

## 仕込まれた欠陥 (合計 9 件)

詳細は [docs/demo.md](../docs/demo.md) 参照。AI レビューでこれらが検出できるかを確認するためのテストケースです。

## 再生成方法

```bash
cd samples
python -m pip install openpyxl
python generate_mock_excels.py
```

## 注意

- すべてのデータは**完全な架空**です。実在の企業・人物・案件とは一切関係ありません。
- 商標・固有名詞は意図的に避けています。
