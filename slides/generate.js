// Waterfall Review App 概要スライド v4 (ポートフォリオ完成版に準拠)
// Phase 1〜4 完了 / F-01〜F-09 リリース済 / BE 75 + FE 19 = 94 tests
// Reference: https://note.com/it_navi/n/ne26d4d078386
// Library: PptxGenJS v4.x

const PptxGenJS = require("pptxgenjs");

// ====== デザインシステム ======
const C = {
  bgWhite: "FFFFFF",
  bgLight: "F5F7FA",
  bgPale: "EAF1FA",
  bgNavy: "0B1F3F",
  textBlack: "1A1A1A",
  textWhite: "FFFFFF",
  textMuted: "5A5A5A",
  royalBlue: "1B3A6B",
  blue2: "3D6098",
  blue3: "7A9CC6",
  gridLine: "D0D0D0",
  green: "2E7D32",
  amber: "ED6C02",
  red: "C62828",
  purple: "6A1B9A",
};

const F = {
  headJa: "Yu Mincho",
  bodyJa: "Yu Gothic",
  num: "Calibri",
  mono: "Consolas",
};

// ====== 共通ヘルパ ======
function addActionTitle(s, title) {
  s.addText(title, {
    x: 0.5, y: 0.3, w: 12.4, h: 0.7,
    fontFace: F.headJa, fontSize: 24, bold: true, color: C.royalBlue,
  });
  s.addShape("line", {
    x: 0.5, y: 1.07, w: 12.4, h: 0,
    line: { color: C.royalBlue, width: 1 },
  });
}

function addPageNo(s, n, total) {
  s.addText(`${n} / ${total}`, {
    x: 12.0, y: 7.05, w: 1.0, h: 0.3,
    fontFace: F.num, fontSize: 11, color: C.textMuted, align: "right",
  });
}

function circleIcon(s, x, y, size, fill, glyph, glyphSize, glyphColor = C.textWhite) {
  s.addShape("ellipse", {
    x, y, w: size, h: size,
    fill: { color: fill },
    line: { color: fill, width: 0 },
  });
  s.addText(glyph, {
    x, y, w: size, h: size,
    fontFace: F.bodyJa, fontSize: glyphSize, bold: true,
    color: glyphColor, align: "center", valign: "middle",
  });
}

function badge(s, x, y, w, h, text, fill, color = C.textWhite, fontSize = 12) {
  s.addShape("roundRect", {
    x, y, w, h,
    fill: { color: fill },
    line: { color: fill, width: 0 },
    rectRadius: 0.08,
  });
  s.addText(text, {
    x, y, w, h,
    fontFace: F.bodyJa, fontSize, bold: true,
    color, align: "center", valign: "middle",
  });
}

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Waterfall Review App";
pptx.company = "";
pptx.title = "Waterfall Review App 概要 v4";

const TOTAL = 12;

// =============================================================
// Slide 1: タイトル
// =============================================================
{
  const s = pptx.addSlide();
  s.background = { color: C.bgNavy };
  s.addShape("ellipse", { x: 11.0, y: -1.5, w: 5.0, h: 5.0, fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 } });
  s.addShape("ellipse", { x: -1.5, y: 5.5, w: 4.0, h: 4.0, fill: { color: C.blue2 }, line: { color: C.blue2, width: 0 } });

  s.addText("Waterfall Review App", {
    x: 0.7, y: 2.1, w: 12, h: 1.0,
    fontFace: F.headJa, fontSize: 48, bold: true, color: C.textWhite,
  });
  s.addText("AI レビュー支援ツール — UI 機能概要書 × SS 構造設計書 を AI で完璧化する", {
    x: 0.7, y: 3.2, w: 12, h: 0.6,
    fontFace: F.bodyJa, fontSize: 20, color: C.blue3,
  });
  s.addShape("rect", { x: 0.7, y: 4.3, w: 0.15, h: 1.9, fill: { color: C.amber }, line: { color: C.amber, width: 0 } });
  s.addText("PoC v1.0 (Phase 1〜4 完了)\nF-01〜F-09 全機能リリース\nBE 75 + FE 19 = 94 tests passed\nGitHub 公開 (MIT License)", {
    x: 1.0, y: 4.3, w: 10, h: 1.9,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.textWhite, valign: "top",
  });
  s.addText("ポートフォリオ版  /  2026-04-28", {
    x: 0.7, y: 6.7, w: 12, h: 0.4,
    fontFace: F.bodyJa, fontSize: 13, color: C.blue3,
  });
}

// =============================================================
// Slide 2: これ何 (Why)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "UI 機能概要書 と SS 構造設計書 を AI が完璧化する");

  s.addShape("rect", { x: 0.5, y: 1.4, w: 5.8, h: 5.0, fill: { color: C.bgLight }, line: { color: C.gridLine, width: 1 } });
  s.addText("従来 (人手レビュー)", {
    x: 0.7, y: 1.55, w: 5.4, h: 0.6,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.textMuted,
  });
  ["UI: 顧客クレーム/QA の温床", "SS: 抜けが PG漏れ → バグ直結", "工程間整合性チェック漏れ", "属人化、品質ばらつき"].forEach((t, i) => {
    circleIcon(s, 0.7, 2.4 + i * 0.85, 0.4, C.red, "✕", 16);
    s.addText(t, {
      x: 1.3, y: 2.4 + i * 0.85, w: 4.8, h: 0.4,
      fontFace: F.bodyJa, fontSize: 16, color: C.textBlack, valign: "middle",
    });
  });

  s.addShape("rightArrow", {
    x: 6.32, y: 3.7, w: 0.8, h: 0.7,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 },
  });
  s.addText("AI 化", {
    x: 6.0, y: 3.0, w: 1.5, h: 0.4,
    fontFace: F.headJa, fontSize: 12, bold: true, color: C.royalBlue, align: "center",
  });

  s.addShape("rect", { x: 7.1, y: 1.4, w: 5.8, h: 5.0, fill: { color: C.bgPale }, line: { color: C.royalBlue, width: 1.5 } });
  s.addText("AIレビュー支援ツール", {
    x: 7.3, y: 1.55, w: 5.4, h: 0.6,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.royalBlue,
  });
  ["UI 観点で網羅レビュー (顧客視点)", "SS 観点で網羅レビュー (PG視点)", "UI×SS 整合性を AI が突合", "PDF 出力で印刷・配布可能"].forEach((t, i) => {
    circleIcon(s, 7.3, 2.4 + i * 0.85, 0.4, C.green, "✓", 16);
    s.addText(t, {
      x: 7.9, y: 2.4 + i * 0.85, w: 4.8, h: 0.4,
      fontFace: F.bodyJa, fontSize: 16, bold: true, color: C.textBlack, valign: "middle",
    });
  });

  s.addText("UI と SS の両方とも「完璧」が要求される。AI が抜け・矛盾・曖昧をあぶり出す。", {
    x: 0.5, y: 6.65, w: 12.4, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 2, TOTAL);
}

