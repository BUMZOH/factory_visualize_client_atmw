# ボタン配色設計方針（Bootstrapの思想を採用）

## 目的

ボタンの色を「見た目」ではなく**役割（意味）**で管理する。

例えば、

❌ 悪い例

``` html
<button class="green-button">保存</button>
```

後から青色に変更した場合でも `green-button` のままとなり、
コードの意味が分かりにくくなる。

------------------------------------------------------------------------

## 良い例

``` html
<button class="button button-success">保存</button>
```

`success` は「保存・正常終了・出力」などの**意味**を表す。

色を変更してもHTMLは変更不要。

------------------------------------------------------------------------

# Bootstrapと同じ思想

Bootstrapでも以下のような命名になっている。

  クラス          意味     標準色   用途
  --------------- -------- -------- --------------------------
  btn-primary     主操作   青       表示、登録、検索など
  btn-success     成功     緑       保存、出力、完了
  btn-danger      危険     赤       削除、初期化
  btn-warning     注意     黄       警告、確認
  btn-secondary   補助     灰       閉じる、戻る、キャンセル

このアプリでも同じ思想を採用する。

------------------------------------------------------------------------

# このアプリでの運用方針

  クラス             用途
  ------------------ ----------------------------
  button-primary     表示更新・検索など主操作
  button-success     画像出力・CSV出力・保存
  button-danger      削除・DB初期化など危険操作
  button-warning     注意が必要な操作
  button-secondary   閉じる・戻る・キャンセル

------------------------------------------------------------------------

# CSS設計

共通部分

``` css
.button{
    padding:10px 24px;
    border:none;
    border-radius:6px;
    color:white;
    font-size:16px;
    cursor:pointer;
}
```

色だけ分離する。

``` css
.button-primary{
    background:#1f6feb;
}

.button-success{
    background:#28a745;
}

.button-danger{
    background:#dc3545;
}

.button-warning{
    background:#ffc107;
    color:#222;
}

.button-secondary{
    background:#6c757d;
}
```

------------------------------------------------------------------------

# HTML記述例

``` html
<button class="button button-primary">表示更新</button>

<button class="button button-success">画像出力</button>

<button class="button button-danger">削除</button>

<button class="button button-secondary">閉じる</button>
```

------------------------------------------------------------------------

# この設計のメリット

-   色ではなく役割で管理できる
-   色変更時にHTMLを書き換える必要がない
-   共通デザインは `.button` を1か所修正するだけ
-   Bootstrapと同じ考え方なので理解しやすい
-   ボタンが増えても保守しやすい

------------------------------------------------------------------------

# 今後の設計方針

-   ボタン名は**色ではなく意味**で命名する。
-   共通デザインと色を分離する。
-   Bootstrapと同じ思想を採用し、保守性・可読性を優先する。