// =============================================================
// Slide 3: ドキュメントの位置付け (UI vs SS)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "UI = 顧客向け / SS = PG向け。両方とも完璧でなければバグ・クレーム発生");

  // UI ボックス
  s.addShape("roundRect", {
    x: 0.5, y: 1.4, w: 6.0, h: 4.5,
    fill: { color: "FFF8E1" }, line: { color: C.amber, width: 2 }, rectRadius: 0.15,
  });
  badge(s, 0.7, 1.55, 1.5, 0.6, "UI", C.amber, C.textWhite, 18);
  s.addText("機能概要書", {
    x: 2.4, y: 1.55, w: 4.0, h: 0.6,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.amber, valign: "middle",
  });

  s.addText("読者: 顧客 + 開発側", {
    x: 0.7, y: 2.4, w: 5.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, bold: true, color: C.textBlack,
  });
  s.addText("役割: 機能の見た目・動作を顧客と合意", {
    x: 0.7, y: 2.85, w: 5.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 13, color: C.textBlack,
  });

  s.addShape("line", { x: 0.7, y: 3.4, w: 5.6, h: 0, line: { color: C.amber, width: 0.5 } });

  s.addText("失敗時の影響:", {
    x: 0.7, y: 3.55, w: 5.6, h: 0.4,
    fontFace: F.headJa, fontSize: 13, bold: true, color: C.red,
  });
  s.addText("• 顧客クレーム発生\n• 仕様QA(質問)が大量発生\n• 後工程の手戻り (SS再設計)", {
    x: 0.7, y: 4.0, w: 5.6, h: 1.5,
    fontFace: F.bodyJa, fontSize: 13, color: C.textBlack, valign: "top",
  });

  // SS ボックス
  s.addShape("roundRect", {
    x: 6.8, y: 1.4, w: 6.0, h: 4.5,
    fill: { color: "E3F2FD" }, line: { color: C.royalBlue, width: 2 }, rectRadius: 0.15,
  });
  badge(s, 7.0, 1.55, 1.5, 0.6, "SS", C.royalBlue, C.textWhite, 18);
  s.addText("構造設計書", {
    x: 8.7, y: 1.55, w: 4.0, h: 0.6,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.royalBlue, valign: "middle",
  });

  s.addText("読者: 開発側 (PG / PT)", {
    x: 7.0, y: 2.4, w: 5.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, bold: true, color: C.textBlack,
  });
  s.addText("役割: PG 内容を 100% 決定 (擬似コード) + PT 項目の根拠", {
    x: 7.0, y: 2.85, w: 5.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 13, color: C.textBlack,
  });

  s.addShape("line", { x: 7.0, y: 3.4, w: 5.6, h: 0, line: { color: C.royalBlue, width: 0.5 } });

  s.addText("失敗時の影響:", {
    x: 7.0, y: 3.55, w: 5.6, h: 0.4,
    fontFace: F.headJa, fontSize: 13, bold: true, color: C.red,
  });
  s.addText("• 記載漏れ = PG漏れ = PTで検出されない\n• 実装後に仕様食い違いが発覚\n• リファクタ/再テストの工数発生", {
    x: 7.0, y: 4.0, w: 5.6, h: 1.5,
    fontFace: F.bodyJa, fontSize: 13, color: C.textBlack, valign: "top",
  });

  // 作成順序
  s.addShape("roundRect", {
    x: 0.5, y: 6.0, w: 12.4, h: 0.85,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 }, rectRadius: 0.08,
  });
  s.addText("作成順序: UI 作成 → 顧客 OK → SS 作成 → SS 承認 → PG → PT (SSの項目を1:1テスト)", {
    x: 0.5, y: 6.0, w: 12.4, h: 0.85,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textWhite, align: "center", valign: "middle",
  });
  addPageNo(s, 3, TOTAL);
}

// =============================================================
// Slide 4: システム構成 (シンプル)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "媒体は Web アプリ。ブラウザのみで全機能利用可能");

  circleIcon(s, 1.2, 2.6, 1.0, C.royalBlue, "👤", 32, C.textWhite);
  s.addText("PM / SE\n(レビュア)", {
    x: 0.6, y: 3.7, w: 2.2, h: 0.7,
    fontFace: F.bodyJa, fontSize: 14, bold: true, color: C.textBlack, align: "center",
  });

  s.addShape("rightArrow", {
    x: 2.3, y: 2.85, w: 1.2, h: 0.5,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 },
  });
  s.addText("HTTPS", {
    x: 2.3, y: 2.85, w: 1.2, h: 0.5,
    fontFace: F.num, fontSize: 12, bold: true, color: C.textWhite, align: "center", valign: "middle",
  });

  s.addShape("roundRect", {
    x: 3.6, y: 2.0, w: 3.2, h: 2.2,
    fill: { color: C.bgPale }, line: { color: C.blue3, width: 2 }, rectRadius: 0.15,
  });
  s.addText("Web ブラウザ", {
    x: 3.6, y: 2.15, w: 3.2, h: 0.5,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.royalBlue, align: "center",
  });
  s.addText("Chrome / Edge", { x: 3.6, y: 2.7, w: 3.2, h: 0.4, fontFace: F.bodyJa, fontSize: 12, color: C.textMuted, align: "center" });
  circleIcon(s, 4.85, 3.2, 0.7, C.blue3, "🌐", 22);

  s.addShape("rightArrow", {
    x: 6.85, y: 2.85, w: 1.2, h: 0.5,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 },
  });
  s.addText("REST API", {
    x: 6.85, y: 2.85, w: 1.2, h: 0.5,
    fontFace: F.num, fontSize: 11, bold: true, color: C.textWhite, align: "center", valign: "middle",
  });

  s.addShape("roundRect", {
    x: 8.0, y: 1.5, w: 4.5, h: 3.4,
    fill: { color: C.bgLight }, line: { color: C.royalBlue, width: 2 }, rectRadius: 0.15,
  });
  s.addText("AWS (Windows Server EC2)", {
    x: 8.0, y: 1.65, w: 4.5, h: 0.5,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.royalBlue, align: "center",
  });

  badge(s, 8.3, 2.3, 1.8, 0.5, "フロント", C.blue3, C.textWhite, 13);
  badge(s, 10.4, 2.3, 1.8, 0.5, "API", C.blue2, C.textWhite, 13);
  badge(s, 8.3, 2.95, 1.8, 0.5, "DB", C.royalBlue, C.textWhite, 13);
  badge(s, 10.4, 2.95, 1.8, 0.5, "ファイル", C.royalBlue, C.textWhite, 13);
  s.addText("Next.js + FastAPI + PostgreSQL", {
    x: 8.0, y: 3.7, w: 4.5, h: 0.4,
    fontFace: F.mono, fontSize: 11, color: C.textBlack, align: "center",
  });
  s.addText("Excel COM / LibreOffice + PyMuPDF (注釈)", {
    x: 8.0, y: 4.15, w: 4.5, h: 0.4,
    fontFace: F.mono, fontSize: 11, color: C.textMuted, align: "center",
  });

  s.addShape("downArrow", {
    x: 9.95, y: 4.95, w: 0.6, h: 0.6,
    fill: { color: C.amber }, line: { color: C.amber, width: 0 },
  });
  s.addShape("roundRect", {
    x: 8.0, y: 5.6, w: 4.5, h: 1.2,
    fill: { color: C.bgPale }, line: { color: C.amber, width: 2 }, rectRadius: 0.15,
  });
  circleIcon(s, 8.3, 5.85, 0.7, C.amber, "AI", 14);
  s.addText("Claude API\n(レビュー指摘生成)", {
    x: 9.2, y: 5.7, w: 3.2, h: 1.0,
    fontFace: F.bodyJa, fontSize: 13, bold: true, color: C.textBlack, valign: "middle",
  });

  s.addText("Windows Server で Excel COM。Linux EC2 では LibreOffice fallback で運用可。", {
    x: 0.5, y: 6.65, w: 12.4, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 4, TOTAL);
}

// =============================================================
// Slide 5: 利用フロー (5ステップ)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "利用フロー: D&D で 3 ファイル投入 → AI レビュー → PDF DL");

  const steps = [
    { icon: "①", title: "ログイン", desc: "メール+PW で\nJWT 認証" },
    { icon: "②", title: "工程選択", desc: "UI / SS /\nUI×SS 整合性" },
    { icon: "③", title: "3 ファイル D&D", desc: "観点 + UI + SS\nを同時投入" },
    { icon: "④", title: "AI レビュー", desc: "Claude が指摘+\n修正案を生成" },
    { icon: "⑤", title: "PDF DL", desc: "原本 PDF + 注釈\nオーバーレイ付き" },
  ];

  const stepW = 2.1;
  const gap = 0.4;
  const totalW = stepW * 5 + gap * 4;
  const startX = (13.33 - totalW) / 2;

  steps.forEach((st, i) => {
    const x = startX + i * (stepW + gap);
    s.addShape("roundRect", {
      x, y: 1.5, w: stepW, h: 4.6,
      fill: { color: i % 2 === 0 ? C.bgPale : C.bgLight },
      line: { color: C.royalBlue, width: 1.5 },
      rectRadius: 0.15,
    });
    circleIcon(s, x + (stepW - 0.9) / 2, 1.8, 0.9, C.royalBlue, st.icon, 28);
    s.addText(st.title, {
      x, y: 2.9, w: stepW, h: 0.6,
      fontFace: F.headJa, fontSize: 18, bold: true, color: C.royalBlue, align: "center",
    });
    s.addShape("line", {
      x: x + 0.4, y: 3.55, w: stepW - 0.8, h: 0,
      line: { color: C.royalBlue, width: 0.5 },
    });
    s.addText(st.desc, {
      x: x + 0.15, y: 3.7, w: stepW - 0.3, h: 2.3,
      fontFace: F.bodyJa, fontSize: 14, color: C.textBlack, align: "center", valign: "top",
    });

    if (i < steps.length - 1) {
      s.addShape("rightArrow", {
        x: x + stepW + 0.05, y: 3.5, w: gap - 0.1, h: 0.7,
        fill: { color: C.amber }, line: { color: C.amber, width: 0 },
      });
    }
  });

  s.addText("特徴: ファイルを 3 つ画面にドラッグするだけ。観点ファイルは PM が用意 (Excel/TXT)。", {
    x: 0.5, y: 6.5, w: 12.4, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 5, TOTAL);
}

// =============================================================
// Slide 6: 投入時画面 (D&D)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "投入画面: 3 ファイル (観点 / UI / SS) を D&D で同時投入");

  // ブラウザ枠
  s.addShape("roundRect", { x: 0.5, y: 1.3, w: 12.4, h: 5.5, fill: { color: C.bgWhite }, line: { color: C.gridLine, width: 1 }, rectRadius: 0.1 });
  s.addShape("rect", { x: 0.5, y: 1.3, w: 12.4, h: 0.4, fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 } });
  s.addText("⬤ ⬤ ⬤   AIレビュー支援ツール   /   レビュー実行", {
    x: 0.7, y: 1.3, w: 12.0, h: 0.4,
    fontFace: F.bodyJa, fontSize: 11, color: C.textWhite, valign: "middle",
  });

  // 工程選択 ラジオ
  s.addText("① 工程選択", { x: 0.8, y: 1.85, w: 4.0, h: 0.4, fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack });
  ["⦿ UI レビュー", "○ SS レビュー", "○ UI × SS 整合性"].forEach((t, i) => {
    s.addText(t, { x: 0.9 + i * 3.5, y: 2.25, w: 3.4, h: 0.4, fontFace: F.bodyJa, fontSize: 13, color: C.textBlack });
  });

  // ② 観点ファイル D&D
  s.addText("② 観点ファイル (PM 提供)", { x: 0.8, y: 2.85, w: 5.0, h: 0.4, fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack });
  s.addShape("roundRect", {
    x: 0.8, y: 3.25, w: 11.8, h: 0.9,
    fill: { color: "FFF8E1" }, line: { color: C.amber, width: 2, dashType: "dash" }, rectRadius: 0.1,
  });
  s.addText("📁  観点ファイル (.xlsx / .txt) をここにドラッグ&ドロップ", {
    x: 0.8, y: 3.25, w: 11.8, h: 0.9,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.amber, align: "center", valign: "middle",
  });

  // ③ UI / SS D&D 並列
  s.addText("③ レビュー対象資料", { x: 0.8, y: 4.3, w: 5.0, h: 0.4, fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack });

  s.addShape("roundRect", {
    x: 0.8, y: 4.7, w: 5.8, h: 1.3,
    fill: { color: C.bgPale }, line: { color: C.amber, width: 2, dashType: "dash" }, rectRadius: 0.1,
  });
  badge(s, 0.95, 4.85, 1.0, 0.5, "UI", C.amber, C.textWhite, 16);
  s.addText("📁 機能概要書", {
    x: 2.0, y: 4.85, w: 4.5, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack, valign: "middle",
  });
  s.addText("(.xlsx / .docx) D&D", {
    x: 2.0, y: 5.3, w: 4.5, h: 0.4,
    fontFace: F.bodyJa, fontSize: 12, color: C.textMuted, valign: "middle",
  });
  s.addText("顧客向け、図表/装飾あり", {
    x: 2.0, y: 5.65, w: 4.5, h: 0.3,
    fontFace: F.bodyJa, fontSize: 10, italic: true, color: C.textMuted, valign: "middle",
  });

  s.addShape("roundRect", {
    x: 6.8, y: 4.7, w: 5.8, h: 1.3,
    fill: { color: C.bgPale }, line: { color: C.royalBlue, width: 2, dashType: "dash" }, rectRadius: 0.1,
  });
  badge(s, 6.95, 4.85, 1.0, 0.5, "SS", C.royalBlue, C.textWhite, 16);
  s.addText("📁 構造設計書", {
    x: 8.0, y: 4.85, w: 4.5, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack, valign: "middle",
  });
  s.addText("(.xlsx) D&D", {
    x: 8.0, y: 5.3, w: 4.5, h: 0.4,
    fontFace: F.bodyJa, fontSize: 12, color: C.textMuted, valign: "middle",
  });
  s.addText("PG向け、擬似コード+PT項目", {
    x: 8.0, y: 5.65, w: 4.5, h: 0.3,
    fontFace: F.bodyJa, fontSize: 10, italic: true, color: C.textMuted, valign: "middle",
  });

  // 実行ボタン
  s.addShape("roundRect", {
    x: 5.0, y: 6.15, w: 3.4, h: 0.55,
    fill: { color: C.green }, line: { color: C.green, width: 0 }, rectRadius: 0.08,
  });
  s.addText("▶  AI レビュー実行", {
    x: 5.0, y: 6.15, w: 3.4, h: 0.55,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.textWhite, align: "center", valign: "middle",
  });

  s.addText("画面1枚で完結。観点と対象を 3 ファイル同時 D&D する設計。", {
    x: 0.5, y: 6.95, w: 12.4, h: 0.3,
    fontFace: F.bodyJa, fontSize: 11, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 6, TOTAL);
}

// =============================================================
// Slide 7: レビュー結果 (PDF オーバーレイ)
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "レビュー結果 = PDF。原本 + 注釈オーバーレイ + サマリページ");

  // PDF プレビュー枠
  s.addShape("roundRect", { x: 0.5, y: 1.3, w: 8.0, h: 5.5, fill: { color: C.bgWhite }, line: { color: C.gridLine, width: 2 }, rectRadius: 0.1 });
  s.addShape("rect", { x: 0.5, y: 1.3, w: 8.0, h: 0.4, fill: { color: "B71C1C" }, line: { color: "B71C1C", width: 0 } });
  s.addText("📕  ABC社_機能概要書_v1.2_AIレビュー結果.pdf", {
    x: 0.6, y: 1.3, w: 7.9, h: 0.4,
    fontFace: F.bodyJa, fontSize: 12, bold: true, color: C.textWhite, valign: "middle",
  });

  // PDF コンテンツ (Excel ベース)
  s.addText("Sheet1: 機能一覧", { x: 0.7, y: 1.85, w: 4.0, h: 0.4, fontFace: F.headJa, fontSize: 13, bold: true, color: C.textBlack });

  // 模擬テーブル
  const cols = ["ID", "機能名", "概要", "備考"];
  const cw = [0.7, 1.6, 2.3, 1.6];
  let cx = 0.7;
  cols.forEach((c, i) => {
    s.addShape("rect", { x: cx, y: 2.3, w: cw[i], h: 0.35, fill: { color: C.bgLight }, line: { color: C.gridLine, width: 0.3 } });
    s.addText(c, { x: cx + 0.05, y: 2.3, w: cw[i] - 0.1, h: 0.35, fontFace: F.bodyJa, fontSize: 10, bold: true, color: C.textBlack, valign: "middle" });
    cx += cw[i];
  });
  const rows = [
    ["F-001", "受注登録", "顧客から受注", ""],
    ["F-003", "受注承認", "10万円超で承認", ""],
    ["F-004", "金額計算", "数量×単価", ""],
    ["F-006", "削除",     "適切に処理する", "★曖昧"],
    ["F-007", "メール通知", "登録時に通知", ""],
  ];
  rows.forEach((row, r) => {
    let x = 0.7;
    row.forEach((cell, i) => {
      s.addShape("rect", { x, y: 2.65 + r * 0.35, w: cw[i], h: 0.35, fill: { color: r % 2 === 0 ? C.bgWhite : C.bgLight }, line: { color: C.gridLine, width: 0.3 } });
      s.addText(cell, { x: x + 0.05, y: 2.65 + r * 0.35, w: cw[i] - 0.1, h: 0.35, fontFace: F.bodyJa, fontSize: 9.5, color: C.textBlack, valign: "middle" });
      x += cw[i];
    });
  });

  // 番号バッジ (セル右上に重ねる)
  circleIcon(s, 6.45, 3.65, 0.32, C.red, "①", 11);    // F-006 削除 にバッジ
  circleIcon(s, 6.45, 4.0, 0.32, C.amber, "②", 11);    // F-007 メール通知 にバッジ
  circleIcon(s, 4.50, 3.30, 0.32, C.amber, "③", 11);   // F-004 金額計算

  s.addText("Page 1 / 5", { x: 0.7, y: 6.5, w: 7.5, h: 0.3, fontFace: F.num, fontSize: 10, color: C.textMuted, align: "right" });

  // 右側: 指摘ボックス (3つ、重ならない配置)
  s.addText("AI 指摘", {
    x: 8.6, y: 1.85, w: 4.3, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.royalBlue,
  });

  // 指摘①
  s.addShape("roundRect", {
    x: 8.6, y: 2.3, w: 4.3, h: 1.4,
    fill: { color: "FFEBEE" }, line: { color: C.red, width: 1.5 }, rectRadius: 0.08,
  });
  badge(s, 8.7, 2.4, 0.6, 0.35, "①高", C.red, C.textWhite, 10);
  s.addText("曖昧表現", { x: 9.4, y: 2.4, w: 3.4, h: 0.35, fontFace: F.headJa, fontSize: 11, bold: true, color: C.red, valign: "middle" });
  s.addText("位置: F-006 削除", { x: 8.75, y: 2.8, w: 4.0, h: 0.3, fontFace: F.bodyJa, fontSize: 10, color: C.textBlack });
  s.addText("「適切に処理」が曖昧。\n削除条件・確認ダイアログを明記推奨", {
    x: 8.75, y: 3.1, w: 4.0, h: 0.55,
    fontFace: F.bodyJa, fontSize: 10, color: C.textBlack, valign: "top",
  });

  // 指摘②
  s.addShape("roundRect", {
    x: 8.6, y: 3.85, w: 4.3, h: 1.4,
    fill: { color: "FFF3E0" }, line: { color: C.amber, width: 1.5 }, rectRadius: 0.08,
  });
  badge(s, 8.7, 3.95, 0.6, 0.35, "②中", C.amber, C.textWhite, 10);
  s.addText("UI×SS 整合", { x: 9.4, y: 3.95, w: 3.4, h: 0.35, fontFace: F.headJa, fontSize: 11, bold: true, color: C.amber, valign: "middle" });
  s.addText("位置: F-007 メール通知", { x: 8.75, y: 4.35, w: 4.0, h: 0.3, fontFace: F.bodyJa, fontSize: 10, color: C.textBlack });
  s.addText("UI に F-007 あるが、SS の\nモジュール一覧に対応無し", {
    x: 8.75, y: 4.65, w: 4.0, h: 0.55,
    fontFace: F.bodyJa, fontSize: 10, color: C.textBlack, valign: "top",
  });

  // 指摘③
  s.addShape("roundRect", {
    x: 8.6, y: 5.4, w: 4.3, h: 1.4,
    fill: { color: "FFF3E0" }, line: { color: C.amber, width: 1.5 }, rectRadius: 0.08,
  });
  badge(s, 8.7, 5.5, 0.6, 0.35, "③中", C.amber, C.textWhite, 10);
  s.addText("UI×SS 不整合", { x: 9.4, y: 5.5, w: 3.4, h: 0.35, fontFace: F.headJa, fontSize: 11, bold: true, color: C.amber, valign: "middle" });
  s.addText("位置: F-004 金額計算", { x: 8.75, y: 5.9, w: 4.0, h: 0.3, fontFace: F.bodyJa, fontSize: 10, color: C.textBlack });
  s.addText("UI=税込表示、SS=税抜計算\nで矛盾。顧客クレーム発生リスク", {
    x: 8.75, y: 6.2, w: 4.0, h: 0.55,
    fontFace: F.bodyJa, fontSize: 10, color: C.textBlack, valign: "top",
  });

  // 引出線 (バッジ → 指摘ボックス)
  s.addShape("line", { x: 6.77, y: 3.81, w: 1.83, h: 0, line: { color: C.red, width: 1, dashType: "dash" } });
  s.addShape("line", { x: 6.77, y: 4.16, w: 1.83, h: 0.4, line: { color: C.amber, width: 1, dashType: "dash" } });
  s.addShape("line", { x: 4.82, y: 3.46, w: 3.78, h: 2.5, line: { color: C.amber, width: 1, dashType: "dash" } });

  s.addText("注釈は右マージンに縦積み配置 → 重ならない / 引出線でセル位置と接続", {
    x: 0.5, y: 6.95, w: 12.4, h: 0.3,
    fontFace: F.bodyJa, fontSize: 11, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 7, TOTAL);
}

// =============================================================
// Slide 8: PDF 構造 + ダウンロード
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "PDF 構造: 原本各ページ + サマリページ + PT項目候補");

  // 3 段重ね PDF
  const layers = [
    { y: 1.5, title: "原本ページ ×N (Excel→PDF変換)", desc: "Excel の図表・装飾を保持。各ページに番号バッジ + 注釈ボックスをオーバーレイ", color: C.blue3 },
    { y: 3.5, title: "サマリページ (全指摘一覧)", desc: "指摘番号 / 重要度 / 観点 / 位置 / 内容 / 修正案 を表形式で1ページに集約", color: C.royalBlue },
    { y: 5.5, title: "PT項目候補ページ (SS レビュー時のみ)", desc: "AI が SS から自動抽出した PT 項目候補一覧 (PT-ID / 観点 / 期待結果)", color: C.amber },
  ];

  layers.forEach((l, i) => {
    s.addShape("roundRect", {
      x: 0.5, y: l.y, w: 8.0, h: 1.7,
      fill: { color: i === 0 ? "E3F2FD" : i === 1 ? "EAF1FA" : "FFF8E1" },
      line: { color: l.color, width: 1.5 },
      rectRadius: 0.1,
    });
    badge(s, 0.7, l.y + 0.2, 0.6, 0.5, `${i + 1}`, l.color, C.textWhite, 22);
    s.addText(l.title, {
      x: 1.5, y: l.y + 0.2, w: 6.8, h: 0.5,
      fontFace: F.headJa, fontSize: 16, bold: true, color: l.color, valign: "middle",
    });
    s.addText(l.desc, {
      x: 1.5, y: l.y + 0.8, w: 6.8, h: 0.85,
      fontFace: F.bodyJa, fontSize: 12, color: C.textBlack, valign: "top",
    });
  });

  // 右側: ダウンロードボタン
  s.addShape("roundRect", {
    x: 9.0, y: 2.5, w: 3.9, h: 3.2,
    fill: { color: C.bgLight }, line: { color: C.green, width: 2 },
    rectRadius: 0.15,
  });
  circleIcon(s, 9.6, 2.8, 1.0, C.green, "⬇", 38);
  s.addText("PDF\nダウンロード", {
    x: 10.7, y: 2.8, w: 2.0, h: 1.0,
    fontFace: F.headJa, fontSize: 16, bold: true, color: C.green, valign: "middle",
  });
  s.addText("レビュー結果画面に\n[⬇ PDF DL] ボタン配置", {
    x: 9.2, y: 4.1, w: 3.6, h: 0.7,
    fontFace: F.bodyJa, fontSize: 12, color: C.textBlack, valign: "top",
  });
  s.addShape("rect", { x: 9.2, y: 4.85, w: 3.6, h: 0, line: { color: C.green, width: 0.5 } });
  s.addText("ファイル名:\nABC_機能概要書_v1.2\n_AIレビュー_20260428.pdf", {
    x: 9.2, y: 4.95, w: 3.6, h: 0.7,
    fontFace: F.mono, fontSize: 10, color: C.textMuted, valign: "top",
  });

  s.addText("Excel COM (PDF変換) + PyMuPDF (注釈オーバーレイ) で生成。重ならない自動配置。", {
    x: 0.5, y: 6.95, w: 12.4, h: 0.3,
    fontFace: F.bodyJa, fontSize: 11, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 8, TOTAL);
}

// =============================================================
// Slide 9: 工程別の機能切替
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "工程別 機能切替: UI / SS / UI×SS で必要資料・観点が変わる");

  const headers = ["工程", "UI 投入", "SS 投入", "観点", "AI が見る点", "出力"];
  const rows = [
    ["UI レビュー", "✓必須", "−", "UI 観点", "顧客視点・曖昧表現・項目欠落・用語統一", "PDF (UI注釈)"],
    ["SS レビュー", "−", "✓必須", "SS 観点", "条件網羅・データ型・PT項目1:1・エラー処理", "PDF (SS注釈+PT候補)"],
    ["UI×SS 整合性", "✓必須", "✓必須", "整合性 観点", "UI機能のSS反映漏れ・SSにあるUI外処理・税込/税抜矛盾", "PDF (UI+SS注釈)"],
  ];

  const colW = [2.0, 1.5, 1.5, 1.5, 4.4, 1.5];
  const startX = 0.5;
  const startY = 1.4;

  // ヘッダ
  let xc = startX;
  headers.forEach((h, i) => {
    s.addShape("rect", { x: xc, y: startY, w: colW[i], h: 0.6, fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0.5 } });
    s.addText(h, {
      x: xc + 0.1, y: startY, w: colW[i] - 0.2, h: 0.6,
      fontFace: F.headJa, fontSize: 13, bold: true, color: C.textWhite, valign: "middle",
    });
    xc += colW[i];
  });

  // データ
  rows.forEach((row, r) => {
    let x = startX;
    row.forEach((cell, i) => {
      s.addShape("rect", {
        x, y: startY + (r + 1) * 1.3, w: colW[i], h: 1.3,
        fill: { color: r % 2 === 0 ? C.bgWhite : C.bgLight },
        line: { color: C.gridLine, width: 0.5 },
      });
      const isCheck = cell === "✓必須";
      const color = isCheck ? C.green : (cell === "−" ? C.textMuted : C.textBlack);
      s.addText(cell, {
        x: x + 0.1, y: startY + (r + 1) * 1.3, w: colW[i] - 0.2, h: 1.3,
        fontFace: i === 0 ? F.headJa : F.bodyJa,
        fontSize: i === 0 ? 14 : 12,
        bold: i === 0 || isCheck,
        color,
        valign: "middle",
      });
      x += colW[i];
    });
  });

  s.addText("ユーザは工程選択するだけ。必要資料/観点/出力形式が自動切替される。", {
    x: 0.5, y: 6.65, w: 12.4, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 9, TOTAL);
}

// =============================================================
// Slide 10: AI コスト
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "AI コスト: 開発は ¥0、本番運用は月 $50〜200 (要予算管理)");

  s.addShape("roundRect", {
    x: 0.5, y: 1.4, w: 6.1, h: 5.0,
    fill: { color: "E8F5E9" }, line: { color: C.green, width: 2 },
    rectRadius: 0.15,
  });
  circleIcon(s, 0.7, 1.6, 1.0, C.green, "¥0", 22);
  s.addText("開発フェーズ", {
    x: 1.85, y: 1.6, w: 4.6, h: 0.5,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.green,
  });
  s.addText("追加課金なし", {
    x: 1.85, y: 2.1, w: 4.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, color: C.textMuted,
  });

  s.addText("内訳:", {
    x: 0.7, y: 2.9, w: 5.7, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack,
  });
  ["Stub LLM で全機能動作", "CI も Stub で完結 (94 tests)", "Anthropic キー不要で開発可"].forEach((t, i) => {
    circleIcon(s, 0.8, 3.4 + i * 0.7, 0.35, C.green, "✓", 13);
    s.addText(t, {
      x: 1.3, y: 3.4 + i * 0.7, w: 5.0, h: 0.4,
      fontFace: F.bodyJa, fontSize: 14, color: C.textBlack, valign: "middle",
    });
  });
  s.addText("→ ローカル開発・CI ともに ¥0 で完結", {
    x: 0.7, y: 5.6, w: 5.7, h: 0.4,
    fontFace: F.bodyJa, fontSize: 13, italic: true, color: C.green,
  });

  s.addShape("roundRect", {
    x: 6.8, y: 1.4, w: 6.1, h: 5.0,
    fill: { color: "FFF3E0" }, line: { color: C.amber, width: 2 },
    rectRadius: 0.15,
  });
  circleIcon(s, 7.0, 1.6, 1.0, C.amber, "$", 28);
  s.addText("本番運用フェーズ", {
    x: 8.15, y: 1.6, w: 4.6, h: 0.5,
    fontFace: F.headJa, fontSize: 22, bold: true, color: C.amber,
  });
  s.addText("従量課金 (月額)", {
    x: 8.15, y: 2.1, w: 4.6, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, color: C.textMuted,
  });

  s.addText("試算:", {
    x: 7.0, y: 2.9, w: 5.7, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textBlack,
  });
  s.addText("1 レビュー = 観点 10 × 1 ページ ≒ 5〜10 円", {
    x: 7.0, y: 3.4, w: 5.7, h: 0.4,
    fontFace: F.bodyJa, fontSize: 13, color: C.textBlack,
  });
  s.addText("100案件 × 5レビュー/日 ≒ 月 $50〜200", {
    x: 7.0, y: 3.8, w: 5.7, h: 0.6,
    fontFace: F.headJa, fontSize: 18, bold: true, color: C.amber,
  });

  s.addText("対策:", {
    x: 7.0, y: 4.6, w: 5.7, h: 0.4,
    fontFace: F.headJa, fontSize: 13, bold: true, color: C.textBlack,
  });
  s.addText("• 観点ファイル粒度で線形に制御\n• Anthropic ダッシュボードで月上限設定\n• tenacity リトライで失敗課金を最小化", {
    x: 7.0, y: 5.0, w: 5.7, h: 1.2,
    fontFace: F.bodyJa, fontSize: 12, color: C.textBlack, valign: "top",
  });

  s.addText("ポイント: 開発に追加コストは一切なし。本番投入時は月額予算の合意が必要。", {
    x: 0.5, y: 6.65, w: 12.4, h: 0.4,
    fontFace: F.bodyJa, fontSize: 14, italic: true, color: C.textMuted, align: "center",
  });
  addPageNo(s, 10, TOTAL);
}

// =============================================================
// Slide 11: 進捗 + 次のアクション
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "進捗: Phase 1〜4 完了。Phase 5 以降は OSS 公開後の拡張ロードマップ");

  // 進捗バー
  s.addText("Phase 完了: 4 / 8  (50%) ＋ F-01〜F-09 全機能 ✅", {
    x: 0.5, y: 1.4, w: 12.4, h: 0.5,
    fontFace: F.headJa, fontSize: 18, bold: true, color: C.royalBlue,
  });
  s.addShape("rect", { x: 0.5, y: 2.0, w: 12.4, h: 0.4, fill: { color: C.bgLight }, line: { color: C.gridLine, width: 0.5 } });
  s.addShape("rect", { x: 0.5, y: 2.0, w: (12.4 * 50) / 100, h: 0.4, fill: { color: C.green }, line: { color: C.green, width: 0 } });

  const phases = [
    { num: 1, name: "認証・基盤", state: "done" },
    { num: 2, name: "AI レビュー実行", state: "done" },
    { num: 3, name: "観点ファイル/Anthropic", state: "done" },
    { num: 4, name: "PDF出力+横断+対応管理", state: "done" },
    { num: 5, name: "ナレッジ管理", state: "todo" },
    { num: 6, name: "レポート出力強化", state: "todo" },
    { num: 7, name: "マルチテナント", state: "todo" },
    { num: 8, name: "AWS 本番デプロイ", state: "todo" },
  ];

  const cardW = 3.0, cardH = 1.0, gap = 0.15;
  phases.forEach((p, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.5 + col * (cardW + gap);
    const y = 2.85 + row * (cardH + 0.2);

    const colorMap = { done: C.green, next: C.amber, todo: C.textMuted };
    s.addShape("roundRect", {
      x, y, w: cardW, h: cardH,
      fill: { color: p.state === "done" ? "E8F5E9" : p.state === "next" ? "FFF3E0" : C.bgLight },
      line: { color: colorMap[p.state], width: 1.5 },
      rectRadius: 0.1,
    });
    badge(s, x + 0.15, y + 0.2, 0.6, 0.4, `P${p.num}`, colorMap[p.state], C.textWhite, 12);
    s.addText(p.name, {
      x: x + 0.85, y: y + 0.1, w: cardW - 0.95, h: 0.55,
      fontFace: F.headJa, fontSize: 13, bold: true, color: C.textBlack, valign: "middle",
    });
    s.addText(p.state === "done" ? "✓ 完了" : p.state === "next" ? "▶ 着手予定" : "□ 未着手", {
      x: x + 0.85, y: y + 0.55, w: cardW - 0.95, h: 0.4,
      fontFace: F.bodyJa, fontSize: 11, color: colorMap[p.state],
    });
  });

  // Next Action box
  s.addShape("roundRect", {
    x: 0.5, y: 5.6, w: 12.4, h: 1.3,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 },
    rectRadius: 0.1,
  });
  s.addText("Next Action", {
    x: 0.7, y: 5.7, w: 12.0, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.amber,
  });
  s.addText("Phase 5: ナレッジ蓄積 (Findings → 学習データ化) で精度向上ループ確立", {
    x: 0.7, y: 6.1, w: 12.0, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textWhite,
  });
  s.addText("samples/ に検証用モック Excel 5 ファイル同梱 → リポジトリ clone 直後に動作確認可能", {
    x: 0.7, y: 6.45, w: 12.0, h: 0.4,
    fontFace: F.bodyJa, fontSize: 12, color: C.textWhite,
  });
  addPageNo(s, 11, TOTAL);
}

// =============================================================
// Slide 12: まとめ
// =============================================================
{
  const s = pptx.addSlide();
  addActionTitle(s, "まとめ: D&D で投入 → AI レビュー → PDF DL の3ステップ完結 (公開済)");

  const items = [
    { icon: "✅", text: "Phase 1〜4 完了 (BE 75 tests + FE 19 tests = 94 tests passed)" },
    { icon: "✅", text: "F-01〜F-09 全機能リリース (UI / SS / 横断 / PDF / 対応管理 / 認証 ほか)" },
    { icon: "✅", text: "D&D 1画面で観点+UI+SS 同時投入、操作シンプル" },
    { icon: "✅", text: "PDF 出力 (原本+注釈+サマリ+PT候補) — 元 Excel を壊さない" },
    { icon: "✅", text: "LLM 抽象化 (Stub / Anthropic 切替) → 開発・CI コスト ¥0" },
    { icon: "✅", text: "GitHub 公開 (MIT) — README / docs / CI / Issue Templates 整備済" },
    { icon: "🔜", text: "Phase 5以降: ナレッジ蓄積 / レポート強化 / マルチテナント / AWS デプロイ" },
  ];
  items.forEach((it, i) => {
    s.addText(it.icon, {
      x: 0.5, y: 1.4 + i * 0.55, w: 0.6, h: 0.5,
      fontFace: F.bodyJa, fontSize: 16, valign: "middle",
    });
    s.addText(it.text, {
      x: 1.2, y: 1.4 + i * 0.55, w: 11.7, h: 0.5,
      fontFace: F.bodyJa, fontSize: 13, color: C.textBlack, valign: "middle",
    });
  });

  s.addShape("roundRect", {
    x: 0.5, y: 5.6, w: 12.4, h: 1.3,
    fill: { color: C.royalBlue }, line: { color: C.royalBlue, width: 0 },
    rectRadius: 0.1,
  });
  s.addText("リポジトリの読み方", {
    x: 0.7, y: 5.7, w: 12.0, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.amber,
  });
  s.addText("① README.md → 全体像 / クイックスタート  ② docs/portfolio.md → 技術判断・設計トレードオフ", {
    x: 0.7, y: 6.1, w: 12.0, h: 0.4,
    fontFace: F.headJa, fontSize: 14, bold: true, color: C.textWhite,
  });
  s.addText("③ samples/ で動作確認  ④ docs/architecture.md / setup.md / demo.md で深掘り", {
    x: 0.7, y: 6.45, w: 12.0, h: 0.4,
    fontFace: F.bodyJa, fontSize: 12, color: C.textWhite,
  });
  addPageNo(s, 12, TOTAL);
}

// ====== 保存 ======
const path = require("path");
const fs = require("fs");
const outDir = path.resolve(__dirname, "dist");
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, "Waterfall_Review_App_Overview.pptx");
pptx.writeFile({ fileName: outPath }).then((file) => {
  console.log(`✓ Generated: ${file}`);
}).catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
